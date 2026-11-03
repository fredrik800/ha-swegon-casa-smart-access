"""Constants for the Swegon Casa integration."""

from enum import StrEnum
from typing import Any

DOMAIN = "swegon_casa"

# Per-config-entry calibration; each unit has independent settings.
CONF_AFTERHEATER_WATTS = "afterheater_watts"
CONF_SUPPLY_MAX_RPM = "supply_max_rpm"
CONF_EXHAUST_MAX_RPM = "exhaust_max_rpm"


def data_updated_event(entry_id: str) -> str:
    """Keep readings from different Swegon units isolated."""
    return f"{DOMAIN}_{entry_id}_data_updated"

ID_TEMPERATURE_SUPPLY = "17"
ID_TEMPERATURE_ROOM = "18"
ID_TEMPERATURE_OUTSIDE = "19"
ID_HUMIDITY_PERCENTAGE = "22"
ID_HUMIDITY_GM3 = "23"
ID_CURRENT_FAN_SPEED = "27"
ID_VENTILATION_LEVEL_IN = "28"
ID_VENTILATION_LEVEL_OUT = "29"
ID_BOOST_COUNT_DOWN = "31"
ID_AFTERHEATER_PERCENT = "38"  # Confirmed as heater control percent on R5.
TRAVELLING_MODE_TEMPERATURE_DROP = "121"
ID_SETPOINT_SUPPLY_TEMPERATURE = "163"

ID_SET_MODE = "111"
ID_MODE_AWAY = "1"
ID_MODE_HOME = "2"
ID_MODE_BOOST = "3"
ID_MODE_OFF = "0"

ID_SET_MODE_FIREPLACE = "153"
ID_SET_MODE_TRAVEL = "154"


class ClimateMode(StrEnum):
    """Climate modes."""

    AWAY = "away"
    HOME = "home"
    BOOST = "boost"
    OFF = "off"


MODE_MAPPINGS = {
    "0": "Off",
    "1": "Away",
    "2": "Home",
    "3": "Boost",
}

CLIMATE_MODE_MAP = {
    "away": ID_MODE_AWAY,
    "home": ID_MODE_HOME,
    "boost": ID_MODE_BOOST,
    "off": ID_MODE_OFF,
}


SENSOR_CONFIG: dict[str, dict[str, Any]] = {
    ID_TEMPERATURE_SUPPLY: {
        "key": "supply_temperature",
        "name": "FTX Supply Temperature",
        "device_class": "temperature",
        "unit_of_measurement": "°C",
        "state_class": "measurement",
        "icon": "mdi:thermometer-chevron-up",
    },
    ID_TEMPERATURE_ROOM: {
        "key": "room_temperature",
        "name": "FTX Room Temperature",
        "device_class": "temperature",
        "unit_of_measurement": "°C",
        "state_class": "measurement",
        "icon": "mdi:home-thermometer",
    },
    ID_TEMPERATURE_OUTSIDE: {
        "key": "outside_temperature",
        "name": "FTX Outside Temperature",
        "device_class": "temperature",
        "unit_of_measurement": "°C",
        "state_class": "measurement",
        "icon": "mdi:thermometer",
    },
    ID_HUMIDITY_PERCENTAGE: {
        "key": "humidity_percentage",
        "name": "FTX Humidity",
        "device_class": "humidity",
        "unit_of_measurement": "%",
        "state_class": "measurement",
        "icon": "mdi:water-percent",
    },
    ID_HUMIDITY_GM3: {
        "key": "humidity_absolute",
        "name": "FTX Absolute Humidity",
        "device_class": None,
        "unit_of_measurement": "g/m³",
        "state_class": "measurement",
        "icon": "mdi:water",
    },
    ID_CURRENT_FAN_SPEED: {
        "key": "fan_speed",
        "name": "FTX Fan Speed (unverified API value)",
        "device_class": None,
        # API ID 27 returned 2; this is not a verified fan RPM reading.
        "unit_of_measurement": None,
        "state_class": None,
        "icon": "mdi:fan",
    },
    ID_VENTILATION_LEVEL_IN: {
        "key": "ventilation_level_in",
        "name": "FTX Ventilation Level In",
        "device_class": None,
        "unit_of_measurement": "%",
        "state_class": "measurement",
        "icon": "mdi:arrow-down-bold",
    },
    ID_VENTILATION_LEVEL_OUT: {
        "key": "ventilation_level_out",
        "name": "FTX Ventilation Level Out",
        "device_class": None,
        "unit_of_measurement": "%",
        "state_class": "measurement",
        "icon": "mdi:arrow-up-bold",
    },
    ID_BOOST_COUNT_DOWN: {
        "key": "boost_countdown",
        "name": "FTX Boost Countdown",
        "device_class": "duration",
        "unit_of_measurement": "min",
        "state_class": "measurement",
        "icon": "mdi:timer",
    },
    ID_AFTERHEATER_PERCENT: {
        "key": "afterheater_percent",
        "name": "FTX Eftervärme effekt",
        "device_class": None,
        "unit_of_measurement": "%",
        "state_class": "measurement",
        "icon": "mdi:radiator",
    },
    TRAVELLING_MODE_TEMPERATURE_DROP: {
        "key": "travel_temp_drop",
        "name": "FTX Travel Mode Temperature Drop",
        "device_class": "temperature",
        "unit_of_measurement": "°C",
        "state_class": "measurement",
        "icon": "mdi:thermometer-minus",
    },
    ID_SETPOINT_SUPPLY_TEMPERATURE: {
        "key": "supply_temp_setpoint",
        "name": "FTX Supply Temperature Setpoint",
        "device_class": "temperature",
        "unit_of_measurement": "°C",
        "state_class": "measurement",
        "icon": "mdi:thermometer-lines",
    },
    ID_SET_MODE: {
        "key": "current_mode",
        "name": "FTX Current Mode",
        "device_class": None,
        "unit_of_measurement": None,
        "state_class": None,
        "icon": "mdi:home-automation",
        "options": ["Off", "Away", "Home", "Boost"],
    },
    ID_SET_MODE_FIREPLACE: {
        "key": "fireplace_mode",
        "name": "FTX Fireplace Mode",
        "device_class": None,
        "unit_of_measurement": None,
        "state_class": None,
        "icon": "mdi:fireplace",
    },
    ID_SET_MODE_TRAVEL: {
        "key": "travel_mode",
        "name": "FTX Travel Mode",
        "device_class": None,
        "unit_of_measurement": None,
        "state_class": None,
        "icon": "mdi:briefcase-check",
    },
}
