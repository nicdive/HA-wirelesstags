"""Base entity for Wireless Tags."""

from __future__ import annotations

from typing import Any

from wirelesstagpy import SensorTag

from homeassistant.const import (
    ATTR_BATTERY_LEVEL,
    ATTR_VOLTAGE,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricPotential,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WirelessTagsCoordinator

ATTR_TAG_SIGNAL_STRENGTH = "signal_strength"
ATTR_TAG_OUT_OF_RANGE = "out_of_range"
ATTR_TAG_POWER_CONSUMPTION = "power_consumption"


class WirelessTagEntity(CoordinatorEntity[WirelessTagsCoordinator]):
    """Base entity tied to a Wireless Tag device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WirelessTagsCoordinator,
        tag: SensorTag,
        key: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._uuid = tag.uuid
        self._key = key
        self._attr_unique_id = f"{tag.uuid}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, tag.uuid)},
            name=tag.name,
            manufacturer="Cao Gadgets LLC",
            model=f"Wireless Tag (type {tag.tag_type})",
            sw_version=str(getattr(tag, "sw_version", "") or ""),
            hw_version=str(getattr(tag, "hw_revision", "") or ""),
        )

    @property
    def tag(self) -> SensorTag | None:
        """Return the latest tag data."""
        return self.coordinator.tags.get(self._uuid)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        tag = self.tag
        return super().available and tag is not None and bool(tag.is_alive)

    @property
    def tag_id(self) -> int | None:
        """Return the tag id."""
        tag = self.tag
        return None if tag is None else tag.tag_id

    @property
    def tag_manager_mac(self) -> str | None:
        """Return the tag manager MAC address."""
        tag = self.tag
        return None if tag is None else tag.tag_manager_mac

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return common tag attributes."""
        tag = self.tag
        if tag is None:
            return {}
        return {
            ATTR_BATTERY_LEVEL: int(tag.battery_remaining * 100),
            ATTR_VOLTAGE: f"{tag.battery_volts:.2f}{UnitOfElectricPotential.VOLT}",
            ATTR_TAG_SIGNAL_STRENGTH: (
                f"{tag.signal_strength}{SIGNAL_STRENGTH_DECIBELS_MILLIWATT}"
            ),
            ATTR_TAG_OUT_OF_RANGE: not tag.is_in_range,
            ATTR_TAG_POWER_CONSUMPTION: f"{tag.power_consumption:.2f}{PERCENTAGE}",
        }
