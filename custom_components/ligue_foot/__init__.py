"""Intégration Ligue Foot : équipes favorites de Ligue 1 / Ligue 2 + rappels."""
from __future__ import annotations

from datetime import timedelta
import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util import dt as dt_util

from .const import (
    CARDS_URL,
    CARDS_VERSION,
    CONF_MESSAGE,
    CONF_NOTIFY_SERVICE,
    CONF_REMINDER_MINUTES,
    DEFAULT_MESSAGE,
    DEFAULT_REMINDER_MINUTES,
    DOMAIN,
    LEAGUES,
)
from .coordinator import LigueFootCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


class ReminderManager:
    """Planifie une notification avant chaque prochain match des favoris."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, coordinator: LigueFootCoordinator
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.coordinator = coordinator
        self._unsubs: dict[str, callable] = {}

    @callback
    def reschedule(self) -> None:
        """Annule puis recrée les rappels (appelé à chaque mise à jour des données)."""
        self.cancel()
        service = self.entry.options.get(CONF_NOTIFY_SERVICE)
        if not service:
            return  # rappels désactivés tant qu'aucun service n'est choisi
        minutes = self.entry.options.get(CONF_REMINDER_MINUTES, DEFAULT_REMINDER_MINUTES)
        now = dt_util.utcnow()

        for team in self.coordinator.teams:
            match = self.coordinator.next_match(team["league"], team["id"])
            # Un match entre deux favoris ne notifie qu'une fois (clé = id du match)
            if not match or match["id"] in self._unsubs or match["state"] != "pre":
                continue
            fire_at = match["kickoff"] - timedelta(minutes=minutes)
            if fire_at <= now:
                continue
            self._unsubs[match["id"]] = async_track_point_in_time(
                self.hass, self._make_job(service, minutes, match), fire_at
            )

    def _make_job(self, service: str, minutes: int, match: dict):
        async def _fire(_now) -> None:
            template = self.entry.options.get(CONF_MESSAGE) or DEFAULT_MESSAGE
            values = {
                "home": match["home"]["name"],
                "away": match["away"]["name"],
                "time": dt_util.as_local(match["kickoff"]).strftime("%H:%M"),
                "minutes": minutes,
                "venue": match["venue"] or "",
                "league": LEAGUES.get(match["league"], match["league"]),
            }
            try:
                message = template.format(**values)
            except (KeyError, IndexError, ValueError):
                message = DEFAULT_MESSAGE.format(**values)  # texte perso invalide
            try:
                await self.hass.services.async_call(
                    "notify",
                    service,
                    {"title": values["league"], "message": message},
                    blocking=False,
                )
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Échec de l'envoi du rappel via notify.%s", service)

        return _fire

    @callback
    def cancel(self) -> None:
        for unsub in self._unsubs.values():
            unsub()
        self._unsubs.clear()


async def _async_register_cards(hass: HomeAssistant) -> None:
    """Sert le fichier JS des cartes et le charge automatiquement dans l'interface."""
    key = f"{DOMAIN}_frontend"
    if hass.data.get(key):
        return
    path = Path(__file__).parent / "frontend" / "ligue-foot-cards.js"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARDS_URL, str(path), False)]
    )
    add_extra_js_url(hass, f"{CARDS_URL}?v={CARDS_VERSION}")
    hass.data[key] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await _async_register_cards(hass)
    coordinator = LigueFootCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    reminders = ReminderManager(hass, entry, coordinator)
    reminders.reschedule()
    entry.async_on_unload(coordinator.async_add_listener(reminders.reschedule))
    entry.async_on_unload(reminders.cancel)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Recharge l'intégration quand les options changent (délai, service, message)
    entry.async_on_unload(entry.add_update_listener(_async_reload))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok
