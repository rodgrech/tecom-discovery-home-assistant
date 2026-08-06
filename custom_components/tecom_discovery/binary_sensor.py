"""Input and relay entities for Tecom Discovery."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import KIND_INPUT, KIND_RELAY
from .coordinator import DiscoveryCoordinator
from .entity import DiscoveryEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up inputs and relays."""

    coordinator: DiscoveryCoordinator = entry.runtime_data
    entities = [
        DiscoveryBinarySensor(coordinator, item)
        for item in (*coordinator.data.inputs, *coordinator.data.relays)
    ]
    async_add_entities(entities)


class DiscoveryBinarySensor(DiscoveryEntity, BinarySensorEntity):
    """A read-only Discovery input or relay."""

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        if self.kind == KIND_INPUT:
            return BinarySensorDeviceClass.SAFETY
        if self.kind == KIND_RELAY:
            return BinarySensorDeviceClass.POWER
        return None

    @property
    def is_on(self) -> bool | None:
        state = self.discovery_state
        return state.active if state else None
