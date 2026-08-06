"""Base entity for Tecom Discovery."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DiscoveryCoordinator
from .models import DiscoveryEntityState


class DiscoveryEntity(CoordinatorEntity[DiscoveryCoordinator]):
    """Base coordinator entity."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: DiscoveryCoordinator, entity: DiscoveryEntityState
    ) -> None:
        super().__init__(coordinator)
        self.kind = entity.kind
        self.number = entity.number
        self._attr_unique_id = (
            f"{coordinator.entry.entry_id}_{entity.kind}_{entity.number}"
        )
        self._attr_name = entity.name

    @property
    def discovery_state(self) -> DiscoveryEntityState | None:
        """Return this entity from the latest coordinator data."""

        collection = getattr(self.coordinator.data, f"{self.kind}s", [])
        return next((item for item in collection if item.number == self.number), None)

    @property
    def available(self) -> bool:
        state = self.discovery_state
        return super().available and state is not None and state.state != "unknown"

    @property
    def extra_state_attributes(self):
        state = self.discovery_state
        if state is None:
            return None
        return {"number": state.number, "panel_state": state.state, **state.raw}

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
