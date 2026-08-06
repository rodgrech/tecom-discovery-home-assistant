"""Regression tests for area state matching."""


def map_alarm_state(value: str) -> str | None:
    """Mirror the entity's ordered string mapping without Home Assistant imports."""

    value = value.lower()
    if "alarm" in value:
        return "triggered"
    if any(word in value for word in ("disarm", "access", "unset", "normal")):
        return "disarmed"
    if "entry_delay" in value:
        return "pending"
    if "exit_delay" in value:
        return "arming"
    if any(word in value for word in ("partial", "stay", "perimeter")):
        return "armed_home"
    if any(word in value for word in ("armed", "secure", "set")):
        return "armed_away"
    return None


def test_disarmed_does_not_match_armed() -> None:
    assert map_alarm_state("disarmed") == "disarmed"


def test_armed_away_still_matches() -> None:
    assert map_alarm_state("armed_away") == "armed_away"
