"""The Swegon Casa integration."""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import SwegonCasaClient
from .const import (
    CONF_AFTERHEATER_WATTS,
    DOMAIN,
    data_updated_event,
)
from .energy import SwegonCasaEnergyTracker

_LOGGER: logging.Logger = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR, Platform.NUMBER, Platform.SELECT,
    Platform.CLIMATE, Platform.BUTTON,
]


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload this unit when its IP or calibration changes."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Swegon Casa from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.options.get(CONF_HOST, entry.data[CONF_HOST])
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

    tracker = SwegonCasaEnergyTracker(
        hass, entry.entry_id, entry.options.get(CONF_AFTERHEATER_WATTS, 0)
    )
    await tracker.async_load()
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "energy_tracker": tracker,
    }
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def async_fetch_data() -> None:
        """Fetch data from device periodically."""
        while True:
            try:
                data = await client.fetch_data()
                if data is not None:
                    tracker.process_reading(data)
                    hass.bus.async_fire(
                        data_updated_event(entry.entry_id),
                        {"data": data},
                    )
            except Exception as err:
                _LOGGER.error("Error fetching data: %s", err)

            await asyncio.sleep(30)

    task = hass.async_create_task(async_fetch_data())
    hass.data[DOMAIN][entry.entry_id]["poll_task"] = task

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and stop polling for this unit."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        data = hass.data[DOMAIN].pop(entry.entry_id, {})
        task = data.get("poll_task")
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        tracker = data.get("energy_tracker")
        if tracker is not None:
            await tracker.async_save()
    return unloaded
