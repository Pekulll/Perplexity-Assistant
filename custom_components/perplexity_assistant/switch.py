"""Switch platform for Perplexity Assistant."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory, DeviceInfo

from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Perplexity switch from a config entry."""
    voice_notification_switch = VoiceNotificationSwitch(hass, entry.entry_id)
    web_search_switch = WebSearchSwitch(hass, entry.entry_id, entry)
    entity_actions_switch = EntityActionsSwitch(hass, entry.entry_id, entry)
    entity_access_switch = EntityAccessSwitch(hass, entry.entry_id, entry)
    
    async_add_entities([voice_notification_switch, web_search_switch, entity_actions_switch, entity_access_switch])
    
    hass.data.setdefault("perplexity_assistant_sensors", {})["voice_notification_switch"] = voice_notification_switch
    hass.data.setdefault("perplexity_assistant_sensors", {})["web_search_switch"] = web_search_switch
    hass.data.setdefault("perplexity_assistant_sensors", {})["entity_actions_switch"] = entity_actions_switch
    hass.data.setdefault("perplexity_assistant_sensors", {})["entity_access_switch"] = entity_access_switch


class VoiceNotificationSwitch(SwitchEntity, RestoreEntity):
    """Switch to enable/disable voice responses from Perplexity Assistant."""
    
    _attr_icon = "mdi:account-voice"
    _attr_has_entity_name = True
    _attr_translation_key = "voice_notifications"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self._entry_id = entry_id
        self._is_on = True

    async def async_added_to_hass(self):
        """Restore previous state."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
             if state.state == "off":
                 self._is_on = False
             elif state.state == "on":
                 self._is_on = True

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        self._is_on = False
        self.async_write_ha_state()
    
    @property
    def unique_id(self) -> str:
        """Return the unique ID of the switch."""
        return f"{self._entry_id}_voice_notifications"
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="Perplexity Assistant",
            manufacturer="Perplexity AI",
            model="Perplexity API",
        )


class WebSearchSwitch(SwitchEntity, RestoreEntity):
    """Switch to enable/disable web search."""
    
    _attr_icon = "mdi:web"
    _attr_has_entity_name = True
    _attr_translation_key = "web_search"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry_id: str, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry_id = entry_id
        self._entry = entry
        self._is_on = entry.options.get(CONF_ENABLE_WEBSEARCH, DEFAULT_ENABLE_WEBSEARCH)

    async def async_added_to_hass(self):
        """Restore previous state."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
             if state.state == "off":
                 self._is_on = False
             elif state.state == "on":
                 self._is_on = True

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        self._is_on = False
        self.async_write_ha_state()
    
    @property
    def unique_id(self) -> str:
        """Return the unique ID of the switch."""
        return f"{self._entry_id}_web_search"
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="Perplexity Assistant",
            manufacturer="Perplexity AI",
            model="Perplexity API",
        )


class EntityActionsSwitch(SwitchEntity, RestoreEntity):
    """Switch to enable/disable entity actions."""
    
    _attr_icon = "mdi:gavel"
    _attr_has_entity_name = True
    _attr_translation_key = "entity_actions"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry_id: str, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry_id = entry_id
        self._entry = entry
        self._is_on = entry.options.get(CONF_ALLOW_ACTIONS_ON_ENTITIES, DEFAULT_ALLOW_ACTIONS_ON_ENTITIES)

    async def async_added_to_hass(self):
        """Restore previous state."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
             if state.state == "off":
                 self._is_on = False
             elif state.state == "on":
                 self._is_on = True

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        self._is_on = False
        self.async_write_ha_state()
    
    @property
    def unique_id(self) -> str:
        """Return the unique ID of the switch."""
        return f"{self._entry_id}_entity_actions"
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="Perplexity Assistant",
            manufacturer="Perplexity AI",
            model="Perplexity API",
        )
        
        
class EntityAccessSwitch(SwitchEntity, RestoreEntity):
    """Switch to enable/disable entity access."""
    
    _attr_icon = "mdi:eye"
    _attr_has_entity_name = True
    _attr_translation_key = "entity_access"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry_id: str, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry_id = entry_id
        self._entry = entry
        self._is_on = entry.options.get(CONF_ALLOW_ENTITIES_ACCESS, DEFAULT_ALLOW_ENTITIES_ACCESS)

    async def async_added_to_hass(self):
        """Restore previous state."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
             if state.state == "off":
                 self._is_on = False
             elif state.state == "on":
                 self._is_on = True

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        self._is_on = False
        self.async_write_ha_state()
    
    @property
    def unique_id(self) -> str:
        """Return the unique ID of the switch."""
        return f"{self._entry_id}_entity_access"
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="Perplexity Assistant",
            manufacturer="Perplexity AI",
            model="Perplexity API",
        )