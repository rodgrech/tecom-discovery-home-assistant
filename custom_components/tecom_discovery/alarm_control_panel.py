"""Read-only area entities for Tecom Discovery."""

from __future__ import annotations

import asyncio
import hmac

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
    CodeFormat,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.exceptions import HomeAssistantError

from .api import DiscoveryError
from .const import CONF_CONTROL_CODE
from .coordinator import DiscoveryCoordinator
from .entity import DiscoveryEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up panel areas."""

    coordinator: DiscoveryCoordinator = entry.runtime_data
    async_add_entities(
        DiscoveryArea(coordinator, item) for item in coordinator.data.areas
    )


class DiscoveryArea(DiscoveryEntity, AlarmControlPanelEntity):
    """A read-only Discovery alarm area."""

    @property
    def code_arm_required(self) -> bool:
        return bool(self.coordinator.entry.options.get(CONF_CONTROL_CODE))

    @property
    def code_format(self) -> CodeFormat | None:
        if self.coordinator.entry.options.get(CONF_CONTROL_CODE):
            return CodeFormat.NUMBER
        return None

    @property
    def supported_features(self) -> AlarmControlPanelEntityFeature:
        if not self.coordinator.entry.options.get(CONF_CONTROL_CODE):
            return AlarmControlPanelEntityFeature(0)
        return (
            AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_HOME
        )

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        state = self.discovery_state
        if state is None:
            return None
        value = state.state.lower()
        if "alarm" in value:
            return AlarmControlPanelState.TRIGGERED
        if any(word in value for word in ("disarm", "access", "unset", "normal")):
            return AlarmControlPanelState.DISARMED
        if "entry_delay" in value:
            return AlarmControlPanelState.PENDING
        if "exit_delay" in value:
            return AlarmControlPanelState.ARMING
        if any(word in value for word in ("partial", "stay", "perimeter")):
            return AlarmControlPanelState.ARMED_HOME
        if any(word in value for word in ("armed", "secure", "set")):
            return AlarmControlPanelState.ARMED_AWAY
        return None

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Fully arm this Discovery area."""

        await self._async_set_area_action(2, code)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Stay-arm this Discovery area."""

        await self._async_set_area_action(1, code)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Disarm this Discovery area."""

        await self._async_set_area_action(4, code)

    async def _async_set_area_action(
        self, action: int, code: str | None
    ) -> None:
        configured_code = self.coordinator.entry.options.get(CONF_CONTROL_CODE)
        if not configured_code:
            raise HomeAssistantError(
                "Configure a keypad code in Tecom Discovery options first"
            )
        if code is None or not hmac.compare_digest(str(code), str(configured_code)):
            raise HomeAssistantError("Invalid keypad code")
        try:
            await self.coordinator.api.async_set_area_action(self.number, action)
        except DiscoveryError as err:
            raise HomeAssistantError(str(err)) from err
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()
