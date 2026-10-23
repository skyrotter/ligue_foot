"""Coordinateur de données pour l'intégration Ligue Foot."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_LEAGUE,
    CONF_TEAM_ID,
    DOMAIN,
    ESPN_API_BASE,
    ESPN_API_BASE_V2,
    ESPN_SCOREBOARD,
    ESPN_STANDINGS,
    ESPN_TEAM_SCHEDULE,
    LEAGUES,
    SCAN_INTERVAL_DEFAULT,
    SCAN_INTERVAL_LIVE,
    SCAN_INTERVAL_MATCHDAY,
    SYNC_STATUS_FETCHING,
    SYNC_STATUS_PROVIDER_UNAVAILABLE,
    SYNC_STATUS_RATE_LIMITED,
    SYNC_STATUS_READY,
)

_LOGGER = logging.getLogger(__name__)


class LigueFootCoordinator(DataUpdateCoordinator[dict[str, Any]]):
        """Gère les mises à jour de données depuis l'API ESPN."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
                """Initialise le coordinateur."""
                self.entry = entry
                self.league_id: str = entry.data[CONF_LEAGUE]
                self.team_id: str = entry.data[CONF_TEAM_ID]
                self.espn_league: str = LEAGUES[self.league_id]["espn_id"]

        # État de synchronisation exposé comme capteur
                self.sync_status: str = SYNC_STATUS_FETCHING

        # Cache de secours : dernières données connues (TTL 7 jours)
                self._last_known: dict[str, Any] = {}
                self._last_known_at: datetime | None = None

        super().__init__(
                        hass,
                        _LOGGER,
                        name=f"{DOMAIN}_{entry.entry_id}",
                        update_interval=timedelta(seconds=SCAN_INTERVAL_DEFAULT),
        )

    async def _async_update_data(self) -> dict[str, Any]:
                """Récupère les données ESPN et adapte l'intervalle de polling."""
                self.sync_status = SYNC_STATUS_FETCHING
                session = async_get_clientsession(self.hass)

        try:
                        data = await asyncio.gather(
                                            self._fetch_scoreboard(session),
                                            self._fetch_standings(session),
                                            self._fetch_team_schedule(session),
                        )
except aiohttp.ClientResponseError as err:
                if err.status == 429:
                                    self.sync_status = SYNC_STATUS_RATE_LIMITED
                                    _LOGGER.warning("ESPN : quota dépassé (429), utilisation du cache")
                                    return self._cached_or_raise()
                                self.sync_status = SYNC_STATUS_PROVIDER_UNAVAILABLE
            _LOGGER.error("ESPN : erreur HTTP %s", err.status)
            return self._cached_or_raise()
except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            self.sync_status = SYNC_STATUS_PROVIDER_UNAVAILABLE
            _LOGGER.error("ESPN : erreur réseau %s", err)
            return self._cached_or_raise()

        scoreboard, standings, schedule = data
        result = {
                        "scoreboard": scoreboard,
                        "standings": standings,
                        "schedule": schedule,
                        "next_match": self._extract_next_match(schedule),
                        "live_match": self._extract_live_match(scoreboard),
                        "team_form": self._extract_team_form(schedule),
        }

        # Met à jour le cache
        self._last_known = result
        self._last_known_at = dt_util.utcnow()
        self.sync_status = SYNC_STATUS_READY

        # Adapte l'intervalle : plus fréquent si match en cours ou aujourd'hui
        self._adjust_poll_interval(result)

        return result

    def _cached_or_raise(self) -> dict[str, Any]:
                """Retourne le cache si récent (7 jours), sinon lève une exception."""
        if self._last_known_at and (
                        dt_util.utcnow() - self._last_known_at < timedelta(days=7)
        ):
                        _LOGGER.debug("Utilisation des dernières données connues (cache)")
                        return self._last_known
                    raise UpdateFailed("Aucune donnée disponible et cache expiré")

    def _adjust_poll_interval(self, data: dict[str, Any]) -> None:
                """Adapte l'intervalle de polling selon l'état du match."""
        if data.get("live_match"):
                        interval = SCAN_INTERVAL_LIVE
elif self._match_today(data):
            interval = SCAN_INTERVAL_MATCHDAY
