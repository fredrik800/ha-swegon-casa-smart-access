"""Config flow for Swegon Casa integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import SwegonCasaClient
from .const import (
    CONF_AFTERHEATER_WATTS,
    CONF_EXHAUST_MAX_RPM,
    CONF_SUPPLY_MAX_RPM,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)


class SwegonCasaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Swegon Casa."""

    domain = DOMAIN
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Provide per-unit IP and calculation settings."""
        return SwegonCasaOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> Any:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                host = user_input[CONF_HOST]
                username = user_input[CONF_USERNAME]
                password = user_input[CONF_PASSWORD]

                session = async_get_clientsession(self.hass)
                client = SwegonCasaClient(host, username, password)
                client.set_session(session)

                if not await client.login():
                    errors["base"] = "invalid_auth"
                else:
                    await self.async_set_unique_id(host)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"Swegon Casa ({host})",
                        data={
                            CONF_HOST: host,
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                        },
                    )

            except Exception as err:
                _LOGGER.error("Error during login: %s", err)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


_NONNEGATIVE_INT = vol.All(vol.Coerce(int), vol.Range(min=0, max=20000))


class SwegonCasaOptionsFlow(config_entries.OptionsFlow):
    """Edit IP address and heater/fan calibration independently per unit."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> Any:
        entry = self.config_entry
        options = entry.options
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                host = user_input[CONF_HOST].strip()
                if not host:
                    errors["base"] = "invalid_host"
                elif any(
                    other.entry_id != entry.entry_id
                    and other.options.get(CONF_HOST, other.data.get(CONF_HOST)) == host
                    for other in self.hass.config_entries.async_entries(DOMAIN)
                ):
                    errors["base"] = "already_configured"
                else:
                    client = SwegonCasaClient(
                        host, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
                    )
                    client.set_session(async_get_clientsession(self.hass))
                    if not await client.login():
                        errors["base"] = "cannot_connect"
                    else:
                        return self.async_create_entry(
                            title="",
                            data={
                                CONF_HOST: host,
                                CONF_AFTERHEATER_WATTS: user_input[CONF_AFTERHEATER_WATTS],
                                CONF_SUPPLY_MAX_RPM: user_input[CONF_SUPPLY_MAX_RPM],
                                CONF_EXHAUST_MAX_RPM: user_input[CONF_EXHAUST_MAX_RPM],
                            },
                        )
            except Exception:
                _LOGGER.exception("Could not validate Swegon Casa options")
                errors["base"] = "cannot_connect"

        schema = vol.Schema({
            vol.Required(
                CONF_HOST, default=options.get(CONF_HOST, entry.data[CONF_HOST])
            ): str,
            vol.Required(
                CONF_AFTERHEATER_WATTS,
                default=options.get(CONF_AFTERHEATER_WATTS, 0),
            ): _NONNEGATIVE_INT,
            vol.Required(
                CONF_SUPPLY_MAX_RPM,
                default=options.get(CONF_SUPPLY_MAX_RPM, 0),
            ): _NONNEGATIVE_INT,
            vol.Required(
                CONF_EXHAUST_MAX_RPM,
                default=options.get(CONF_EXHAUST_MAX_RPM, 0),
            ): _NONNEGATIVE_INT,
        })
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
