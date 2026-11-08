"""Config flow for Wireless Tags."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from requests.exceptions import ConnectTimeout, HTTPError
from wirelesstagpy import WirelessTags
from wirelesstagpy.exceptions import (
    WirelessTagsConnectionError,
    WirelessTagsException,
    WirelessTagsWrongCredentials,
)

from homeassistant import config_entries
from homeassistant.config_entries import OptionsFlow
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, MIN_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def _validate_credentials(
    hass, username: str, password: str
) -> dict[str, str] | None:
    """Validate credentials against the Wireless Tags cloud."""

    def _login() -> int:
        api = WirelessTags(username=username, password=password)
        tags = api.load_tags()
        return len(tags)

    try:
        await hass.async_add_executor_job(_login)
    except WirelessTagsWrongCredentials:
        return {"base": "invalid_auth"}
    except (WirelessTagsConnectionError, ConnectTimeout, HTTPError, OSError):
        return {"base": "cannot_connect"}
    except WirelessTagsException:
        return {"base": "cannot_connect"}
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Unexpected error validating Wireless Tags credentials")
        return {"base": "unknown"}
    return None


class WirelessTagsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wireless Tags."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
            self._abort_if_unique_id_configured()

            errors = (
                await _validate_credentials(
                    self.hass,
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
                or {}
            )
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                    options={
                        CONF_SCAN_INTERVAL: int(
                            DEFAULT_SCAN_INTERVAL.total_seconds()
                        )
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle reauthentication when credentials fail."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm reauthentication with a new password."""
        errors: dict[str, str] = {}
        reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        if reauth_entry is None:
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            username = reauth_entry.data[CONF_USERNAME]
            errors = (
                await _validate_credentials(
                    self.hass, username, user_input[CONF_PASSWORD]
                )
                or {}
            )
            if not errors:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data={
                        **reauth_entry.data,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={
                "username": reauth_entry.data[CONF_USERNAME],
            },
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> WirelessTagsOptionsFlow:
        """Create the options flow."""
        return WirelessTagsOptionsFlow()


class WirelessTagsOptionsFlow(OptionsFlow):
    """Handle options for Wireless Tags."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, int(DEFAULT_SCAN_INTERVAL.total_seconds())
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=3600,
                            step=30,
                            unit_of_measurement="seconds",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
