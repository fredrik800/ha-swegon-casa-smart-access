"""Climate platform for Swegon Casa."""

from typing import Any

from homeassistant.components.climate import ClimateEntity, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import SwegonCasaClient
from .const import DOMAIN
from .lib import ClimateModes, SwegonObjectId


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Swegon Casa climate platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: SwegonCasaClient = data["client"]

    entity = SwegonCasaClimate(hass, client, entry.entry_id)
    async_add_entities([entity])


class SwegonCasaClimate(ClimateEntity):
    """Swegon Casa climate entity."""

    _attr_hvac_modes = [HVACMode.OFF, HVACMode.AUTO, HVACMode.FAN_ONLY]  # noqa: RUF012
    _attr_has_entity_name = True
    _attr_min_temp = 15.0
    _attr_max_temp = 30.0

    def __init__(
        self,
        hass: HomeAssistant,
        client: SwegonCasaClient,
        entry_id: str,
    ) -> None:
        """Initialize the climate entity."""
        self.hass = hass
        self.client = client
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_climate"
        self._attr_name = "Climate"

        self._climate_mode: str = ClimateModes.HOME
        self._attr_current_temperature: float | None = None
        self._attr_target_temperature: float | None = None
        self._attr_hvac_mode: HVACMode | None = HVACMode.FAN_ONLY

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

        supply_temp = data.get(str(SwegonObjectId.TEMPERATURE_SUPPLY))
        if supply_temp is not None:
            self._attr_current_temperature = float(supply_temp)

        setpoint_temp = data.get(str(SwegonObjectId.SETPOINT_SUPPLY_TEMPERATURE))
        if setpoint_temp is not None:
            self._attr_target_temperature = float(setpoint_temp)

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
            self._climate_mode = climate_modes_map.get(
                int(climate_mode_value), ClimateModes.HOME
            )
            if self._climate_mode == ClimateModes.OFF:
                self._attr_hvac_mode = HVACMode.OFF
            else:
                self._attr_hvac_mode = HVACMode.FAN_ONLY

        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            new_mode = 5
        else:
            new_mode = 2

        await self.client.set_value(str(SwegonObjectId.CLIMATE_MODE), new_mode)
