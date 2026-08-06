"""Constants for the Tecom Discovery integration."""

from datetime import timedelta

DOMAIN = "tecom_discovery"
PLATFORMS = ["alarm_control_panel", "binary_sensor", "sensor"]

CONF_INPUT_COUNT = "input_count"
CONF_AREA_COUNT = "area_count"
CONF_RELAY_COUNT = "relay_count"
CONF_INPUT_MAPPINGS = "input_mappings"
CONF_INPUT_TYPE = "input_type"
CONF_INPUT_AREA = "input_area"
CONF_CONTROL_CODE = "control_code"

DEFAULT_INPUT_COUNT = 16
DEFAULT_AREA_COUNT = 8
DEFAULT_RELAY_COUNT = 4
DEFAULT_SCAN_INTERVAL = timedelta(seconds=10)

KIND_INPUT = "input"
KIND_AREA = "area"
KIND_RELAY = "relay"

INPUT_TYPE_SEALED = "sealed"
INPUT_TYPE_MOTION = "motion"
INPUT_TYPE_DOOR = "door"
INPUT_TYPE_WINDOW = "window"
INPUT_TYPE_OCCUPANCY = "occupancy"
INPUT_TYPE_SMOKE = "smoke"
INPUT_TYPE_MOISTURE = "moisture"
INPUT_TYPE_VIBRATION = "vibration"
INPUT_TYPES = (
    INPUT_TYPE_SEALED,
    INPUT_TYPE_MOTION,
    INPUT_TYPE_DOOR,
    INPUT_TYPE_WINDOW,
    INPUT_TYPE_OCCUPANCY,
    INPUT_TYPE_SMOKE,
    INPUT_TYPE_MOISTURE,
    INPUT_TYPE_VIBRATION,
)
