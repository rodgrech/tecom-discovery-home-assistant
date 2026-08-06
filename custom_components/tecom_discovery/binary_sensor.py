"""Relay and movement entities for Tecom Discovery."""

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
from .entity import DiscoveryEntity, is_motion_input


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up relays and inputs identified as movement detectors."""

    coordinator: DiscoveryCoordinator = entry.runtime_data
    entities = [
        DiscoveryBinarySensor(coordinator, item)
        for item in coordinator.data.relays
    ]
    entities.extend(
        DiscoveryMotionSensor(coordinator, item)
        for item in coordinator.data.inputs
        if is_motion_input(item)
    )
    async_add_entities(entities)


class DiscoveryBinarySensor(DiscoveryEntity, BinarySensorEntity):
    """A read-only Discovery relay."""

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        if self.kind == KIND_RELAY:
            return BinarySensorDeviceClass.POWER
        return None

    @property
    def is_on(self) -> bool | None:
        state = self.discovery_state
        return state.active if state else None


class DiscoveryMotionSensor(DiscoveryEntity, BinarySensorEntity):
    """A Discovery PIR or movement input."""

    _attr_device_class = BinarySensorDeviceClass.MOTION

    def __init__(self, coordinator: DiscoveryCoordinator, entity) -> None:
        super().__init__(coordinator, entity)
        self._attr_unique_id = (
            f"{coordinator.entry.entry_id}_{KIND_INPUT}_motion_{entity.number}"
        )

    @property
    def is_on(self) -> bool | None:
        state = self.discovery_state
        return state.active if state else None
