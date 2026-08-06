"""Constants for the Tecom Discovery integration."""

from datetime import timedelta

DOMAIN = "tecom_discovery"
PLATFORMS = ["alarm_control_panel", "binary_sensor", "sensor"]

CONF_INPUT_COUNT = "input_count"
CONF_AREA_COUNT = "area_count"
CONF_RELAY_COUNT = "relay_count"

DEFAULT_INPUT_COUNT = 16
DEFAULT_AREA_COUNT = 8
DEFAULT_RELAY_COUNT = 4
DEFAULT_SCAN_INTERVAL = timedelta(seconds=10)

KIND_INPUT = "input"
KIND_AREA = "area"
KIND_RELAY = "relay"

