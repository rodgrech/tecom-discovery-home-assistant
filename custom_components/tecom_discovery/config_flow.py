"""Config flow for Tecom Discovery."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    DiscoveryApi,
    DiscoveryAuthenticationError,
    DiscoveryConnectionError,
    DiscoveryError,
)
from .const import (
    CONF_AREA_COUNT,
    CONF_INPUT_COUNT,
    CONF_RELAY_COUNT,
    DEFAULT_AREA_COUNT,
    DEFAULT_INPUT_COUNT,
    DEFAULT_RELAY_COUNT,
    DOMAIN,
)


class DiscoveryConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure a Discovery panel."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip().rstrip("/")
            await self.async_set_unique_id(host.lower())
            self._abort_if_unique_id_configured()

            api = DiscoveryApi(
                async_get_clientsession(self.hass),
                host,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input[CONF_VERIFY_SSL],
            )
            try:
                await api.async_login()
                panel = await api.async_panel_info()
            except DiscoveryAuthenticationError:
                errors["base"] = "invalid_auth"
            except DiscoveryConnectionError:
                errors["base"] = "cannot_connect"
            except DiscoveryError:
                errors["base"] = "unknown"
            else:
                title = str(
                    panel.get("board")
                    or panel.get("ultraSync")
                    or f"Discovery {host}"
                )
                return self.async_create_entry(title=title, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default="192.168.1.99"): str,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_VERIFY_SSL, default=False): bool,
                vol.Required(CONF_INPUT_COUNT, default=DEFAULT_INPUT_COUNT): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=1008)
                ),
                vol.Required(CONF_AREA_COUNT, default=DEFAULT_AREA_COUNT): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=99)
                ),
                vol.Required(CONF_RELAY_COUNT, default=DEFAULT_RELAY_COUNT): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=512)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""

        return DiscoveryOptionsFlow()


class DiscoveryOptionsFlow(OptionsFlow):
    """Configure entity ranges."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_INPUT_COUNT,
                        default=current.get(CONF_INPUT_COUNT, DEFAULT_INPUT_COUNT),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=1008)),
                    vol.Required(
                        CONF_AREA_COUNT,
                        default=current.get(CONF_AREA_COUNT, DEFAULT_AREA_COUNT),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=99)),
                    vol.Required(
                        CONF_RELAY_COUNT,
                        default=current.get(CONF_RELAY_COUNT, DEFAULT_RELAY_COUNT),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=512)),
                }
            ),
        )