else:
            interval = SCAN_INTERVAL_DEFAULT

        if self.update_interval != timedelta(seconds=interval):
                        self.update_interval = timedelta(seconds=interval)
                        _LOGGER.debug("Intervalle de polling → %s s", interval)

    def _match_today(self, data: dict[str, Any]) -> bool:
                """Vérifie si un match a lieu aujourd'hui."""
        next_match = data.get("next_match")
        if not next_match:
                        return False
                    match_date = next_match.get("date")
        if not match_date:
                        return False
                    today = dt_util.now().date()
        return match_date.date() == today

    # ──────────────────────────────────────────────────────────────────────────
    # Appels ESPN
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_scoreboard(self, session: aiohttp.ClientSession) -> dict:
                """Récupère les matchs en cours / du jour."""
        url = ESPN_SCOREBOARD.format(base=ESPN_API_BASE, league_id=self.espn_league)
        return await self._get(session, url)

    async def _fetch_standings(self, session: aiohttp.ClientSession) -> dict:
                """Récupère le classement de la ligue."""
        url = ESPN_STANDINGS.format(base=ESPN_API_BASE_V2, league_id=self.espn_league)
        return await self._get(session, url)

    async def _fetch_team_schedule(self, session: aiohttp.ClientSession) -> dict:
                """Récupère le calendrier de l'équipe."""
        url = ESPN_TEAM_SCHEDULE.format(
                        base=ESPN_API_BASE,
                        league_id=self.espn_league,
                        team_id=self.team_id,
        )
        return await self._get(session, url)

    async def _get(self, session: aiohttp.ClientSession, url: str) -> dict:
                """Effectue une requête GET et retourne le JSON."""
        _LOGGER.debug("ESPN GET %s", url)
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        resp.raise_for_status()
                        return await resp.json()

    # ──────────────────────────────────────────────────────────────────────────
    # Extraction des données
    # ──────────────────────────────────────────────────────────────────────────

    def _extract_next_match(self, schedule: dict) -> dict | None:
                """Retourne le prochain match de l'équipe (non terminé)."""
        try:
                        events = schedule.get("events", [])
                        now = dt_util.utcnow()
                        upcoming = []
                        for event in events:
                                            date_str = event.get("date")
                                            if not date_str:
                                                                    continue
                                                                match_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                                            status = event.get("status", {}).get("type", {}).get("state", "")
                                            if status != "post" and match_date >= now:
                                                                    upcoming.append({"date": match_date, "raw": event})
                                                            if not upcoming:
                                                                                return None
                                                                            upcoming.sort(key=lambda x: x["date"])
                                        return self._parse_event(upcoming[0]["raw"])
except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Erreur extraction prochain match : %s", err)
            return None

    def _extract_live_match(self, scoreboard: dict) -> dict | None:
                """Retourne le match en cours pour cette équipe, si existant."""
        try:
                        for event in scoreboard.get("events", []):
                                            state = event.get("status", {}).get("type", {}).get("state", "")
                                            if state != "in":
                                                                    continue
                                                                for comp in event.get("competitions", []):
                                                                                        for comp_team in comp.get("competitors", []):
                                                                                                                    if comp_team.get("team", {}).get("id") == self.team_id:
                                                                                                                                                    return self._parse_event(event)
                                                                                            except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Erreur extraction match live : %s", err)
        return None

    def _extract_team_form(self, schedule: dict) -> list[str]:
                """Retourne les 5 derniers résultats (W/D/L) de l'équipe."""
        try:
                        events = schedule.get("events", [])
            past = []
            for event in events:
                                state = event.get("status", {}).get("type", {}).get("state", "")
                if state == "post":
                                        past.append(event)
            # Trie par date décroissante, prend les 5 derniers
            past.sort(
                                key=lambda e: e.get("date", ""),
                                reverse=True,
            )
            form = []
            for event in past[:5]:
                                result = self._get_team_result(event)
                if result:
                                        form.append(result)
            return form
except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Erreur extraction forme : %s", err)
            return []

    def _get_team_result(self, event: dict) -> str | None:
                """Retourne W, D ou L pour cette équipe dans un match terminé."""
        try:
                        for comp in event.get("competitions", []):
                                            for comp_team in comp.get("competitors", []):
                                                                    if comp_team.get("team", {}).get("id") == self.team_id:
                                                                                                winner = comp_team.get("winner")
                                                                                                score_home = int(comp.get("competitors", [{}])[0].get("score", 0) or 0)
                                                                                                score_away = int(comp.get("competitors", [{}])[-1].get("score", 0) or 0)
                                                                                                if winner is True:
                                                                                                                                return "W"
                                                                                                                            if winner is False:
                                                                                                                                                            return "L"
                                                                                                                                                        return "D"
except Exception:  # noqa: BLE001
            pass
        return None

    def _parse_event(self, event: dict) -> dict:
                """Normalise un événement ESPN en dict utilisable par les capteurs."""
        try:
                        comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [{}, {}])
            home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
            away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[-1])
            date_str = event.get("date", "")
            match_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else None
            return {
                                "id": event.get("id"),
                                "date": match_date,
                                "home_team": home.get("team", {}).get("displayName", ""),
                                "home_team_logo": home.get("team", {}).get("logo", ""),
                                "home_score": home.get("score", ""),
                                "away_team": away.get("team", {}).get("displayName", ""),
                                "away_team_logo": away.get("team", {}).get("logo", ""),
                                "away_score": away.get("score", ""),
                                "status": event.get("status", {}).get("type", {}).get("description", ""),
                                "venue": comp.get("venue", {}).get("fullName", ""),
                                "matchday": event.get("week", {}).get("number", ""),
            }
except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Erreur parsing event : %s", err)
            return {"id": event.get("id"), "raw": event}
