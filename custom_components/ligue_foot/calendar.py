"""Entité calendrier pour l'intégration Ligue Foot.

Chaque entrée crée un calendrier qui liste les matchs de l'équipe
pour la compétition configurée uniquement (pas de repli sur 'tous les matchs').
Réutilise les données du coordinateur — pas de requête supplémentaire.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import CONF_TEAM_NAME, DOMAIN, LEAGUES
from .coordinator import LigueFootCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crée l'entité calendrier pour cette entrée."""
    coordinator: LigueFootCoordinator = hass.data[DOMAIN][entry.entry_id]
    team_name = entry.data[CONF_TEAM_NAME]
    async_add_entities([LigueFootCalendar(coordinator, entry, team_name)])


class LigueFootCalendar(CoordinatorEntity[LigueFootCoordinator], CalendarEntity):
    """Calendrier des matchs de l'équipe pour la compétition configurée."""

    def __init__(
        self,
        coordinator: LigueFootCoordinator,
        entry: ConfigEntry,
        team_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._team_name = team_name
        league_name = LEAGUES.get(entry.data.get("league", ""), {}).get("name", "")
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_name = f"{team_name} · {league_name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Ligue Foot · {team_name}",
            manufacturer="ESPN",
            model=league_name,
        )

    @property
    def event(self) -> CalendarEvent | None:
        live = self.coordinator.data.get("live_match")
        if live and live.get("date"):
            return self._to_calendar_event(live, 105)
        next_match = self.coordinator.data.get("next_match")
        if next_match and next_match.get("date"):
            return self._to_calendar_event(next_match, 105)
        return None

    async def async_get_events(self, hass, start_date, end_date):
        schedule = self.coordinator.data.get("schedule", {})
        events = []
        for raw_event in schedule.get("events", []):
            date_str = raw_event.get("date")
            if not date_str:
                continue
            try:
                match_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                continue
            if match_date < start_date or match_date > end_date:
                continue
            parsed = self.coordinator._parse_event(raw_event)
            events.append(self._to_calendar_event(parsed, 105))
        return events

    def _to_calendar_event(self, match, duration_minutes=105):
        start = match["date"]
        end = start + timedelta(minutes=duration_minutes)
        home = match.get("home_team", "?")
        away = match.get("away_team", "?")
        parts = []
        if match.get("matchday"): parts.append(f"J{\match['matchday']}")
        if match.get("venue"): parts.append(match["venue"])
        return CalendarEvent(
            start=start, end=end,
            summary=f"{home} – {away}",
            description=" · ".join(parts) if parts else None,
            location=match.get("venue"),
        )
