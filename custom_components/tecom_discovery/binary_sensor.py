"""Relay and movement entities for Tecom Discovery."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    INPUT_TYPE_DOOR,
    INPUT_TYPE_MOISTURE,
    INPUT_TYPE_MOTION,
    INPUT_TYPE_OCCUPANCY,
    INPUT_TYPE_SEALED,
    INPUT_TYPE_SMOKE,
    INPUT_TYPE_VIBRATION,
    INPUT_TYPE_WINDOW,
    KIND_INPUT,
    KIND_RELAY,
)
from .coordinator import DiscoveryCoordinator
from .entity import DiscoveryEntity, configured_input_type


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
        DiscoveryInputBinarySensor(coordinator, item)
        for item in coordinator.data.inputs
        if configured_input_type(coordinator, item) != INPUT_TYPE_SEALED
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


class DiscoveryInputBinarySensor(DiscoveryEntity, BinarySensorEntity):
    """A typed Discovery binary input."""

    def __init__(self, coordinator: DiscoveryCoordinator, entity) -> None:
        super().__init__(coordinator, entity)
        self._attr_unique_id = (
            f"{coordinator.entry.entry_id}_{KIND_INPUT}_binary_{entity.number}"
        )

    @property
    def device_class(self) -> BinarySensorDeviceClass:
        state = self.discovery_state
        input_type = (
            configured_input_type(self.coordinator, state)
            if state is not None
            else INPUT_TYPE_MOTION
        )
        return {
            INPUT_TYPE_MOTION: BinarySensorDeviceClass.MOTION,
            INPUT_TYPE_DOOR: BinarySensorDeviceClass.DOOR,
            INPUT_TYPE_WINDOW: BinarySensorDeviceClass.WINDOW,
            INPUT_TYPE_OCCUPANCY: BinarySensorDeviceClass.OCCUPANCY,
            INPUT_TYPE_SMOKE: BinarySensorDeviceClass.SMOKE,
            INPUT_TYPE_MOISTURE: BinarySensorDeviceClass.MOISTURE,
            INPUT_TYPE_VIBRATION: BinarySensorDeviceClass.VIBRATION,
        }.get(input_type, BinarySensorDeviceClass.SAFETY)

    @property
    def is_on(self) -> bool | None:
        state = self.discovery_state
        return state.active if state else None
