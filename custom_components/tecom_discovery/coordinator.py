"""Data coordinator for Tecom Discovery."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DiscoveryApi, DiscoveryError
from .const import (
    CONF_AREA_COUNT,
    CONF_INPUT_COUNT,
    CONF_RELAY_COUNT,
    DEFAULT_AREA_COUNT,
    DEFAULT_INPUT_COUNT,
    DEFAULT_RELAY_COUNT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    KIND_AREA,
    KIND_INPUT,
    KIND_RELAY,
)
from .models import DiscoveryData

_LOGGER = logging.getLogger(__name__)


class DiscoveryCoordinator(DataUpdateCoordinator[DiscoveryData]):
    """Poll state from the panel."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: DiscoveryApi
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            config_entry=entry,
        )
        self.api = api
        self.entry = entry

    async def _async_update_data(self) -> DiscoveryData:
        options = {**self.entry.data, **self.entry.options}
        try:
            panel, inputs, areas, relays = await asyncio.gather(
                self.api.async_panel_info(),
                self.api.async_recall_states(
                    KIND_INPUT,
                    int(options.get(CONF_INPUT_COUNT, DEFAULT_INPUT_COUNT)),
                ),
                self.api.async_recall_states(
                    KIND_AREA,
                    int(options.get(CONF_AREA_COUNT, DEFAULT_AREA_COUNT)),
                ),
                self.api.async_recall_states(
                    KIND_RELAY,
                    int(options.get(CONF_RELAY_COUNT, DEFAULT_RELAY_COUNT)),
                ),
            )
        except DiscoveryError as err:
            raise UpdateFailed(str(err)) from err
        return DiscoveryData(panel=panel, inputs=inputs, areas=areas, relays=relays)

