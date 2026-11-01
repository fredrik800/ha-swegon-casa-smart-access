"""Sensor platform for Swegon Casa."""

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import SwegonCasaClient
from .const import (
    DOMAIN,
    ID_HUMIDITY_GM3,
    ID_SET_MODE,
    MODE_MAPPINGS,
    SENSOR_CONFIG,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Swegon Casa sensor platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: SwegonCasaClient = data["client"]

    sensors = []
    for sensor_id, config in SENSOR_CONFIG.items():
        sensors.append(
            SwegonCasaSensor(
                client,
                hass,
                sensor_id,
                config,
                entry.entry_id,
            )
        )

    async_add_entities(sensors)


class SwegonCasaSensor(SensorEntity):
    """Swegon Casa sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        client: SwegonCasaClient,
        hass: HomeAssistant,
        sensor_id: str,
        config: dict[str, Any],
        entry_id: str,
    ) -> None:
        """Initialize the sensor entity."""
        self.client = client
        self.hass = hass
        self.sensor_id = sensor_id
        self._attr_name = config["name"]
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{sensor_id}"
        self._attr_native_value = None

        if config["device_class"]:
            self._attr_device_class = config["device_class"]

        if config["unit_of_measurement"]:
            self._attr_native_unit_of_measurement = config["unit_of_measurement"]

        if config["state_class"]:
            self._attr_state_class = config["state_class"]

        if "icon" in config:
            self._attr_icon = config["icon"]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_data_updated_{self.client.host.replace('.', '_')}",
                self._handle_data_update,
            )
        )

    @callback
    def _handle_data_update(self, event: Any) -> None:
        """Handle data update from device."""
        data = event.data.get("data", {})

        if self.sensor_id in data:
            value = data[self.sensor_id]

            if self.sensor_id == ID_HUMIDITY_GM3:
                value = round(float(value) / 10, 2)

            if self.sensor_id == ID_SET_MODE:
                value = MODE_MAPPINGS.get(str(value), f"Unknown({value})")

            self._attr_native_value = value
            self.async_write_ha_state()
