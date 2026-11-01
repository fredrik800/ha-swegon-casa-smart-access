"""The Swegon Casa integration."""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import SwegonCasaClient
from .const import DOMAIN

_LOGGER: logging.Logger = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.NUMBER, Platform.SELECT, Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Swegon Casa from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    session = async_get_clientsession(hass)
    client = SwegonCasaClient(host, username, password)
    client.set_session(session)

    try:
        if not await client.login():
            _LOGGER.error("Failed to login to Swegon Casa")
            return False
    except Exception as err:
        _LOGGER.error("Error during login: %s", err)
        return False

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def async_fetch_data() -> None:
        """Fetch data from device periodically."""
        while True:
            try:
                data = await client.fetch_data()
                if data:
                    hass.bus.async_fire(
                        f"{DOMAIN}_data_updated_{host.replace('.', '_')}",
                        {"data": data},
                    )
            except Exception as err:
                _LOGGER.error("Error fetching data: %s", err)

            await asyncio.sleep(30)

    hass.create_task(async_fetch_data())

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return bool(unload_ok)
