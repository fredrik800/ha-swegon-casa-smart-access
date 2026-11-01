"""Select platform for Swegon Casa."""

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import SwegonCasaClient
from .const import DOMAIN
from .lib import (
    AutoHumidityControlModes,
    ClimateModes,
    FireplaceModes,
    SummerNightCoolingModes,
    SwegonObjectId,
    TravelModes,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Swegon Casa select platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: SwegonCasaClient = data["client"]
    entry_id = entry.entry_id

    selects = [
        SwegonCasaClimateSelect(hass, client, entry_id),
        SwegonCasaFireplaceModeSelect(hass, client, entry_id),
        SwegonCasaTravelModeSelect(hass, client, entry_id),
        SwegonCasaAutoHumidityControlSelect(hass, client, entry_id),
        SwegonCasaSummerNightCoolingSelect(hass, client, entry_id),
    ]

    async_add_entities(selects)


class SwegonCasaClimateSelect(SelectEntity):
    """Swegon Casa climate mode select."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        client: SwegonCasaClient,
        entry_id: str,
    ) -> None:
        """Initialize the select entity."""
        self.hass = hass
        self.client = client
        self._attr_name = "Climate Mode"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_climate_mode"
        self._attr_current_option = ClimateModes.HOME
        self._attr_options = [m.value for m in ClimateModes]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_data_updated_{self.client.host.replace('.', '_')}",
                self._handle_data_update,
            )
        )

    @callback
    async def _handle_data_update(self, event: Any) -> None:
        """Handle data update event."""
        data = event.data.get("data", {})
        climate_mode_value = data.get(str(SwegonObjectId.CLIMATE_MODE))

        if climate_mode_value is not None:
            climate_modes_map = {
                1: ClimateModes.AWAY,
                2: ClimateModes.HOME,
                3: ClimateModes.BOOST,
                4: ClimateModes.TRAVEL,
                5: ClimateModes.OFF,
                6: ClimateModes.FIREPLACE,
            }
            self._attr_current_option = climate_modes_map.get(
                int(climate_mode_value), ClimateModes.HOME
            )
            self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        climate_mode_map: dict[str, int] = {
            ClimateModes.AWAY: 1,
            ClimateModes.HOME: 2,
            ClimateModes.BOOST: 3,
            ClimateModes.TRAVEL: 4,
            ClimateModes.OFF: 5,
            ClimateModes.FIREPLACE: 6,
        }

        new_mode = climate_mode_map.get(option, 2)
        await self.client.set_value(str(SwegonObjectId.CLIMATE_MODE), new_mode)


class SwegonCasaFireplaceModeSelect(SelectEntity):
    """Swegon Casa fireplace mode select."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        client: SwegonCasaClient,
        entry_id: str,
    ) -> None:
        """Initialize the select entity."""
        self.hass = hass
        self.client = client
        self._attr_name = "Fireplace Mode"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_fireplace_mode"
        self._attr_current_option = FireplaceModes.OFF
        self._attr_options = [m.value for m in FireplaceModes]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_data_updated_{self.client.host.replace('.', '_')}",
                self._handle_data_update,
            )
        )

    @callback
    async def _handle_data_update(self, event: Any) -> None:
        """Handle data update event."""
        data = event.data.get("data", {})
        fireplace_mode_value = data.get(str(SwegonObjectId.FIREPLACE_MODE))

        if fireplace_mode_value is not None:
            fireplace_mode_map: dict[int, FireplaceModes] = {
                0: FireplaceModes.OFF,
                1: FireplaceModes.ON,
            }
            self._attr_current_option = fireplace_mode_map.get(
                int(fireplace_mode_value), FireplaceModes.OFF
            )
            self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        fireplace_mode_reverse_map: dict[str, int] = {
            FireplaceModes.OFF: 0,
            FireplaceModes.ON: 1,
        }

        value = fireplace_mode_reverse_map.get(option, 0)
        await self.client.set_value(str(SwegonObjectId.FIREPLACE_MODE), value)


class SwegonCasaTravelModeSelect(SelectEntity):
    """Swegon Casa travel mode select.

    Note: Travel mode is only visible in the UI when BOTH conditions are met:
    1. Climate mode is set to Travel (4)
    2. Travel mode flag (154) is set to ON (1)

    When turning on travel mode, the integration automatically sets the climate mode
    to Travel if it's not already set. When turning off travel mode, the climate mode
    is NOT automatically changed to preserve user preferences.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        client: SwegonCasaClient,
        entry_id: str,
    ) -> None:
        """Initialize the select entity."""
        self.hass = hass
        self.client = client
        self._attr_name = "Travel Mode"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_travel_mode"
        self._attr_current_option = TravelModes.OFF
        self._attr_options = [m.value for m in TravelModes]
        self._climate_mode: int | None = None

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_data_updated_{self.client.host.replace('.', '_')}",
                self._handle_data_update,
            )
        )

    @callback
    async def _handle_data_update(self, event: Any) -> None:
        """Handle data update event."""
        data = event.data.get("data", {})
        travel_mode_value = data.get(str(SwegonObjectId.TRAVEL_MODE))
        self._climate_mode = data.get(str(SwegonObjectId.CLIMATE_MODE))

        if travel_mode_value is not None:
            travel_mode_map: dict[int, TravelModes] = {
                0: TravelModes.OFF,
                1: TravelModes.ON,
            }
            self._attr_current_option = travel_mode_map.get(
                int(travel_mode_value), TravelModes.OFF
            )
            self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Select an option.

        When turning ON travel mode, also sets climate mode to Travel (4).
        """
        travel_mode_reverse_map: dict[str, int] = {
            TravelModes.OFF: 0,
            TravelModes.ON: 1,
        }

        value = travel_mode_reverse_map.get(option, 0)

        if value == 1 and self._climate_mode != 4:
            await self.client.set_value(str(SwegonObjectId.CLIMATE_MODE), 4)

        await self.client.set_value(str(SwegonObjectId.TRAVEL_MODE), value)


