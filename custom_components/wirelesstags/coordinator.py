"""Data update coordinator for Wireless Tags."""

from __future__ import annotations

import logging
from datetime import timedelta

from requests.exceptions import ConnectTimeout, HTTPError
from wirelesstagpy import SensorTag, WirelessTags
from wirelesstagpy.binaryevent import BinaryEvent
from wirelesstagpy.exceptions import (
    WirelessTagsException,
    WirelessTagsWrongCredentials,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ARM_KEY_OVERRIDES,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SIGNAL_BINARY_EVENT_UPDATE,
    SIGNAL_TAG_UPDATE,
)

_LOGGER = logging.getLogger(__name__)

type WirelessTagsConfigEntry = ConfigEntry[WirelessTagsCoordinator]


class WirelessTagsCoordinator(DataUpdateCoordinator[dict[str, SensorTag]]):
    """Coordinator that polls tags and forwards cloud push updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        scan_seconds = entry.options.get(
            CONF_SCAN_INTERVAL, int(DEFAULT_SCAN_INTERVAL.total_seconds())
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=scan_seconds),
        )
        self.entry = entry
        self.api = WirelessTags(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
        )
        self._monitoring = False

    @property
    def tags(self) -> dict[str, SensorTag]:
        """Return the latest known tags."""
        return self.data or {}

    async def _async_update_data(self) -> dict[str, SensorTag]:
        """Fetch tags from wirelesstag.net."""
        try:
            return await self.hass.async_add_executor_job(self.api.load_tags)
        except WirelessTagsWrongCredentials as err:
            raise ConfigEntryAuthFailed("Invalid Wireless Tags credentials") from err
        except (ConnectTimeout, HTTPError, WirelessTagsException, OSError) as err:
            raise UpdateFailed(
                f"Error communicating with Wireless Tags API: {err}"
            ) from err

    async def async_start_monitoring(self) -> None:
        """Start cloud push monitoring in a background thread."""
        if self._monitoring:
            return

        def push_callback(
            tags_spec: dict[str, SensorTag],
            event_spec: dict[str, list[BinaryEvent]],
        ) -> None:
            """Handle push update from the cloud."""
            _LOGGER.debug(
                "Push notification arrived: %s, events: %s", tags_spec, event_spec
            )
            # Update coordinator data synchronously first so dispatcher
            # listeners reading `.tags` see the fresh values immediately.
            if tags_spec:
                merged = dict(self.data or {})
                merged.update(tags_spec)
                self.data = merged
                self.hass.add_job(self.async_set_updated_data, merged)

            for uuid, tag in tags_spec.items():
                try:
                    tag_id = tag.tag_id
                    mac = tag.tag_manager_mac
                    dispatcher_send(
                        self.hass, SIGNAL_TAG_UPDATE.format(tag_id, mac), tag
                    )
                    if uuid in event_spec:
                        for event in event_spec[uuid]:
                            dispatcher_send(
                                self.hass,
                                SIGNAL_BINARY_EVENT_UPDATE.format(
                                    tag_id, event.type, mac
                                ),
                                tag,
                            )
                except Exception:  # noqa: BLE001
                    _LOGGER.exception("Unable to handle tag push update: %s", tag)

        @callback
        def _stop_monitoring(_event: Event) -> None:
            self.stop_monitoring()

        await self.hass.async_add_executor_job(
            self.api.start_monitoring, push_callback
        )
        self._monitoring = True
        self.entry.async_on_unload(
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _stop_monitoring)
        )

    def stop_monitoring(self) -> None:
        """Stop cloud push monitoring."""
        if not self._monitoring:
            return
        try:
            self.api.stop_monitoring()
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Error while stopping Wireless Tags monitoring", exc_info=True)
        self._monitoring = False

    def arm(self, tag_id: int, tag_manager_mac: str | None, sensor_key: str) -> None:
        """Arm monitoring for a sensor type."""
        key = ARM_KEY_OVERRIDES.get(sensor_key, sensor_key)
        getattr(self.api, f"arm_{key}")(tag_id, tag_manager_mac)

    def disarm(self, tag_id: int, tag_manager_mac: str | None, sensor_key: str) -> None:
        """Disarm monitoring for a sensor type."""
        key = ARM_KEY_OVERRIDES.get(sensor_key, sensor_key)
        getattr(self.api, f"disarm_{key}")(tag_id, tag_manager_mac)
