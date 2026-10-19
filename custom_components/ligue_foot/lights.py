"""Effets lumineux les jours de match (Philips Hue, Ambilight, toute entité light)."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util import dt as dt_util

from .api import EspnApi, EspnApiError
from .const import (
    CONF_LIGHT_GOAL,
    CONF_LIGHT_KICKOFF,
    CONF_LIGHT_PREMATCH,
    CONF_LIGHT_RESTORE,
    CONF_LIGHTS,
    UPDATE_INTERVAL_MINUTES,
)
from .coordinator import LigueFootCoordinator

_LOGGER = logging.getLogger(__name__)

SCENE_ID = "ligue_foot_avant_match"
LIVE_INTERVAL = timedelta(minutes=1)  # rafraîchissement rapide pendant un match


def _rgb(value: str | None) -> tuple[int, int, int] | None:
    try:
        h = value.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except (AttributeError, ValueError):
        return None


def _lum(c: tuple[int, int, int]) -> float:
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _palette(primary: str | None, alt: str | None):
    """Couleur principale + couleur de flash (une lampe ne rend pas bien le noir)."""
    p, a = _rgb(primary), _rgb(alt)
    if p is None or _lum(p) < 40:
        p = a if a is not None and _lum(a) >= 40 else (255, 255, 255)
    if a is None or a == p:
        a = (255, 255, 255)
    return p, a


def _int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


class LightManager:
    """Habille les lampes aux couleurs de l'équipe : avant-match, coup d'envoi, buts."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, coordinator: LigueFootCoordinator
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.coordinator = coordinator
        self._colors: dict[tuple[str, str], tuple] = {}
        self._scores: dict[str, tuple[int, int]] = {}
        self._active: dict | None = None  # {"id": match, "live": bool}
        self._snapshot_taken = False
        self._flashing = False
        self._triggers: list = []
        self._failsafe = None
        self._unsub = None

    # ------------------------------------------------------------- options
    @property
    def lights(self) -> list[str]:
        return self.entry.options.get(CONF_LIGHTS) or []

    def _opt(self, key: str, default):
        return self.entry.options.get(key, default)

    # ---------------------------------------------------------- cycle de vie
    async def async_start(self) -> None:
        if not self.lights:
            return
        api = EspnApi(async_get_clientsession(self.hass))
        for league in self.coordinator.leagues:
            try:
                for team in await api.teams(league):
                    self._colors[(league, team["id"])] = _palette(
                        team.get("color"), team.get("alternate_color")
                    )
            except EspnApiError:
                _LOGGER.warning("Couleurs des équipes indisponibles pour %s", league)
        self._unsub = self.coordinator.async_add_listener(self._on_update)
        self._on_update()

    @callback
    def stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
        self._cancel_triggers()
        if self._failsafe:
            self._failsafe()
            self._failsafe = None

    def _cancel_triggers(self) -> None:
        for unsub in self._triggers:
            unsub()
        self._triggers = []

    def _palette_for(self, team: dict):
        return self._colors.get((team["league"], team["id"])) or (
            (255, 255, 255),
            (255, 255, 255),
        )

    # ------------------------------------------------------ données ESPN
    @callback
    def _on_update(self) -> None:
        self._cancel_triggers()
        now = dt_util.utcnow()
        live: list[tuple[dict, dict]] = []
        upcoming: list[tuple[dict, dict]] = []
        for team in self.coordinator.teams:
            for m in self.coordinator.data["matches"].get(team["league"], []):
                if team["id"] not in (m["home"]["id"], m["away"]["id"]):
                    continue
                if m["state"] == "in":
                    live.append((team, m))
                elif m["state"] == "pre" and m["kickoff"] > now:
                    upcoming.append((team, m))

        # Rafraîchissement rapide pendant un match, normal sinon
        self.coordinator.update_interval = (
            LIVE_INTERVAL if live else timedelta(minutes=UPDATE_INTERVAL_MINUTES)
        )

        # Buts
        old, new = self._scores, {}
        for team, m in live:
            score = (_int(m["home"]["score"]), _int(m["away"]["score"]))
            new[m["id"]] = score
            prev = old.get(m["id"])
            side = 0 if m["home"]["id"] == team["id"] else 1
            if prev is not None and score[side] > prev[side] and self._opt(CONF_LIGHT_GOAL, True):
                self.hass.async_create_task(self._flash(team))
        self._scores = new

        # Coup d'envoi / fin de match
        if live:
            team, m = live[0]
            if self._active and self._active["id"] == m["id"]:
                self._active["live"] = True
            elif self._opt(CONF_LIGHT_KICKOFF, True):
                self.hass.async_create_task(self._begin(team, m, True))
        elif self._active and self._active["live"]:
            self.hass.async_create_task(self._finish())

        # Déclencheurs à venir : ambiance avant-match + rafraîchissement au coup d'envoi
        minutes = _int(self._opt(CONF_LIGHT_PREMATCH, 0))
        for team, m in upcoming:
            for delay in (timedelta(seconds=30), timedelta(minutes=2)):
                self._triggers.append(
                    async_track_point_in_time(
                        self.hass, self._refresh_cb, m["kickoff"] + delay
                    )
                )
            start = m["kickoff"] - timedelta(minutes=minutes)
            if minutes > 0 and start > now:
                self._triggers.append(
                    async_track_point_in_time(self.hass, self._prematch_cb(team, m), start)
                )

    @callback
    def _refresh_cb(self, _now) -> None:
        self.hass.async_create_task(self.coordinator.async_request_refresh())

    def _prematch_cb(self, team: dict, match: dict):
        @callback
        def _cb(_now) -> None:
            self.hass.async_create_task(self._begin(team, match, False))

        return _cb

    @callback
    def _failsafe_cb(self, _now) -> None:
        self.hass.async_create_task(self._finish())

    # ------------------------------------------------------------ effets
    async def _begin(self, team: dict, match: dict, live: bool) -> None:
        if self._active is None:
            await self._snapshot()
        self._active = {"id": match["id"], "live": live}
        await self._set(self._palette_for(team)[0])
        # Sécurité : on rend les lampes 3 h après le coup d'envoi quoi qu'il arrive
        if self._failsafe:
            self._failsafe()
        self._failsafe = async_track_point_in_time(
            self.hass, self._failsafe_cb, match["kickoff"] + timedelta(hours=3)
        )

    async def _finish(self) -> None:
        if self._active is None:
            return
        self._active = None
        if self._failsafe:
            self._failsafe()
            self._failsafe = None
        await self._restore()

    async def _flash(self, team: dict) -> None:
        if self._flashing:
            return
        self._flashing = True
        try:
            temporary = self._active is None
            if temporary:
                await self._snapshot()
            main, alt = self._palette_for(team)
            for _ in range(3):
                await self._set(alt)
                await asyncio.sleep(0.7)
                await self._set(main)
                await asyncio.sleep(0.7)
            if temporary:
                await self._restore()
        finally:
            self._flashing = False

    async def _set(self, rgb: tuple[int, int, int]) -> None:
        await self._call(
            "light",
            "turn_on",
            {"entity_id": self.lights, "rgb_color": list(rgb), "brightness": 255},
        )

    async def _snapshot(self) -> None:
        if not self._opt(CONF_LIGHT_RESTORE, True):
            return
        self._snapshot_taken = await self._call(
            "scene",
            "create",
            {"scene_id": SCENE_ID, "snapshot_entities": self.lights},
        )

    async def _restore(self) -> None:
        if self._opt(CONF_LIGHT_RESTORE, True) and self._snapshot_taken:
            await self._call(
                "scene", "turn_on", {"entity_id": f"scene.{SCENE_ID}"}
            )
        self._snapshot_taken = False

    async def _call(self, domain: str, service: str, data: dict) -> bool:
        try:
            await self.hass.services.async_call(domain, service, data, blocking=True)
            return True
        except Exception as err:  # noqa: BLE001 - une lampe en panne ne doit rien casser
            _LOGGER.warning("Lumières : %s.%s a échoué (%s)", domain, service, err)
            return False
