"""Capteurs pour l'intégration Ligue Foot."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LEAGUE, CONF_TEAM_NAME, DOMAIN, LEAGUES
from .coordinator import LigueFootCoordinator


def _entry_stats(entry: dict) -> dict[str, Any]:
    """Transforme la liste de stats ESPN en dict {nom: valeur}."""
    return {
        s.get("name"): s.get("value")
        for s in entry.get("stats", [])
        if isinstance(s, dict)
    }


def _get_tables(standings: dict) -> list[list[dict]]:
    """Retourne toutes les tables de classement, quelle que soit la structure ESPN.

    ESPN renvoie soit ``standings.entries``, soit ``children[].standings.entries``
    (une table par groupe ou par phase).
    """
    tables: list[list[dict]] = []
    if not isinstance(standings, dict):
        return tables
    direct = standings.get("standings")
    if isinstance(direct, dict) and direct.get("entries"):
        tables.append(direct["entries"])
    for child in standings.get("children") or []:
        child_standings = child.get("standings") if isinstance(child, dict) else None
        if isinstance(child_standings, dict) and child_standings.get("entries"):
            tables.append(child_standings["entries"])
    return tables


def _sort_entries(entries: list[dict]) -> list[dict]:
    """Trie les entrées par rang ESPN (ordre d'origine conservé si pas de rang)."""

    def _key(entry: dict) -> float:
        try:
            return float(_entry_stats(entry).get("rank"))
        except (TypeError, ValueError):
            return float("inf")

    return sorted(entries, key=_key)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crée les capteurs pour cette entrée."""
    coordinator: LigueFootCoordinator = hass.data[DOMAIN][entry.entry_id]
    team_name = entry.data[CONF_TEAM_NAME]

    async_add_entities(
        [
            LigueFootNextMatchSensor(coordinator, entry, team_name),
            LigueFootStandingsSensor(coordinator, entry, team_name),
            LigueFootFormSensor(coordinator, entry, team_name),
            LigueFootSyncStatusSensor(coordinator, entry, team_name),
        ]
    )


class LigueFootBaseSensor(CoordinatorEntity[LigueFootCoordinator], SensorEntity):
    """Capteur de base avec device info commun."""

    def __init__(
        self,
        coordinator: LigueFootCoordinator,
        entry: ConfigEntry,
        team_name: str,
        unique_suffix: str,
    ) -> None:
        """Initialise le capteur."""
        super().__init__(coordinator)
        self._entry = entry
        self._team_name = team_name
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Ligue Foot · {team_name}",
            manufacturer="ESPN",
            model=LEAGUES.get(entry.data.get(CONF_LEAGUE, ""), {}).get("name", ""),
        )


class LigueFootNextMatchSensor(LigueFootBaseSensor):
    """Capteur : prochain match de l'équipe."""

    _attr_icon = "mdi:soccer"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, entry, team_name) -> None:
        """Initialise."""
        super().__init__(coordinator, entry, team_name, "next_match")
        self._attr_name = f"{team_name} — Prochain match"

    @property
    def native_value(self) -> datetime | None:
        """Retourne la date du prochain match comme état principal."""
        match = self.coordinator.data.get("next_match")
        if not match:
            return None
        date: datetime | None = match.get("date")
        return date if isinstance(date, datetime) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose les détails du match."""
        match = self.coordinator.data.get("next_match")
        if not match:
            return {}
        return {
            "home_team": match.get("home_team"),
            "home_team_logo": match.get("home_team_logo"),
            "away_team": match.get("away_team"),
            "away_team_logo": match.get("away_team_logo"),
            "venue": match.get("venue"),
            "matchday": match.get("matchday"),
            "status": match.get("status"),
        }


class LigueFootStandingsSensor(LigueFootBaseSensor):
    """Capteur : classement complet de la ligue."""

    _attr_icon = "mdi:trophy"

    def __init__(self, coordinator, entry, team_name) -> None:
        """Initialise."""
        super().__init__(coordinator, entry, team_name, "standings")
        league_name = LEAGUES.get(entry.data.get(CONF_LEAGUE, ""), {}).get("name", "Ligue")
        self._attr_name = f"{league_name} — Classement"

    @property
    def native_value(self) -> int | None:
        """Retourne la position de l'équipe dans le classement."""
        standings = self.coordinator.data.get("standings")
        if not standings:
            return None
        return self._find_team_position(standings)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose le classement complet."""
        standings = self.coordinator.data.get("standings")
        if not standings:
            return {}
        return {"table": self._extract_table(standings)}

    def _team_table(self, standings: dict) -> list[dict]:
        """Retourne la table (triée) qui contient l'équipe, sinon la première."""
        tables = _get_tables(standings)
        team_id = str(self.coordinator.team_id)
        for entries in tables:
            if any(str(e.get("team", {}).get("id")) == team_id for e in entries):
                return _sort_entries(entries)
        return _sort_entries(tables[0]) if tables else []

    def _find_team_position(self, standings: dict) -> int | None:
        """Trouve la position de l'équipe dans le classement ESPN."""
        try:
            team_id = str(self.coordinator.team_id)
            for i, entry in enumerate(self._team_table(standings), 1):
                if str(entry.get("team", {}).get("id")) == team_id:
                    return i
        except Exception:  # noqa: BLE001
            pass
        return None

    def _extract_table(self, standings: dict) -> list[dict]:
        """Extrait le tableau de classement complet."""
        try:
            table = []
            for i, entry in enumerate(self._team_table(standings), 1):
                team = entry.get("team", {})
                stats = _entry_stats(entry)
                logos = team.get("logos") or [{}]
                table.append({
                    "position": i,
                    "team": team.get("displayName"),
                    "logo": logos[0].get("href", ""),
                    "points": stats.get("points"),
                    "played": stats.get("gamesPlayed"),
                    "wins": stats.get("wins"),
                    "draws": stats.get("ties"),
                    "losses": stats.get("losses"),
                    "gd": stats.get("pointDifferential"),
                })
            return table
        except Exception:  # noqa: BLE001
            return []


class LigueFootFormSensor(LigueFootBaseSensor):
    """Capteur : forme récente de l'équipe (5 derniers matchs)."""

    _attr_icon = "mdi:chart-line"

    def __init__(self, coordinator, entry, team_name) -> None:
        """Initialise."""
        super().__init__(coordinator, entry, team_name, "form")
        self._attr_name = f"{team_name} — Forme"

    @property
    def native_value(self) -> str | None:
        """Retourne la forme sous forme de chaîne (ex: W W D L W)."""
        form = self.coordinator.data.get("team_form", [])
        return " ".join(form) if form else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose la liste détaillée."""
        return {"results": self.coordinator.data.get("team_form", [])}


class LigueFootSyncStatusSensor(LigueFootBaseSensor):
    """Capteur : état de synchronisation avec ESPN."""

    _attr_icon = "mdi:cloud-sync"

    def __init__(self, coordinator, entry, team_name) -> None:
        """Initialise."""
        super().__init__(coordinator, entry, team_name, "sync_status")
        self._attr_name = f"{team_name} — Sync"

    @property
    def native_value(self) -> str:
        """Retourne l'état de synchronisation."""
        return self.coordinator.sync_status
