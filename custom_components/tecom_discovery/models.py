"""Data models for Tecom Discovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DiscoveryEntityState:
    """A normalized panel entity."""

    number: int
    name: str
    kind: str
    state: str
    active: bool | None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DiscoveryData:
    """All data collected during one coordinator refresh."""

    panel: dict[str, Any]
    inputs: list[DiscoveryEntityState]
    areas: list[DiscoveryEntityState]
    relays: list[DiscoveryEntityState]

