"""Tests for input entity classification."""


def is_motion_name(name: str) -> bool:
    """Mirror the integration's name-based movement classification."""

    value = name.casefold()
    return any(term in value for term in ("pir", "motion", "movement"))


def test_pir_is_movement_sensor() -> None:
    assert is_motion_name("Test PIR")


def test_motion_is_movement_sensor() -> None:
    assert is_motion_name("Hallway Motion")


def test_door_remains_sealed_sensor() -> None:
    assert not is_motion_name("Front Door")
