"""Capteurs binaires pour l'intégration Ligue Foot."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
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
    """Crée les capteurs binaires pour cette entrée."""
    coordinator: LigueFootCoordinator = hass.data[DOMAIN][entry.entry_id]
    team_name = entry.data[CONF_TEAM_NAME]

    async_add_entities(
        [
            LigueFootMatchLiveSensor(coordinator, entry, team_name),
            LigueFootMatchTodaySensor(coordinator, entry, team_name),
            LigueFootMatchTomorrowSensor(coordinator, entry, team_name),
        ]
    )


class LigueFootBaseBinary(CoordinatorEntity[LigueFootCoordinator], BinarySensorEntity):
    """Capteur binaire de base."""

    def __init__(self, coordinator, entry, team_name, suffix) -> None:
        """Initialise."""
        super().__init__(coordinator)
        self._entry = entry
        self._team_name = team_name
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Ligue Foot · {team_name}",
            manufacturer="ESPN",
            model=LEAGUES.get(entry.data.get("league", ""), {}).get("name", ""),
        )


class LigueFootMatchLiveSensor(LigueFootBaseBinary):
    """Match en cours (ON si un match de l'équipe est live)."""

    _attr_icon = "mdi:soccer-field"

    def __init__(self, coordinator, entry, team_name) -> None:
        """Initialise."""
        super().__init__(coordinator, entry, team_name, "match_live")
        self._attr_name = f"{team_name} — Match en cours"

    @property
    def is_on(self) -> bool:
        """Retourne True si un match est en cours."""
        return bool(self.coordinator.data.get("live_match"))


class LigueFootMatchTodaySensor(LigueFootBaseBinary):
    """Match aujourd'hui (ON si un match est prévu ce jour)."""

    _attr_icon = "mdi:calendar-today"

    def __init__(self, coordinator, entry, team_name) -> None:
        """Initialise."""
        super().__init__(coordinator, entry, team_name, "match_today")
        self._attr_name = f"{team_name} — Match aujourd'hui"

    @property
    def is_on(self) -> bool:
        """Retourne True si un match a lieu aujourd'hui."""
        next_match = self.coordinator.data.get("next_match")
        if not next_match:
            return False
        match_date = next_match.get("date")
        if not match_date:
            return False
        return match_date.date() == dt_util.now().date()


class LigueFootMatchTomorrowSensor(LigueFootBaseBinary):
    """Match demain (ON si un match est prévu demain)."""

    _attr_icon = "mdi:calendar-arrow-right"

    def __init__(self, coordinator, entry, team_name) -> None:
        """Initialise."""
        super().__init__(coordinator, entry, team_name, "match_tomorrow")
        self._attr_name = f"{team_name} — Match demain"

    @property
    def is_on(self) -> bool:
        """Retourne True si un match a lieu demain."""
        next_match = self.coordinator.data.get("next_match")
        if not next_match:
            return False
        match_date = next_match.get("date")
        if not match_date:
            return False
        from datetime import timedelta
        tomorrow = (dt_util.now() + timedelta(days=1)).date()
        return match_date.date() == tomorrow
