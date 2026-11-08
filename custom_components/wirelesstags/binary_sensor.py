"""Binary sensor platform for Wireless Tags."""

from __future__ import annotations

from wirelesstagpy import SensorTag
from wirelesstagpy import constants as WT_CONSTANTS

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SIGNAL_BINARY_EVENT_UPDATE
from .coordinator import WirelessTagsConfigEntry, WirelessTagsCoordinator
from .entity import WirelessTagEntity

BINARY_SENSOR_TYPES: dict[str, BinarySensorEntityDescription] = {
    WT_CONSTANTS.EVENT_PRESENCE: BinarySensorEntityDescription(
        key=WT_CONSTANTS.EVENT_PRESENCE,
        device_class=BinarySensorDeviceClass.PRESENCE,
        translation_key="presence",
    ),
    WT_CONSTANTS.EVENT_MOTION: BinarySensorEntityDescription(
        key=WT_CONSTANTS.EVENT_MOTION,
        device_class=BinarySensorDeviceClass.MOTION,
        translation_key="motion",
    ),
    WT_CONSTANTS.EVENT_DOOR: BinarySensorEntityDescription(
        key=WT_CONSTANTS.EVENT_DOOR,
        device_class=BinarySensorDeviceClass.DOOR,
        translation_key="door",
    ),
    WT_CONSTANTS.EVENT_COLD: BinarySensorEntityDescription(
        key=WT_CONSTANTS.EVENT_COLD,
        device_class=BinarySensorDeviceClass.COLD,
        translation_key="cold",
    ),
    WT_CONSTANTS.EVENT_HEAT: BinarySensorEntityDescription(
        key=WT_CONSTANTS.EVENT_HEAT,
        device_class=BinarySensorDeviceClass.HEAT,
        translation_key="heat",
    ),
    WT_CONSTANTS.EVENT_DRY: BinarySensorEntityDescription(
        key=WT_CONSTANTS.EVENT_DRY,
        translation_key="dry",
    ),
    WT_CONSTANTS.EVENT_WET: BinarySensorEntityDescription(
        key=WT_CONSTANTS.EVENT_WET,
        translation_key="wet",
    ),
    WT_CONSTANTS.EVENT_LIGHT: BinarySensorEntityDescription(
        key=WT_CONSTANTS.EVENT_LIGHT,
        device_class=BinarySensorDeviceClass.LIGHT,
        translation_key="light_detected",
    ),
    WT_CONSTANTS.EVENT_MOISTURE: BinarySensorEntityDescription(
        key=WT_CONSTANTS.EVENT_MOISTURE,
        device_class=BinarySensorDeviceClass.MOISTURE,
        translation_key="leak",
    ),
    WT_CONSTANTS.EVENT_BATTERY: BinarySensorEntityDescription(
        key=WT_CONSTANTS.EVENT_BATTERY,
        device_class=BinarySensorDeviceClass.BATTERY,
        translation_key="battery",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WirelessTagsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Wireless Tags binary sensors from a config entry."""
    coordinator = entry.runtime_data
    entities: list[WirelessTagBinarySensor] = []

    for tag in coordinator.tags.values():
        for event_type in tag.supported_binary_events_types:
            description = BINARY_SENSOR_TYPES.get(event_type)
            if description is None:
                continue
            entities.append(WirelessTagBinarySensor(coordinator, tag, description))

    async_add_entities(entities)


class WirelessTagBinarySensor(WirelessTagEntity, BinarySensorEntity):
    """Representation of a Wireless Tag binary event."""

    entity_description: BinarySensorEntityDescription

    def __init__(
        self,
        coordinator: WirelessTagsCoordinator,
        tag: SensorTag,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, tag, description.key)
        self.entity_description = description

    @property
    def event(self):
        """Return the binary event object."""
        tag = self.tag
        if tag is None:
            return None
        return tag.event[self.entity_description.key]

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is on."""
        event = self.event
        if event is None:
            return None
        return bool(event.is_state_on)

    async def async_added_to_hass(self) -> None:
        """Register push callbacks."""
        await super().async_added_to_hass()
        if self.tag_id is None:
            return
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_BINARY_EVENT_UPDATE.format(
                    self.tag_id, self.entity_description.key, self.tag_manager_mac
                ),
                self._handle_binary_event,
            )
        )

    @callback
    def _handle_binary_event(self, new_tag: SensorTag) -> None:
        """Handle a binary event push update."""
        self.async_write_ha_state()
