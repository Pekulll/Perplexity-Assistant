"""Initialization of the Perplexity Assistant module for Home Assistant."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import discovery
from .const import DOMAIN, CONF_API_KEY, CONF_MODEL, CONF_LANGUAGE
from .conversation import PerplexityAgent

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
    _LOGGER = logging.getLogger(__name__)
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
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
    
    api_key = entry.data.get(CONF_API_KEY)
    model = entry.data.get(CONF_MODEL, "sonar-small-online")
    language = entry.data.get(CONF_LANGUAGE, "en")
    
    session = hass.helpers.aiohttp_client.async_get_clientsession()
    agent = PerplexityAgent(hass, session, api_key, model, language)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = agent

    
    # Load the conversation component
    conversation.async_set_agent(hass, DOMAIN, agent)
    hass.services.async_register(DOMAIN, "ask", agent.async_ask)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
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
    
    hass.data.pop(entry.entry_id, None)
    hass.services.async_remove(DOMAIN, "ask")
    
    return True