"""Diagnostics support for Wireless Tags."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .coordinator import WirelessTagsConfigEntry

TO_REDACT = {CONF_PASSWORD, CONF_USERNAME, "uuid", "tag_manager_mac"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: WirelessTagsConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    tags = []
    for tag in coordinator.tags.values():
        tags.append(
            {
                "name": tag.name,
                "uuid": tag.uuid,
                "tag_id": tag.tag_id,
                "tag_type": tag.tag_type,
                "tag_manager_mac": tag.tag_manager_mac,
                "is_alive": tag.is_alive,
                "is_in_range": tag.is_in_range,
                "allowed_sensor_types": list(tag.allowed_sensor_types),
                "supported_binary_events_types": list(
                    tag.supported_binary_events_types
                ),
                "allowed_monitoring_types": list(tag.allowed_monitoring_types),
            }
        )

    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "tags": async_redact_data(tags, TO_REDACT),
    }
