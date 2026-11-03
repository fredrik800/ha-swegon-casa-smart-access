"""Sensor platform for Swegon Casa."""

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import SwegonCasaClient
from .const import (
    CONF_AFTERHEATER_WATTS,
    CONF_EXHAUST_MAX_RPM,
    CONF_SUPPLY_MAX_RPM,
    DOMAIN,
    ID_AFTERHEATER_PERCENT,
    ID_VENTILATION_LEVEL_IN,
    ID_VENTILATION_LEVEL_OUT,
    data_updated_event,
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

    sensors.extend([
        SwegonCasaCalculatedSensor(
            hass, entry.entry_id, "afterheater_watts", "FTX Beräknad eftervärme",
            ID_AFTERHEATER_PERCENT, entry.options.get(CONF_AFTERHEATER_WATTS, 0),
            "W", "mdi:radiator", SensorDeviceClass.POWER,
        ),
        SwegonCasaCalculatedSensor(
            hass, entry.entry_id, "supply_rpm_estimated", "FTX Beräknat tilluftsvarvtal",
            ID_VENTILATION_LEVEL_IN, entry.options.get(CONF_SUPPLY_MAX_RPM, 0),
            "RPM", "mdi:fan", None,
        ),
        SwegonCasaCalculatedSensor(
            hass, entry.entry_id, "exhaust_rpm_estimated", "FTX Beräknat frånluftsvarvtal",
            ID_VENTILATION_LEVEL_OUT, entry.options.get(CONF_EXHAUST_MAX_RPM, 0),
            "RPM", "mdi:fan", None,
        ),
    ])
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
        self.entry_id = entry_id
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
                data_updated_event(self.entry_id),
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


class SwegonCasaCalculatedSensor(SensorEntity):
    """Estimated power or fan RPM from a percentage and per-unit calibration."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, hass: HomeAssistant, entry_id: str, key: str, name: str,
        source_id: str, maximum: int, unit: str, icon: str,
        device_class: SensorDeviceClass | None,
    ) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.source_id = source_id
        self.maximum = int(maximum)
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{key}"
        self._attr_native_unit_of_measurement = (
            UnitOfPower.WATT if device_class == SensorDeviceClass.POWER else unit
        )
        self._attr_icon = icon
        if device_class:
            self._attr_device_class = device_class
        self._attr_native_value = None
        self._attr_available = self.maximum > 0

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self.hass.bus.async_listen(
                data_updated_event(self.entry_id), self._handle_data_update
            )
        )

    @callback
    def _handle_data_update(self, event: Any) -> None:
        """0% is zero; missing or invalid readings must not become false zeroes."""
        if self.maximum <= 0:
            return
        raw = event.data.get("data", {}).get(self.source_id)
        if raw is None:
            self._attr_available = False
            self._attr_native_value = None
        else:
            try:
                percent = float(raw)
                if not 0 <= percent <= 100:
                    raise ValueError("Percentage outside 0-100")
                calculated = percent * self.maximum / 100
                if self._attr_native_unit_of_measurement == "RPM":
                    # Estimated RPM rounded to the nearest 100, as on CASA panel.
                    self._attr_native_value = int((calculated + 50) // 100) * 100
                else:
                    self._attr_native_value = round(calculated)
                self._attr_available = True
            except (ValueError, TypeError):
                self._attr_available = False
                self._attr_native_value = None
        self.async_write_ha_state()
