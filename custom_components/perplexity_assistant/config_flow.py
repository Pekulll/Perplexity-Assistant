"""Config flow for Perplexity Assistant integration in Home Assistant."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.selector import SelectSelector, BooleanSelector, NumberSelector

from .const import *


# User input schema: only the API key is requested.

@config_entries.HANDLERS.register(DOMAIN)
class PerplexityConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow handler for configuration via the UI."""
    
    async def async_step_user(self, user_input: dict[str, any] | None = None) -> config_entries.ConfigFlowResult:
        """First step of the flow: prompts the user for the API key.

        Args:
            user_input (dict | None): Dictionary containing the user input or None.
        Returns:
            ConfigFlowResult: Shows the form or creates the config entry.
        """
        errors = {}

        # If the user has submitted the form
        if user_input is not None:
            api_key: str = user_input.get(CONF_API_KEY, "")

            # Check if the API key has a valid format
            if not api_key.startswith("pplx-"):
                errors[CONF_API_KEY] = "invalid_api_key"
            else:
                # If the API key is valid, create the config entry
                # Store a flag so the integration can create a credit sensor in async_setup_entry
                data = {**user_input, "create_credit_sensor": True}
                return self.async_create_entry(title=f"Perplexity Assistant - {data[CONF_LANGUAGE]}{api_key[-4:]}", data=data,)

        # Define the data schema for the form
        STEP_USER_DATA_SCHEMA = vol.Schema({
            vol.Required(CONF_API_KEY): vol.All(str, vol.Length(min=53, max=53)),
            vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): SelectSelector({"options": SUPPORTED_LANGUAGES, "mode": "dropdown"}),
            vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): SelectSelector({"options": SUPPORTED_MODELS, "mode": "dropdown"}),
            vol.Optional(CONF_CUSTOM_SYSTEM_PROMPT, default=""): vol.All(str, vol.Length(max=250)),
            vol.Optional(CONF_ENTITIES_SUMMARY_REFRESH_RATE, default=DEFAULT_ENTITIES_SUMMARY_REFRESH_RATE): NumberSelector({"min": 5, "step": 5, "mode": "box", "unit_of_measurement": "s", "max": 43200}),
            vol.Optional(CONF_ENABLE_WEBSEARCH, default=False): BooleanSelector(),
            vol.Optional(CONF_ALLOW_ENTITIES_ACCESS, default=False): BooleanSelector(),
            vol.Optional(CONF_ALLOW_ACTIONS_ON_ENTITIES, default=False): BooleanSelector(),
            vol.Optional(CONF_ENABLE_RESPONSE_ON_SPEAKERS, default=False): BooleanSelector(),
            vol.Optional(CONF_NOTIFY_RESPONSE, default=False): BooleanSelector(),
        })
        
        # Otherwise, show the form
        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors, last_step=True,)
        
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return PerplexityOptionsFlowHandler(config_entry.entry_id)
    
class PerplexityOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Perplexity Assistant options."""

    def __init__(self, config_entry_id: str) -> None:
        """Initialize options flow handler.

        Args:
            config_entry (ConfigEntry): The configuration entry.
        """
        self.config_entry_id = config_entry_id

    async def async_step_init(self, user_input: dict[str, any] | None = None) -> config_entries.ConfigFlowResult:
        """Manage the options step.

        Args:
            user_input (dict | None): Dictionary containing the user input or None.
        Returns:
            ConfigFlowResult: Shows the form or creates the options entry.
        """
        errors = {}
        
        if user_input is not None:
            api_key: str = user_input.get(CONF_API_KEY, "")
            
            # Check if the API key has a valid format
            if not api_key.startswith("pplx-"):
                errors[CONF_API_KEY] = "invalid_api_key"
            else:
                # If the API key is valid, create the config entry
                return self.async_create_entry(title="", data=user_input)
            

        # Show the form to update options
        config_entry: ConfigEntry = self.hass.config_entries.async_get_entry(self.config_entry_id)
        current_api_key: str = config_entry.options.get(CONF_API_KEY) or config_entry.data.get(CONF_API_KEY, "")
        current_model: str = config_entry.options.get(CONF_MODEL) or config_entry.data.get(CONF_MODEL, DEFAULT_MODEL)
        current_language: str = config_entry.options.get(CONF_LANGUAGE) or config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        current_custom_system_prompt: str = config_entry.options.get(CONF_CUSTOM_SYSTEM_PROMPT) or config_entry.data.get(CONF_CUSTOM_SYSTEM_PROMPT, "")
        current_entities_summary_refresh_rate: int = config_entry.options.get(CONF_ENTITIES_SUMMARY_REFRESH_RATE) or config_entry.data.get(CONF_ENTITIES_SUMMARY_REFRESH_RATE, DEFAULT_ENTITIES_SUMMARY_REFRESH_RATE)
        current_enable_websearch: bool = config_entry.options.get(CONF_ENABLE_WEBSEARCH) or config_entry.data.get(CONF_ENABLE_WEBSEARCH, False)
        current_allow_entities_access: bool = config_entry.options.get(CONF_ALLOW_ENTITIES_ACCESS) or config_entry.data.get(CONF_ALLOW_ENTITIES_ACCESS, False)
        current_allow_actions_on_entities: bool = config_entry.options.get(CONF_ALLOW_ACTIONS_ON_ENTITIES) or config_entry.data.get(CONF_ALLOW_ACTIONS_ON_ENTITIES, False)
        current_notify_response: bool = config_entry.options.get(CONF_NOTIFY_RESPONSE) or config_entry.data.get(CONF_NOTIFY_RESPONSE, False)
        current_enable_response_on_speakers: bool = config_entry.options.get(CONF_ENABLE_RESPONSE_ON_SPEAKERS) or config_entry.data.get(CONF_ENABLE_RESPONSE_ON_SPEAKERS, False)

        # Define the options schema with current values as defaults
        options_schema = vol.Schema({
            vol.Required(CONF_API_KEY, default=current_api_key): vol.All(str, vol.Length(min=53, max=53)),
            vol.Optional(CONF_LANGUAGE, default=current_language): SelectSelector({"options": SUPPORTED_LANGUAGES, "mode": "dropdown"}),
            vol.Optional(CONF_MODEL, default=current_model): SelectSelector({"options": SUPPORTED_MODELS, "mode": "dropdown"}),
            vol.Optional(CONF_CUSTOM_SYSTEM_PROMPT, default=current_custom_system_prompt): vol.All(str, vol.Length(max=250)),
            vol.Optional(CONF_ENTITIES_SUMMARY_REFRESH_RATE, default=current_entities_summary_refresh_rate): NumberSelector({"min": 5, "step": 5, "mode": "box", "unit_of_measurement": "s", "max": 43200}),
            vol.Optional(CONF_ENABLE_WEBSEARCH, default=current_enable_websearch): BooleanSelector(),
            vol.Optional(CONF_ALLOW_ENTITIES_ACCESS, default=current_allow_entities_access): BooleanSelector(),
            vol.Optional(CONF_ALLOW_ACTIONS_ON_ENTITIES, default=current_allow_actions_on_entities): BooleanSelector(),
            vol.Optional(CONF_ENABLE_RESPONSE_ON_SPEAKERS, default=current_enable_response_on_speakers): BooleanSelector(),
            vol.Optional(CONF_NOTIFY_RESPONSE, default=current_notify_response): BooleanSelector(),
        })

        return self.async_show_form(step_id="init", data_schema=options_schema, errors=errors,)
