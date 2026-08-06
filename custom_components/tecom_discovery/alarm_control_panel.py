"""Read-only area entities for Tecom Discovery."""

from __future__ import annotations

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

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

    _attr_supported_features = 0
    _attr_code_arm_required = False

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        state = self.discovery_state
        if state is None:
            return None
        value = state.state.lower()
        if "alarm" in value:
            return AlarmControlPanelState.TRIGGERED
        if any(word in value for word in ("partial", "stay", "perimeter")):
            return AlarmControlPanelState.ARMED_HOME
        if any(word in value for word in ("armed", "secure", "set")):
            return AlarmControlPanelState.ARMED_AWAY
        if "entry_delay" in value:
            return AlarmControlPanelState.PENDING
        if "exit_delay" in value:
            return AlarmControlPanelState.ARMING
        if any(word in value for word in ("disarm", "access", "unset", "normal")):
            return AlarmControlPanelState.DISARMED
        return None
