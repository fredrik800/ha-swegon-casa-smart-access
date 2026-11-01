"""Number platform for Swegon Casa."""

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import SwegonCasaClient
from .const import DOMAIN
from .lib import SwegonObjectId


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Swegon Casa number platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: SwegonCasaClient = data["client"]

    entity = SwegonCasaSupplyTemperatureSetpoint(hass, client, entry.entry_id)
    async_add_entities([entity])


class SwegonCasaSupplyTemperatureSetpoint(NumberEntity):
    """Swegon Casa supply temperature setpoint number."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 15.0
    _attr_native_max_value = 30.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        hass: HomeAssistant,
        client: SwegonCasaClient,
        entry_id: str,
    ) -> None:
        """Initialize the number entity."""
        self.hass = hass
        self.client = client
        self._attr_name = "Supply Temperature Setpoint"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_supply_temperature_setpoint"
        self._attr_native_value = 20.0

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
        setpoint_temp = data.get(str(SwegonObjectId.SETPOINT_SUPPLY_TEMPERATURE))

        if setpoint_temp is not None:
            self._attr_native_value = float(setpoint_temp)
            self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set the temperature setpoint."""
        await self.client.set_value(
            str(SwegonObjectId.SETPOINT_SUPPLY_TEMPERATURE), int(value)
        )
