"""Capteurs binaires « jour de match » : un par équipe + un global (tous les favoris)."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, LEAGUES
from .coordinator import LigueFootCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: LigueFootCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = [MyTeamsMatchDay(coordinator, entry)]
    entities += [TeamMatchDay(coordinator, team) for team in coordinator.teams]
    async_add_entities(entities)


def _today(coordinator: LigueFootCoordinator, team: dict) -> list[dict]:
    """Matchs de l'équipe prévus aujourd'hui (heure locale), joués ou non."""
    today = dt_util.now().date()
    return [
        m
        for m in (coordinator.data or {}).get("matches", {}).get(team["league"], [])
        if team["id"] in (m["home"]["id"], m["away"]["id"])
        and dt_util.as_local(m["kickoff"]).date() == today
    ]


def _minutes_until(match: dict) -> int | None:
    """Minutes avant le coup d'envoi (None si le match a commencé)."""
    if match["state"] != "pre":
        return None
    return max(0, int((match["kickoff"] - dt_util.utcnow()).total_seconds() // 60))


class _MatchDayBase(CoordinatorEntity[LigueFootCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _unrecorded_attributes = frozenset({"opponent_logo", "matches"})

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Recalcul chaque minute : minuit, coup d'envoi... sans attendre ESPN.
        self.async_on_remove(
            async_track_time_interval(self.hass, self._tick, timedelta(minutes=1))
        )

    @callback
    def _tick(self, _now) -> None:
        self.async_write_ha_state()


class TeamMatchDay(_MatchDayBase):
    """Allumé toute la journée si l'équipe joue aujourd'hui."""

    _attr_translation_key = "match_day"

    def __init__(self, coordinator: LigueFootCoordinator, team: dict) -> None:
        super().__init__(coordinator)
        self._team = team
        self._attr_unique_id = f"{team['league']}_{team['id']}_match_day"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{team['league']}_{team['id']}")},
            name=team["name"],
            manufacturer="ESPN",
            model=LEAGUES.get(team["league"], team["league"]),
        )

    @property
    def is_on(self) -> bool:
        return bool(_today(self.coordinator, self._team))

    @property
    def extra_state_attributes(self) -> dict:
        matches = _today(self.coordinator, self._team)
        if not matches:
            return {}
        m = matches[0]
        at_home = m["home"]["id"] == self._team["id"]
        opp = m["away"] if at_home else m["home"]
        return {
            "opponent": opp["name"],
            "opponent_logo": opp["logo"],
            "at_home": at_home,
            "venue": m["venue"],
            "kickoff": m["kickoff"].isoformat(),
            "match_state": m["state"],  # pre / in / post
            "minutes_until": _minutes_until(m),
        }


class MyTeamsMatchDay(_MatchDayBase):
    """Allumé si au moins une de tes équipes favorites joue aujourd'hui."""

    _attr_translation_key = "any_match_day"

    def __init__(self, coordinator: LigueFootCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_any_match_day"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "favorites")},
            name="Ligue Foot",
            manufacturer="ESPN",
        )

    def _matches(self) -> list[tuple[dict, dict]]:
        out, seen = [], set()
        for team in self.coordinator.teams:
            for m in _today(self.coordinator, team):
                if m["id"] not in seen:
                    seen.add(m["id"])
                    out.append((team, m))
        return sorted(out, key=lambda tm: tm[1]["kickoff"])

    @property
    def is_on(self) -> bool:
        return bool(self._matches())

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "count": len(self._matches()),
            "matches": [
                {
                    "team": team["name"],
                    "home": m["home"]["name"],
                    "away": m["away"]["name"],
                    "kickoff": m["kickoff"].isoformat(),
                    "match_state": m["state"],
                    "minutes_until": _minutes_until(m),
                }
                for team, m in self._matches()
            ],
        }
