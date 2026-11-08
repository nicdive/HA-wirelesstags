"""Constants for the Wireless Tags integration."""

from datetime import timedelta

DOMAIN = "wirelesstags"

CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=2)
MIN_SCAN_INTERVAL = 30

# Template for signal - first parameter is tag_id,
# second, tag manager mac address
SIGNAL_TAG_UPDATE = f"{DOMAIN}.tag_info_updated_{{}}_{{}}"

# Template for signal - tag_id, sensor type and
# tag manager mac address
SIGNAL_BINARY_EVENT_UPDATE = f"{DOMAIN}.binary_event_updated_{{}}_{{}}_{{}}"

# wirelesstagpy exposes the capacitive sensor under the "humidity" arm/disarm
# endpoints (ArmCapSensor). Water tags report that same sensor as "moisture"
# and have no dedicated arm_moisture/disarm_moisture method.
ARM_KEY_OVERRIDES = {"moisture": "humidity"}

PLATFORMS = ["sensor", "binary_sensor", "switch"]
