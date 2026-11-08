"""Switch platform for Wireless Tags arm/disarm controls."""

from __future__ import annotations

from typing import Any

from wirelesstagpy import SensorTag

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import WirelessTagsConfigEntry, WirelessTagsCoordinator
from .entity import WirelessTagEntity

SWITCH_TYPES: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="temperature",
        translation_key="arm_temperature",
    ),
    SwitchEntityDescription(
        key="humidity",
        translation_key="arm_humidity",
    ),
    SwitchEntityDescription(
        key="motion",
        translation_key="arm_motion",
    ),
    SwitchEntityDescription(
        key="light",
        translation_key="arm_light",
    ),
    SwitchEntityDescription(
        key="moisture",
        translation_key="arm_moisture",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WirelessTagsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Wireless Tags switches from a config entry."""
    coordinator = entry.runtime_data
    entities: list[WirelessTagSwitch] = []

    for tag in coordinator.tags.values():
        for description in SWITCH_TYPES:
            if description.key not in tag.allowed_monitoring_types:
                continue
            entities.append(WirelessTagSwitch(coordinator, tag, description))

    async_add_entities(entities)


class WirelessTagSwitch(WirelessTagEntity, SwitchEntity):
    """Switch that arms or disarms monitoring for a sensor type."""

    entity_description: SwitchEntityDescription

    def __init__(
        self,
        coordinator: WirelessTagsCoordinator,
        tag: SensorTag,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, tag, f"arm_{description.key}")
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return True if monitoring is armed."""
        tag = self.tag
        if tag is None:
            return None
        attr_name = f"is_{self.entity_description.key}_sensor_armed"
        return bool(getattr(tag, attr_name, False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Arm monitoring."""
        if self.tag_id is None:
            return
        await self.hass.async_add_executor_job(
            self.coordinator.arm,
            self.tag_id,
            self.tag_manager_mac,
            self.entity_description.key,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disarm monitoring."""
        if self.tag_id is None:
            return
        await self.hass.async_add_executor_job(
            self.coordinator.disarm,
            self.tag_id,
            self.tag_manager_mac,
            self.entity_description.key,
        )
        await self.coordinator.async_request_refresh()
