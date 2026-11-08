"""The Wireless Tags custom integration."""

from __future__ import annotations

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import PLATFORMS
from .coordinator import WirelessTagsConfigEntry, WirelessTagsCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: WirelessTagsConfigEntry) -> bool:
    """Set up Wireless Tags from a config entry."""
    if CONF_USERNAME not in entry.data or CONF_PASSWORD not in entry.data:
        raise ConfigEntryAuthFailed("Missing Wireless Tags credentials")

    coordinator = WirelessTagsCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await coordinator.async_start_monitoring()

    await hass.config_entries.async_forward_entry_setups(
        entry, [Platform(p) for p in PLATFORMS]
    )
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WirelessTagsConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [Platform(p) for p in PLATFORMS]
    )
    if unload_ok:
        entry.runtime_data.stop_monitoring()
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: WirelessTagsConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
