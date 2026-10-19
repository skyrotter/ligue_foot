"""Config flow : choix des ligues, des équipes favorites, puis options de rappel."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import EspnApi, EspnApiError
from .const import (
    CONF_LEAGUES,
    CONF_LIGHT_GOAL,
    CONF_LIGHT_KICKOFF,
    CONF_LIGHT_PREMATCH,
    CONF_LIGHT_RESTORE,
    CONF_LIGHTS,
    CONF_MESSAGE,
    CONF_NOTIFY_SERVICE,
    CONF_REMINDER_MINUTES,
    CONF_TEAMS,
    DEFAULT_MESSAGE,
    DEFAULT_REMINDER_MINUTES,
    DOMAIN,
    LEAGUES,
)


class LigueFootConfigFlow(ConfigFlow, domain=DOMAIN):
    """Étape 1 : ligues. Étape 2 : équipes (sélection multiple)."""

    VERSION = 1

    def __init__(self) -> None:
        self._leagues: list[str] = []
        # "fra.1:160" -> {"league": "fra.1", "id": "160", "name": "Paris Saint-Germain"}
        self._teams_by_key: dict[str, dict] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}
        if user_input is not None:
            self._leagues = user_input[CONF_LEAGUES]
            api = EspnApi(async_get_clientsession(self.hass))
            try:
                self._teams_by_key = {}
                for league in self._leagues:
                    for team in await api.teams(league):
                        self._teams_by_key[f"{league}:{team['id']}"] = {
                            "league": league,
                            **team,
                        }
            except EspnApiError:
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_teams()

        schema = vol.Schema(
            {
                vol.Required(CONF_LEAGUES, default=["fra.1"]): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=k, label=v)
                            for k, v in LEAGUES.items()
                        ],
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_teams(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            chosen = user_input[CONF_TEAMS]
            if not chosen:
                errors["base"] = "no_team"
            else:
                return self.async_create_entry(
                    title="Ligue Foot",
                    data={CONF_TEAMS: [self._teams_by_key[k] for k in chosen]},
                )

        options = [
            SelectOptionDict(
                value=key,
                label=f"{t['name']} ({LEAGUES[t['league']]})"
                if len(self._leagues) > 1
                else t["name"],
            )
            for key, t in self._teams_by_key.items()
        ]
        schema = vol.Schema(
            {
                vol.Required(CONF_TEAMS): SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        multiple=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="teams", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return LigueFootOptionsFlow()


class LigueFootOptionsFlow(OptionsFlow):
    """Options : délai du rappel, service de notification, texte du message."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        # Services notify.* disponibles sur l'instance
        notify_services = sorted(self.hass.services.async_services().get("notify", {}))
        opts = self.config_entry.options

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_NOTIFY_SERVICE,
                    description={"suggested_value": opts.get(CONF_NOTIFY_SERVICE)},
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=notify_services,
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),
                vol.Required(
                    CONF_REMINDER_MINUTES,
                    default=opts.get(CONF_REMINDER_MINUTES, DEFAULT_REMINDER_MINUTES),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=5,
                        max=1440,
                        step=5,
                        unit_of_measurement="min",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_MESSAGE, default=opts.get(CONF_MESSAGE, DEFAULT_MESSAGE)
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                # Lumières : Philips Hue, Ambilight (Philips TV), toute entité light
                vol.Optional(
                    CONF_LIGHTS,
                    description={"suggested_value": opts.get(CONF_LIGHTS)},
                ): EntitySelector(EntitySelectorConfig(domain="light", multiple=True)),
                vol.Required(
                    CONF_LIGHT_KICKOFF, default=opts.get(CONF_LIGHT_KICKOFF, True)
                ): BooleanSelector(),
                vol.Required(
                    CONF_LIGHT_GOAL, default=opts.get(CONF_LIGHT_GOAL, True)
                ): BooleanSelector(),
                vol.Required(
                    CONF_LIGHT_PREMATCH, default=opts.get(CONF_LIGHT_PREMATCH, 0)
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0,
                        max=240,
                        step=5,
                        unit_of_measurement="min",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_LIGHT_RESTORE, default=opts.get(CONF_LIGHT_RESTORE, True)
                ): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
