"""Capteurs : prochain match, dernier résultat (par équipe), classement (par ligue)."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LEAGUES
from .coordinator import LigueFootCoordinator, result_for


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: LigueFootCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []
    for team in coordinator.teams:
        entities.append(NextMatchSensor(coordinator, team))
        entities.append(LastResultSensor(coordinator, team))
    for league in coordinator.leagues:
        entities.append(StandingsSensor(coordinator, league))
    async_add_entities(entities)


class _TeamSensor(CoordinatorEntity[LigueFootCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: LigueFootCoordinator, team: dict) -> None:
        super().__init__(coordinator)
        self._team = team
        self._league = team["league"]
        self._team_id = team["id"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{self._league}_{self._team_id}")},
            name=team["name"],
            manufacturer="ESPN",
            model=LEAGUES.get(self._league, self._league),
        )

    def _match_attrs(self, match: dict) -> dict:
        is_home = match["home"]["id"] == self._team_id
        opponent = match["away"] if is_home else match["home"]
        return {
            "league": LEAGUES.get(match["league"], match["league"]),
            "home_team": match["home"]["name"],
            "away_team": match["away"]["name"],
            "home_score": match["home"]["score"],
            "away_score": match["away"]["score"],
            "venue": match["venue"],
            "at_home": is_home,
            "opponent": opponent["name"],
            "opponent_logo": opponent["logo"],
            "kickoff": match["kickoff"].isoformat(),
        }


class NextMatchSensor(_TeamSensor):
    """Date du prochain match (horodatage) + détails en attributs."""

    _attr_translation_key = "next_match"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, team) -> None:
        super().__init__(coordinator, team)
        self._attr_unique_id = f"{self._league}_{self._team_id}_next_match"

    @property
    def native_value(self):
        match = self.coordinator.next_match(self._league, self._team_id)
        return match["kickoff"] if match else None

    @property
    def extra_state_attributes(self):
        match = self.coordinator.next_match(self._league, self._team_id)
        return self._match_attrs(match) if match else {}


class LastResultSensor(_TeamSensor):
    """Dernier résultat sous forme « Lyon 2-1 Nice »."""

    _attr_translation_key = "last_result"

    def __init__(self, coordinator, team) -> None:
        super().__init__(coordinator, team)
        self._attr_unique_id = f"{self._league}_{self._team_id}_last_result"

    @property
    def native_value(self):
        m = self.coordinator.last_match(self._league, self._team_id)
        if not m:
            return None
        return f"{m['home']['name']} {m['home']['score']}-{m['away']['score']} {m['away']['name']}"

    @property
    def extra_state_attributes(self):
        m = self.coordinator.last_match(self._league, self._team_id)
        attrs = self._match_attrs(m) if m else {}
        attrs["result"] = result_for(m, self._team_id) if m else None  # V / N / D
        attrs["form"] = self.coordinator.form(self._league, self._team_id)
        return attrs


class StandingsSensor(CoordinatorEntity[LigueFootCoordinator], SensorEntity):
    """Leader du championnat ; le tableau complet est dans l'attribut « table »."""

    _attr_has_entity_name = True
    _attr_translation_key = "standings"

    def __init__(self, coordinator: LigueFootCoordinator, league: str) -> None:
        super().__init__(coordinator)
        self._league = league
        self._attr_unique_id = f"{league}_standings"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, league)},
            name=LEAGUES.get(league, league),
            manufacturer="ESPN",
        )

    @property
    def native_value(self):
        table = self.coordinator.data["standings"].get(self._league) or []
        return table[0]["team"] if table else None

    @property
    def extra_state_attributes(self):
        return {"table": self.coordinator.data["standings"].get(self._league, [])}
