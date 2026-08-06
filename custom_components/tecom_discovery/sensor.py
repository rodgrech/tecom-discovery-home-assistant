"""Panel diagnostic entities for Tecom Discovery."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DiscoveryCoordinator
from .entity import DiscoveryEntity, is_motion_input


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up panel information sensor."""

    coordinator: DiscoveryCoordinator = entry.runtime_data
    async_add_entities(
        [
            DiscoveryPanelInfoSensor(coordinator),
            *(
                DiscoveryInputSensor(coordinator, item)
                for item in coordinator.data.inputs
                if not is_motion_input(item)
            ),
        ]
    )


class DiscoveryInputSensor(DiscoveryEntity, SensorEntity):
    """A Discovery input with the panel's Sealed/Unsealed terminology."""

    _attr_icon = "mdi:shield-check"

    @property
    def native_value(self) -> str | None:
        state = self.discovery_state
        if state is None or state.state == "unknown":
            return None
        return state.state.replace("_", " ").title()

    @property
    def icon(self) -> str:
        state = self.discovery_state
        if state and state.state == "unsealed":
            return "mdi:shield-alert"
        return "mdi:shield-check"


class DiscoveryPanelInfoSensor(CoordinatorEntity[DiscoveryCoordinator], SensorEntity):
    """Panel firmware and API information."""

    _attr_has_entity_name = True
    _attr_name = "Panel information"
    _attr_icon = "mdi:shield-home"

    def __init__(self, coordinator: DiscoveryCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_panel_info"

    @property
    def native_value(self) -> str:
        panel = self.coordinator.data.panel
        return str(panel.get("firmware") or panel.get("appVersion") or "connected")

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.panel

    @property
    def device_info(self) -> DeviceInfo:
        panel = self.coordinator.data.panel
        board = str(panel.get("board") or self.coordinator.entry.entry_id)
        return DeviceInfo(
            identifiers={(DOMAIN, board)},
            manufacturer="Aritech / Tecom",
            model="Discovery",
            name=f"Tecom Discovery {board}",
            sw_version=str(panel.get("firmware") or panel.get("appVersion") or ""),
            configuration_url=self.coordinator.api.base_url.removesuffix("/api"),
        )
