"""Sensor platform for Wireless Tags."""

from __future__ import annotations

from wirelesstagpy import SensorTag

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SIGNAL_TAG_UPDATE
from .coordinator import WirelessTagsConfigEntry, WirelessTagsCoordinator
from .entity import WirelessTagEntity

SENSOR_TYPES: dict[str, SensorEntityDescription] = {
    "temperature": SensorEntityDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="temperature",
    ),
    "ambient_temperature": SensorEntityDescription(
        key="ambient_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="ambient_temperature",
    ),
    "humidity": SensorEntityDescription(
        key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="humidity",
    ),
    "moisture": SensorEntityDescription(
        key="moisture",
        device_class=SensorDeviceClass.MOISTURE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="moisture",
    ),
    "light": SensorEntityDescription(
        key="light",
        device_class=SensorDeviceClass.ILLUMINANCE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="light",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WirelessTagsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Wireless Tags sensors from a config entry."""
    coordinator = entry.runtime_data
    entities: list[WirelessTagSensor] = []

    for tag in coordinator.tags.values():
        for key in tag.allowed_sensor_types:
            description = SENSOR_TYPES.get(key)
            if description is None:
                continue
            entities.append(WirelessTagSensor(coordinator, tag, description))

    async_add_entities(entities)


class WirelessTagSensor(WirelessTagEntity, SensorEntity):
    """Representation of a Wireless Tag metric sensor."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator: WirelessTagsCoordinator,
        tag: SensorTag,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, tag, description.key)
        self.entity_description = description

    @property
    def _sensor(self):
        """Return the underlying wirelesstagpy sensor object."""
        tag = self.tag
        if tag is None:
            return None
        return tag.sensor[self.entity_description.key]

    @property
    def native_value(self):
        """Return the sensor value."""
        sensor = self._sensor
        if sensor is None:
            return None
        value = sensor.value
        try:
            return round(float(value), 1)
        except (TypeError, ValueError):
            return value

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        sensor = self._sensor
        return None if sensor is None else sensor.unit

    async def async_added_to_hass(self) -> None:
        """Register push callbacks."""
        await super().async_added_to_hass()
        if self.tag_id is None:
            return
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_TAG_UPDATE.format(self.tag_id, self.tag_manager_mac),
                self._handle_push_update,
            )
        )

    @callback
    def _handle_push_update(self, new_tag: SensorTag) -> None:
        """Handle a tag push update."""
        self.async_write_ha_state()
