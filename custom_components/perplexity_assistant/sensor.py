"""Sensor platform for Perplexity Assistant credits.

This creates a sensor that (placeholder) would fetch remaining credits or usage
from the Perplexity API. Since the public API for credits may not be available
or documented, this implementation uses a dummy value and is structured so it
can be easily extended later.
"""
from __future__ import annotations

import logging

from datetime import datetime, timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(hours=1)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Perplexity credit sensor from a config entry."""
    monthly_bill_sensor = MonthlyBillSensor(hass, entry.entry_id)
    alltime_bill_sensor = AlltimeBillSensor(hass, entry.entry_id)
    async_add_entities([monthly_bill_sensor, alltime_bill_sensor])
    
    hass.data.setdefault("perplexity_assistant_sensors", {})["monthly_bill_sensor"] = monthly_bill_sensor
    hass.data.setdefault("perplexity_assistant_sensors", {})["alltime_bill_sensor"] = alltime_bill_sensor
    

class MonthlyBillSensor(SensorEntity, RestoreEntity):
    """Sensor representing remaining Perplexity credits (placeholder)."""
    _attr_icon = "mdi:robot"
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

    async def async_added_to_hass(self):
        """Restore previous state when HA restarts."""
        last_state = await self.async_get_last_state()
        
        if last_state and last_state.state not in (None, "unknown", "unavailable"):
            try: self._attr_native_value = float(last_state.state)
            except ValueError: self._attr_native_value = 0.0
            
            last_attrs = last_state.attributes or {}
            
            if "last_reset" in last_attrs:
                try: self._last_reset = datetime.fromisoformat(last_attrs["last_reset"])
                except Exception: _LOGGER.warning("Failed to parse last_reset timestamp")
        else:
            self._attr_native_value = 0.0
            self._last_reset = datetime.now().replace(day=1, hour=0, minute=0, second=0)
            self._attr_extra_state_attributes = {"last_reset_month": self._last_reset}
            
            

    @property
    def native_value(self) -> float:
        """Return the native value of the sensor."""
        return round(self._attr_native_value, 4)
    
    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{self._entry_id}_perplexity_monthly_bill"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
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
        self._attr_extra_state_attributes = {"last_reset_month": self._last_reset}
        self.async_write_ha_state()


class AlltimeBillSensor(SensorEntity, RestoreEntity):
    """Sensor representing remaining Perplexity credits (placeholder)."""
    _attr_icon = "mdi:robot"
    _attr_native_unit_of_measurement = "$"
    
    _attr_name = "Total Cost"
    _attr_native_unit_of_measurement = "$"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize the All-time Bill Sensor."""
        self.hass = hass
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_perplexity_bill"
        self._attr_native_value = 0.0
        self._last_reset = datetime.now().replace(day=1, hour=0, minute=0, second=0)

    async def async_added_to_hass(self):
        """Restore previous state when HA restarts."""
        last_state = await self.async_get_last_state()
        
        if last_state and last_state.state not in (None, "unknown", "unavailable"):
            try: self._attr_native_value = float(last_state.state)
            except ValueError: self._attr_native_value = 0.0
        else:
            self._attr_native_value = 0.0
            
    @property
    def native_value(self) -> float:
        """Return the native value of the sensor."""
        return round(self._attr_native_value, 4)
    
    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{self._entry_id}_perplexity_bill"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Perplexity Bill"

    def increment_cost(self, cost: float):
        """Add cost to current cost."""
        self._attr_native_value += cost
        self.async_write_ha_state()