class SwegonCasaAutoHumidityControlSelect(SelectEntity):
    """Swegon Casa auto humidity control mode select."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        client: SwegonCasaClient,
        entry_id: str,
    ) -> None:
        """Initialize the select entity."""
        self.hass = hass
        self.client = client
        self._attr_name = "Auto Humidity Control Mode"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_auto_humidity_control_mode"
        self._attr_current_option = AutoHumidityControlModes.OFF
        self._attr_options = [m.value for m in AutoHumidityControlModes]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_data_updated_{self.client.host.replace('.', '_')}",
                self._handle_data_update,
            )
        )

    @callback
    async def _handle_data_update(self, event: Any) -> None:
        """Handle data update event."""
        data = event.data.get("data", {})
        humidity_mode_value = data.get(str(SwegonObjectId.AUTO_HUMIDITY_CONTROL_MODE))

        if humidity_mode_value is not None:
            humidity_mode_map: dict[int, AutoHumidityControlModes] = {
                0: AutoHumidityControlModes.OFF,
                1: AutoHumidityControlModes.USER,
                2: AutoHumidityControlModes.LOW,
                3: AutoHumidityControlModes.NORMAL,
                4: AutoHumidityControlModes.HIGH,
                5: AutoHumidityControlModes.FULL,
            }
            self._attr_current_option = humidity_mode_map.get(
                int(humidity_mode_value), AutoHumidityControlModes.OFF
            )
            self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        humidity_mode_reverse_map: dict[str, int] = {
            AutoHumidityControlModes.OFF: 0,
            AutoHumidityControlModes.USER: 1,
            AutoHumidityControlModes.LOW: 2,
            AutoHumidityControlModes.NORMAL: 3,
            AutoHumidityControlModes.HIGH: 4,
            AutoHumidityControlModes.FULL: 5,
        }

        value = humidity_mode_reverse_map.get(option, 0)
        await self.client.set_value(
            str(SwegonObjectId.AUTO_HUMIDITY_CONTROL_MODE), value
        )


class SwegonCasaSummerNightCoolingSelect(SelectEntity):
    """Swegon Casa summer night cooling mode select."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        client: SwegonCasaClient,
        entry_id: str,
    ) -> None:
        """Initialize the select entity."""
        self.hass = hass
        self.client = client
        self._attr_name = "Summer Night Cooling Mode"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_summer_night_cooling_mode"
        self._attr_current_option = SummerNightCoolingModes.OFF
        self._attr_options = [m.value for m in SummerNightCoolingModes]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_data_updated_{self.client.host.replace('.', '_')}",
                self._handle_data_update,
            )
        )

    @callback
    async def _handle_data_update(self, event: Any) -> None:
        """Handle data update event."""
        data = event.data.get("data", {})
        cooling_mode_value = data.get(str(SwegonObjectId.SUMMER_NIGHT_COOLING_MODE))

        if cooling_mode_value is not None:
            cooling_mode_map: dict[int, SummerNightCoolingModes] = {
                0: SummerNightCoolingModes.OFF,
                1: SummerNightCoolingModes.LOW,
                2: SummerNightCoolingModes.NORMAL,
                3: SummerNightCoolingModes.HIGH,
                4: SummerNightCoolingModes.FULL,
                5: SummerNightCoolingModes.USER,
            }
            self._attr_current_option = cooling_mode_map.get(
                int(cooling_mode_value), SummerNightCoolingModes.OFF
            )
            self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        cooling_mode_reverse_map: dict[str, int] = {
            SummerNightCoolingModes.OFF: 0,
            SummerNightCoolingModes.LOW: 1,
            SummerNightCoolingModes.NORMAL: 2,
            SummerNightCoolingModes.HIGH: 3,
            SummerNightCoolingModes.FULL: 4,
            SummerNightCoolingModes.USER: 5,
        }

        value = cooling_mode_reverse_map.get(option, 0)
        await self.client.set_value(
            str(SwegonObjectId.SUMMER_NIGHT_COOLING_MODE), value
        )
