"""Config flow for Tecom Discovery."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    AreaSelector,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    DiscoveryApi,
    DiscoveryAuthenticationError,
    DiscoveryConnectionError,
    DiscoveryError,
)
from .const import (
    CONF_AREA_COUNT,
    CONF_CONTROL_CODE,
    CONF_INPUT_AREA,
    CONF_INPUT_COUNT,
    CONF_INPUT_MAPPINGS,
    CONF_INPUT_TYPE,
    CONF_RELAY_COUNT,
    DEFAULT_AREA_COUNT,
    DEFAULT_INPUT_COUNT,
    DEFAULT_RELAY_COUNT,
    DOMAIN,
    INPUT_TYPES,
)
from .entity import is_motion_input


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

    def __init__(self) -> None:
        self._pending_options: dict[str, Any] = {}
        self._inputs = []
        self._input_index = 0
        self._mappings: dict[str, dict[str, str]] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._pending_options = dict(user_input)
            current_mappings = self.config_entry.options.get(
                CONF_INPUT_MAPPINGS, {}
            )
            self._mappings = {
                str(number): dict(mapping)
                for number, mapping in current_mappings.items()
            }
            coordinator = self.config_entry.runtime_data
            self._inputs = [
                item
                for item in coordinator.data.inputs
                if item.raw.get("entityName") or str(item.number) in self._mappings
            ]
            self._input_index = 0
            if self._inputs:
                return await self.async_step_input()
            self._pending_options[CONF_INPUT_MAPPINGS] = self._mappings
            return self.async_create_entry(title="", data=self._pending_options)

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
                    vol.Optional(
                        CONF_CONTROL_CODE,
                        description={
                            "suggested_value": current.get(CONF_CONTROL_CODE, "")
                        },
                    ): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.PASSWORD,
                            autocomplete="new-password",
                        )
                    ),
                }
            ),
        )

    async def async_step_input(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure one detected panel input."""

        item = self._inputs[self._input_index]
        key = str(item.number)
        existing = self._mappings.get(key, {})

        if user_input is not None:
            mapping = {CONF_INPUT_TYPE: user_input[CONF_INPUT_TYPE]}
            if area_id := user_input.get(CONF_INPUT_AREA):
                mapping[CONF_INPUT_AREA] = area_id
            self._mappings[key] = mapping
            self._input_index += 1
            if self._input_index >= len(self._inputs):
                self._pending_options[CONF_INPUT_MAPPINGS] = self._mappings
                return self.async_create_entry(title="", data=self._pending_options)
            return await self.async_step_input()

        default_type = existing.get(
            CONF_INPUT_TYPE, "motion" if is_motion_input(item) else "sealed"
        )
        type_options = [
            SelectOptionDict(label=value.replace("_", " ").title(), value=value)
            for value in INPUT_TYPES
        ]
        schema: dict[Any, Any] = {
            vol.Required(
                CONF_INPUT_TYPE,
                description={"suggested_value": default_type},
            ): SelectSelector(SelectSelectorConfig(options=type_options)),
        }
        schema[
            vol.Optional(
                CONF_INPUT_AREA,
                description={"suggested_value": existing.get(CONF_INPUT_AREA)},
            )
        ] = AreaSelector()
        return self.async_show_form(
            step_id="input",
            data_schema=vol.Schema(schema),
            description_placeholders={
                "input_name": item.name,
                "input_number": str(item.number),
                "input_state": item.state.title(),
                "position": str(self._input_index + 1),
                "total": str(len(self._inputs)),
            },
        )
