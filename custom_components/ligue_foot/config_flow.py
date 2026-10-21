"""Config flow pour l'intégration Ligue Foot."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_LEAGUE,
    CONF_TEAM_ID,
    CONF_TEAM_NAME,
    DOMAIN,
    ESPN_API_BASE,
    ESPN_TEAMS,
    LEAGUE_BUNDESLIGA,
    LEAGUE_JUPILER_PRO,
    LEAGUE_LALIGA,
    LEAGUE_LIGA_PORTUGAL,
    LEAGUE_LIGUE1,
    LEAGUE_LIGUE2,
    LEAGUE_PREMIER_LEAGUE,
    LEAGUE_SERIE_A,
    LEAGUE_UEFA_CL,
    LEAGUE_UEFA_CONF,
    LEAGUE_UEFA_EL,
    LEAGUES,
)

_LOGGER = logging.getLogger(__name__)


class LigueFootConfigFlow(ConfigFlow, domain=DOMAIN):
    """Gère le flux de configuration en 3 étapes : ligue → équipe → confirmation."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise le flux."""
        self._league: str | None = None
        self._teams: list[dict] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Étape 1 : choix de la ligue."""
        if user_input is not None:
            self._league = user_input[CONF_LEAGUE]
            return await self.async_step_team()

        # Organise les ligues par catégorie
        league_options = []

        # Ligues nationales françaises
        league_options.append(
            SelectOptionDict(
                value=LEAGUE_LIGUE1,
                label=f"🇫🇷 {LEAGUES[LEAGUE_LIGUE1]['name']}"
            )
        )
        league_options.append(
            SelectOptionDict(
                value=LEAGUE_LIGUE2,
                label=f"🇫🇷 {LEAGUES[LEAGUE_LIGUE2]['name']}"
            )
        )

        # Autres ligues nationales
        other_leagues = [
            (LEAGUE_PREMIER_LEAGUE, "🇬🇧"),
            (LEAGUE_LALIGA, "🇪🇸"),
            (LEAGUE_BUNDESLIGA, "🇩🇪"),
            (LEAGUE_SERIE_A, "🇮🇹"),
            (LEAGUE_LIGA_PORTUGAL, "🇵🇹"),
            (LEAGUE_JUPILER_PRO, "🇧🇪"),
        ]
        for league_key, flag in other_leagues:
            league_options.append(
                SelectOptionDict(
                    value=league_key,
                    label=f"{flag} {LEAGUES[league_key]['name']}"
                )
            )

        # Compétitions européennes
        league_options.append(
            SelectOptionDict(
                value=LEAGUE_UEFA_CL,
                label=f"🇪🇺 {LEAGUES[LEAGUE_UEFA_CL]['name']}"
            )
        )
        league_options.append(
            SelectOptionDict(
                value=LEAGUE_UEFA_EL,
                label=f"🇪🇺 {LEAGUES[LEAGUE_UEFA_EL]['name']}"
            )
        )
        league_options.append(
            SelectOptionDict(
                value=LEAGUE_UEFA_CONF,
                label=f"🇪🇺 {LEAGUES[LEAGUE_UEFA_CONF]['name']}"
            )
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_LEAGUE): SelectSelector(
                    SelectSelectorConfig(
                        options=league_options,
                        mode=SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            description_placeholders={
                "supported_leagues": "Ligue 1, Ligue 2, Champions League, Europa League, Conference League"
            },
        )

    async def async_step_team(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Étape 2 : choix de l'équipe."""
        errors: dict[str, str] = {}

        if user_input is not None:
            team_id = user_input[CONF_TEAM_ID]
            team_name = next(
                (t["name"] for t in self._teams if t["id"] == team_id), team_id
            )

            # Évite les doublons ligue+équipe
            await self.async_set_unique_id(f"{self._league}_{team_id}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"{team_name} ({LEAGUES[self._league]['name']})",
                data={
                    CONF_LEAGUE: self._league,
                    CONF_TEAM_ID: team_id,
                    CONF_TEAM_NAME: team_name,
                },
            )

        # Charge la liste des équipes si pas encore fait
        if not self._teams:
            try:
                self._teams = await self._fetch_teams()
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"

        if errors or not self._teams:
            return self.async_show_form(
                step_id="team",
                data_schema=vol.Schema({}),
                errors=errors,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_TEAM_ID): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=t["id"], label=t["name"])
                            for t in sorted(self._teams, key=lambda x: x["name"])
                        ],
                        mode=SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="team", data_schema=schema)

    async def _fetch_teams(self) -> list[dict]:
        """Récupère la liste des équipes de la ligue via ESPN."""
        assert self._league is not None
        espn_id = LEAGUES[self._league]["espn_id"]
        url = ESPN_TEAMS.format(base=ESPN_API_BASE, league_id=espn_id)
        session = async_get_clientsession(self.hass)
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            data = await resp.json()

        teams = []
        for item in data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
            team = item.get("team", {})
            if team.get("id") and team.get("displayName"):
                teams.append({"id": team["id"], "name": team["displayName"]})
        return teams

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Retourne le flux d'options."""
        return LigueFootOptionsFlow(config_entry)


class LigueFootOptionsFlow(OptionsFlow):
    """Gère les options modifiables après installation."""

    def __init__(self, config_entry) -> None:
        """Initialise le flux d'options."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Affiche les options disponibles."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    "notify_kickoff",
                    default=options.get("notify_kickoff", True),
                ): bool,
                vol.Optional(
                    "notify_goal",
                    default=options.get("notify_goal", True),
                ): bool,
                vol.Optional(
                    "notify_red_card",
                    default=options.get("notify_red_card", False),
                ): bool,
                vol.Optional(
                    "notify_match_end",
                    default=options.get("notify_match_end", True),
                ): bool,
                vol.Optional(
                    "notify_service",
                    default=options.get("notify_service", ""),
                ): str,
                vol.Optional(
                    "silence_start",
                    default=options.get("silence_start", "23:00"),
                ): str,
                vol.Optional(
                    "silence_end",
                    default=options.get("silence_end", "07:00"),
                ): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
