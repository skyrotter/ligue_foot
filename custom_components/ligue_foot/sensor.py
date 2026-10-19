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


def compact(m: dict) -> dict:
    """Version légère d'un match, pour les attributs consommés par les cartes."""
    return {
        "home": m["home"]["name"],
        "away": m["away"]["name"],
        "home_logo": m["home"]["logo"],
        "away_logo": m["away"]["logo"],
        "home_score": m["home"]["score"],
        "away_score": m["away"]["score"],
        "kickoff": m["kickoff"].isoformat(),
        "state": m["state"],
        "venue": m["venue"],
    }


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
        entities.append(MatchdaySensor(coordinator, league))
    async_add_entities(entities)


class _TeamSensor(CoordinatorEntity[LigueFootCoordinator], SensorEntity):
    _attr_has_entity_name = True
    # Gros attributs : inutile de les stocker dans l'historique
    _unrecorded_attributes = frozenset({"last_matches", "opponent_logo", "team_logo"})

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
        mine = match["home"] if is_home else match["away"]
        return {
            "team": self._team["name"],
            "team_logo": mine["logo"],
            "league": LEAGUES.get(match["league"], match["league"]),
            "match_state": match["state"],  # pre / in / post
            "home_team": match["home"]["name"],
            "away_team": match["away"]["name"],
            "home_logo": match["home"]["logo"],
            "away_logo": match["away"]["logo"],
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
        attrs["team"] = self._team["name"]
        attrs["last_matches"] = self.coordinator.last_matches(self._league, self._team_id)
        attrs["form"] = [m["result"] for m in attrs["last_matches"]]
        return attrs


class StandingsSensor(CoordinatorEntity[LigueFootCoordinator], SensorEntity):
    """Leader du championnat ; le tableau complet est dans l'attribut « table »."""

    _attr_has_entity_name = True
    _attr_translation_key = "standings"
    _unrecorded_attributes = frozenset({"table"})

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


class MatchdaySensor(CoordinatorEntity[LigueFootCoordinator], SensorEntity):
    """Journée de championnat : date du prochain match ; listes en attributs."""

    _attr_has_entity_name = True
    _attr_translation_key = "matchday"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _unrecorded_attributes = frozenset({"results", "upcoming"})

    def __init__(self, coordinator: LigueFootCoordinator, league: str) -> None:
        super().__init__(coordinator)
        self._league = league
        self._attr_unique_id = f"{league}_matchday"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, league)},
            name=LEAGUES.get(league, league),
            manufacturer="ESPN",
        )

    @property
    def native_value(self):
        _, upcoming = self.coordinator.matchday(self._league)
        return upcoming[0]["kickoff"] if upcoming else None

    @property
    def extra_state_attributes(self):
        results, upcoming = self.coordinator.matchday(self._league)
        return {
            "league": LEAGUES.get(self._league, self._league),
            "results": [compact(m) for m in results],
            "upcoming": [compact(m) for m in upcoming],
        }
