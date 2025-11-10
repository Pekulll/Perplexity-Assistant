"""Initialization of the Perplexity Assistant module for Home Assistant."""
import logging
import voluptuous as vol
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import aiohttp_client
from homeassistant.components import conversation as ha_conversation
from homeassistant.config_entries import ConfigEntry

from .const import (
    CONF_CUSTOM_SYSTEM_PROMPT,
    CONF_NOTIFY_RESPONSE,
    DOMAIN,
    CONF_API_KEY,
    CONF_MODEL,
    CONF_LANGUAGE,
)
from .conversation import PerplexityAgent

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
    
    # Merge options over data (options take precedence)
    data: dict[str, Any] = {**entry.data, **entry.options}

    api_key = data.get(CONF_API_KEY)
    model = data.get(CONF_MODEL, "sonar")
    language = data.get(CONF_LANGUAGE, "en")
    notify_response = data.get(CONF_NOTIFY_RESPONSE, False)
    custom_system_prompt = data.get(CONF_CUSTOM_SYSTEM_PROMPT, "")
        
    session = aiohttp_client.async_get_clientsession(hass)
    agent = PerplexityAgent(hass, entry.entry_id, session, api_key, model, language, notify_response, custom_system_prompt)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = agent

    
    # Register the conversation agent and service
    ha_conversation.async_set_agent(hass, entry, agent)
    hass.services.async_register(DOMAIN, "ask_perplexity", agent.async_ask, schema=vol.Schema({vol.Required("prompt"): str}))

    # Forward setup to sensor platform if requested by config entry (flag set in config_flow)
    if entry.data.get("create_credit_sensor"):
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
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
    
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    hass.services.async_remove(DOMAIN, "ask")

    # Unload platforms
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    return True