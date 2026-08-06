"""Tecom Discovery integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DiscoveryApi
from .const import PLATFORMS
from .coordinator import DiscoveryCoordinator

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
