"""Tests for firmware response normalization."""

from custom_components.tecom_discovery.api import normalize_states


def test_normalize_enveloped_inputs() -> None:
    response = {
        "success": True,
        "data": [
            {"inputNumber": 1, "inputName": "Front Door", "status": "Unsealed"},
            {"inputNumber": 2, "inputName": "Hall PIR", "status": "Sealed"},
        ],
    }
    states = normalize_states(response, "input", [1, 2])
    assert states[0].name == "Front Door"
    assert states[0].active is True
    assert states[1].active is False


def test_normalize_number_map_and_missing_entity() -> None:
    response = {"data": {"1": {"state": False, "name": "Relay 1"}}}
    states = normalize_states(response, "relay", [1, 2])
    assert states[0].active is False
    assert states[1].state == "unknown"


def test_normalize_area_alarm() -> None:
    response = {
        "data": {
            "areas": [
                {
                    "entityNumber": 1,
                    "name": "House",
                    "alarmsActive": True,
                    "areaSecured": True,
                    "responseStatus": True,
                }
            ]
        }
    }
    state = normalize_states(response, "area", [1])[0]
    assert state.active is True
    assert state.state == "alarm"


def test_real_discovery_input_uses_alarm_status() -> None:
    response = {
        "data": [
            {
                "entityNumber": 1,
                "alarmStatus": "Sealed",
                "state": "Open",
                "responseStatus": True,
                "entityName": "Test PIR",
            }
        ]
    }
    state = normalize_states(response, "input", [1])[0]
    assert state.state == "sealed"
    assert state.active is False


def test_real_discovery_area_disarmed() -> None:
    response = {
        "data": [
            {
                "entityNumber": 1,
                "alarmsActive": False,
                "areaSecured": False,
                "areaStay": False,
                "responseStatus": True,
            }
        ]
    }
    state = normalize_states(response, "area", [1])[0]
    assert state.state == "disarmed"
    assert state.active is False
