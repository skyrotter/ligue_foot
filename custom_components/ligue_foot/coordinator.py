"""Coordinateur : récupère les données (1 appel matchs + 1 classement par ligue)."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import EspnApi, EspnApiError
from .const import (
    CONF_TEAMS,
    DAYS_AHEAD,
    DAYS_BEHIND,
    DOMAIN,
    UPDATE_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


class LigueFootCoordinator(DataUpdateCoordinator[dict]):
    """Données : {"matches": {ligue: [...]}, "standings": {ligue: [...]}}."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self.entry = entry
        self.api = EspnApi(async_get_clientsession(hass))
        self.teams: list[dict] = entry.data[CONF_TEAMS]
        # Ligues réellement utilisées (celles des équipes favorites)
        self.leagues = sorted({t["league"] for t in self.teams})

    async def _async_update_data(self) -> dict:
        today = dt_util.now().date()
        start = today - timedelta(days=DAYS_BEHIND)
        end = today + timedelta(days=DAYS_AHEAD)
        data: dict = {"matches": {}, "standings": {}}
        try:
            for league in self.leagues:
                data["matches"][league] = await self.api.matches(league, start, end)
                data["standings"][league] = await self.api.standings(league)
        except EspnApiError as err:
            raise UpdateFailed(f"Erreur ESPN : {err}") from err
        return data

    # --- Helpers utilisés par les capteurs et les rappels ---

    def _team_matches(self, league: str, team_id: str) -> list[dict]:
        return [
            m
            for m in (self.data or {}).get("matches", {}).get(league, [])
            if team_id in (m["home"]["id"], m["away"]["id"])
        ]

    def next_match(self, league: str, team_id: str) -> dict | None:
        """Prochain match (à venir ou en cours) d'une équipe."""
        for m in self._team_matches(league, team_id):
            if m["state"] in ("pre", "in"):
                return m
        return None

    def last_match(self, league: str, team_id: str) -> dict | None:
        """Dernier match terminé d'une équipe."""
        done = [m for m in self._team_matches(league, team_id) if m["state"] == "post"]
        return done[-1] if done else None

    def last_matches(self, league: str, team_id: str, count: int = 5) -> list[dict]:
        """5 derniers matchs terminés (du plus ancien au plus récent)."""
        done = [m for m in self._team_matches(league, team_id) if m["state"] == "post"]
        out = []
        for m in done[-count:]:
            at_home = m["home"]["id"] == team_id
            opp = m["away"] if at_home else m["home"]
            out.append(
                {
                    "result": result_for(m, team_id) or "?",
                    "opponent": opp["name"],
                    "opponent_logo": opp["logo"],
                    "home_team": m["home"]["name"],
                    "away_team": m["away"]["name"],
                    "home_score": m["home"]["score"],
                    "away_score": m["away"]["score"],
                    "at_home": at_home,
                    "date": m["kickoff"].isoformat(),
                }
            )
        return out

    def form(self, league: str, team_id: str, count: int = 5) -> list[str]:
        """Forme récente : liste de V / N / D (du plus ancien au plus récent)."""
        return [m["result"] for m in self.last_matches(league, team_id, count)]

    def matchday(self, league: str) -> tuple[list[dict], list[dict]]:
        """(derniers résultats, prochaine journée) d'une ligue.

        ESPN ne donne pas toujours le numéro de journée : on regroupe les matchs
        joués dans les 4 jours avant le dernier match terminé, et les matchs à
        venir dans les 4 jours après le prochain match.
        """
        matches = (self.data or {}).get("matches", {}).get(league, [])
        done = [m for m in matches if m["state"] == "post"]
        coming = [m for m in matches if m["state"] in ("pre", "in")]
        results, upcoming = [], []
        if done:
            ref = done[-1]["kickoff"]
            results = [m for m in done if ref - m["kickoff"] <= timedelta(days=4)]
        if coming:
            ref = coming[0]["kickoff"]
            upcoming = [m for m in coming if m["kickoff"] - ref <= timedelta(days=4)]
        return results, upcoming


def result_for(match: dict, team_id: str) -> str | None:
    """V / N / D du point de vue de l'équipe, None si score inconnu."""
    hs, as_ = match["home"]["score"], match["away"]["score"]
    if hs is None or as_ is None:
        return None
    mine, theirs = (hs, as_) if match["home"]["id"] == team_id else (as_, hs)
    if mine > theirs:
        return "V"
    if mine < theirs:
        return "D"
    return "N"
