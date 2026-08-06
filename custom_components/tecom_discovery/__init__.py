"""Tecom Discovery integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import entity_registry as er

from .api import DiscoveryApi
from .const import (
    CONF_INPUT_COUNT,
    DEFAULT_INPUT_COUNT,
    DOMAIN,
    INPUT_TYPE_SEALED,
    KIND_INPUT,
    PLATFORMS,
)
from .coordinator import DiscoveryCoordinator
from .entity import configured_input_type

type DiscoveryConfigEntry = ConfigEntry[DiscoveryCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: DiscoveryConfigEntry) -> bool:
    """Set up Tecom Discovery from a config entry."""

    api = DiscoveryApi(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_VERIFY_SSL, False),
    )
    coordinator = DiscoveryCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    _remove_legacy_input_binary_sensors(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DiscoveryConfigEntry) -> bool:
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload_entry(
    hass: HomeAssistant, entry: DiscoveryConfigEntry
) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _remove_legacy_input_binary_sensors(
    hass: HomeAssistant, entry: DiscoveryConfigEntry
) -> None:
    """Remove Beta 01/02 input entities that used Safe/Unsafe state labels."""

    registry = er.async_get(hass)
    options = {**entry.data, **entry.options}
    input_count = int(options.get(CONF_INPUT_COUNT, DEFAULT_INPUT_COUNT))
    for number in range(1, input_count + 1):
        unique_id = f"{entry.entry_id}_{KIND_INPUT}_{number}"
        entity_id = registry.async_get_entity_id("binary_sensor", DOMAIN, unique_id)
        if entity_id is not None:
            registry.async_remove(entity_id)
    for item in entry.runtime_data.data.inputs:
        unique_id = f"{entry.entry_id}_{KIND_INPUT}_{item.number}"
        legacy_motion_id = (
            f"{entry.entry_id}_{KIND_INPUT}_motion_{item.number}"
        )
        entity_id = registry.async_get_entity_id(
            "binary_sensor", DOMAIN, legacy_motion_id
        )
        if entity_id is not None:
            registry.async_remove(entity_id)

        if configured_input_type(entry.runtime_data, item) == INPUT_TYPE_SEALED:
            binary_unique_id = (
                f"{entry.entry_id}_{KIND_INPUT}_binary_{item.number}"
            )
            entity_id = registry.async_get_entity_id(
                "binary_sensor", DOMAIN, binary_unique_id
            )
        else:
            entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
        if entity_id is not None:
            registry.async_remove(entity_id)
