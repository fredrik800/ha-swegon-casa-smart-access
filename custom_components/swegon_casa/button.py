"""Button platform for resetting Swegon CASA energy estimates."""

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .energy import SwegonCasaEnergyTracker


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add an energy reset button for this CASA unit."""
    tracker: SwegonCasaEnergyTracker = hass.data[DOMAIN][entry.entry_id][
        "energy_tracker"
    ]
    async_add_entities([SwegonCasaResetEnergyButton(tracker, entry.entry_id)])


class SwegonCasaResetEnergyButton(ButtonEntity):
    """Clear both energy totals for the selected CASA unit."""

    _attr_has_entity_name = True
    _attr_name = "FTX Reset Energy Consumption"
    _attr_icon = "mdi:counter"

    def __init__(self, tracker: SwegonCasaEnergyTracker, entry_id: str) -> None:
        self.tracker = tracker
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_reset_energy"

    async def async_press(self) -> None:
        """Reset only this unit's energy history."""
        await self.tracker.async_reset()
