"""Sensor platform for Perplexity Assistant credits.

This creates a sensor that (placeholder) would fetch remaining credits or usage
from the Perplexity API. Since the public API for credits may not be available
or documented, this implementation uses a dummy value and is structured so it
can be easily extended later.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, CONF_API_KEY

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=1)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Perplexity credit sensor from a config entry."""
    api_key: str | None = entry.data.get(CONF_API_KEY)

    monthly_bill_sensor = MonthlyBillSensor(hass, entry.entry_id)
    alltime_bill_sensor = AlltimeBillSensor(hass, entry.entry_id)
    async_add_entities([monthly_bill_sensor, alltime_bill_sensor])
    
    hass.data.setdefault("perplexity_assistant_sensors", {})["monthly_bill_sensor"] = monthly_bill_sensor
    hass.data.setdefault("perplexity_assistant_sensors", {})["alltime_bill_sensor"] = alltime_bill_sensor
    

class MonthlyBillSensor(SensorEntity):
    """Sensor representing remaining Perplexity credits (placeholder)."""

    _attr_icon = "mdi:ticket-percent"
    _attr_native_unit_of_measurement = "$"
    
    _attr_name = "Monthly Cost"
    _attr_native_unit_of_measurement = "$"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_perplexity_monthly_bill"
        self._attr_native_value = 0.0
        self._last_reset = datetime.now().replace(day=1, hour=0, minute=0, second=0)

    @property
    def native_value(self) -> float:
        return round(self._attr_native_value, 4)
    
    @property
    def unique_id(self) -> str:
        return f"{self._entry_id}_perplexity_monthly_bill"

    @property
    def name(self) -> str:
        return "Perplexity Monthly Bill"

    def increment_cost(self, cost: float):
        """Add cost to current month."""
        if datetime.now().month != self._last_reset.month:
            self.reset_monthly_cost()
            
        self._attr_native_value += cost
        self.async_write_ha_state()

    def reset_monthly_cost(self):
        """Reset at the beginning of each month."""
        _LOGGER.debug("Resetting Perplexity monthly cost")
        self._attr_native_value = 0.0
        self._last_reset = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        self.async_write_ha_state()


class AlltimeBillSensor(SensorEntity):
    """Sensor representing remaining Perplexity credits (placeholder)."""

    _attr_icon = "mdi:ticket-percent"
    _attr_native_unit_of_measurement = "$"
    
    _attr_name = "Total Cost"
    _attr_native_unit_of_measurement = "$"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_perplexity_bill"
        self._attr_native_value = 0.0
        self._last_reset = datetime.now().replace(day=1, hour=0, minute=0, second=0)

    @property
    def native_value(self) -> float:
        return round(self._attr_native_value, 4)
    
    @property
    def unique_id(self) -> str:
        return f"{self._entry_id}_perplexity_bill"

    @property
    def name(self) -> str:
        return "Perplexity Bill"

    def increment_cost(self, cost: float):
        """Add cost to current month."""
        self._attr_native_value += cost
        self.async_write_ha_state()