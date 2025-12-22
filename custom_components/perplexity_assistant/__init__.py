"""Initialization of the Perplexity Assistant module for Home Assistant."""
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.components import conversation as ha_conversation
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from typing import Any

from .conversation import PerplexityAgent
from .const import *

# Platforms we set up when requested
PLATFORMS: list[str] = ["sensor"]

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Prepare the Perplexity integration when Home Assistant starts.

    This function is called during module initialization.
    It can prepare the general state of the module (services, data, etc.).

    Args:
        hass (HomeAssistant): Home Assistant instance.
        config (ConfigType): Global configuration.
    Returns:
        bool: True if initialization is successful.
    """
    _LOGGER.debug("Setup of the Perplexity Assistant module")
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Perplexity Assistant from a config entry.

    This function is called when a configuration entry is created.
    It sets up the necessary components for the integration.

    Args:
        hass (HomeAssistant): Home Assistant instance.
        entry: Configuration entry.
    Returns:
        bool: True if setup is successful.
    """
    _LOGGER.debug("Setting up Perplexity Assistant from config entry")
    
    # Forward setup to sensor platform
    if entry.data.get("create_credit_sensor"):
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    agent = PerplexityAgent(hass, entry.entry_id)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = agent
    
    # Register the conversation agent and service
    ha_conversation.async_set_agent(hass, entry, agent)
    service_schema = vol.Schema({
        vol.Required("prompt"): cv.string,
        vol.Optional("model"): cv.string,
        vol.Optional("enable_websearch"): cv.boolean,
        vol.Optional("execute_actions"): cv.boolean,
        vol.Optional("force_actions_execution"): cv.boolean
    })
    
    hass.services.async_register(DOMAIN, "ask", agent.async_ask, schema=service_schema, supports_response="optional")
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry for Perplexity Assistant.

    This function is called when a configuration entry is removed.
    It cleans up the resources associated with the integration.

    Args:
        hass (HomeAssistant): Home Assistant instance.
        entry: Configuration entry.
    Returns:
        bool: True if unload is successful.
    """
    _LOGGER.debug("Unloading Perplexity Assistant config entry")
    
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None) # Remove agent from data
    hass.services.async_remove(DOMAIN, "ask") # Remove service

    # Unload platforms
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    return True