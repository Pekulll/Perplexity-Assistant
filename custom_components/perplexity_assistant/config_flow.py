"""Config flow for Perplexity Assistant integration in Home Assistant."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.components import tts
from homeassistant.core import callback
from homeassistant.helpers.selector import (SelectSelector, BooleanSelector, NumberSelector,
                                            SelectSelectorConfig, SelectSelectorMode, TextSelector,
                                            TextSelectorConfig, TextSelectorType)

from .const import *


# User input schema: only the API key is requested.

@config_entries.HANDLERS.register(DOMAIN)
class PerplexityConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow handler for configuration via the UI."""
    
    def __init__(self) -> None:
        """Initialize the config flow."""
        self.data = {}
    
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
            elif len(api_key) != 53:
                errors[CONF_API_KEY] = "invalid_api_key_length"
            else:
                # If the API key is valid, create the config entry
                # Store a flag so the integration can create a credit sensor in async_setup_entry
                data = {**user_input, "create_credit_sensor": True}
                self.data.update(data)
                return await self.async_step_model()

        text_selector = TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD,
                autocomplete="off",
            )
        )
        
        # Define the data schema for the form
        STEP_USER_DATA_SCHEMA = vol.Schema({
            vol.Required(CONF_API_KEY): text_selector,
        })
        
        # Otherwise, show the form
        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors,)
    
    async def async_step_model(self, user_input: dict[str, any] | None = None) -> config_entries.ConfigFlowResult:
        """Second step of the flow: prompts the user for the model.

        Args:
            user_input (dict | None): Dictionary containing the user input or None.
        Returns:
            ConfigFlowResult: Shows the form or creates the config entry.
        """
        text_selector = TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.TEXT,
                autocomplete="off",
                multiline=True,
            )
        )
        
        # Define the data schema for the form
        STEP_USER_DATA_SCHEMA = vol.Schema({
            vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): SelectSelector({"options": SUPPORTED_LANGUAGES, "mode": "dropdown"}),
            vol.Required(CONF_MODEL, default=DEFAULT_MODEL): SelectSelector({"options": SUPPORTED_MODELS, "mode": "dropdown"}),
            vol.Optional(CONF_CUSTOM_SYSTEM_PROMPT, default=""): text_selector,
            vol.Optional('advanced_configuration', default=False): BooleanSelector(),
        })
        
        if user_input is not None:
            if len(user_input.get(CONF_CUSTOM_SYSTEM_PROMPT, "")) > 250:
                return self.async_show_form(
                    step_id="model",
                    data_schema=STEP_USER_DATA_SCHEMA,
                    errors={CONF_CUSTOM_SYSTEM_PROMPT: "max_length_exceeded"},
                )
            
            if user_input.get('advanced_configuration', False):
                self.data.update(user_input)
                return await self.async_step_model_parameters()
            else:
                user_input.pop('advanced_configuration', None)
                self.data.update(user_input)
                return await self.async_step_authorization()
            
        return self.async_show_form(step_id="model", data_schema=STEP_USER_DATA_SCHEMA, last_step=True,)
    
    
    async def async_step_model_parameters(self, user_input: dict[str, any] | None = None) -> config_entries.ConfigFlowResult:
        """Optional step to configure model parameters.

        Args:
            user_input (dict | None): Dictionary containing the user input or None.
        Returns:
            ConfigFlowResult: Shows the form or creates the config entry.
        """
        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_authorization()

        # Define the data schema for the form
        STEP_USER_DATA_SCHEMA = vol.Schema({
            vol.Required(CONF_MAX_TOKENS, default=DEFAULT_MAX_TOKENS): NumberSelector({"min": 1, "max": 1000}),
            vol.Required(CONF_CREATIVITY, default=DEFAULT_CREATIVITY): NumberSelector({"min": 0, "step": 0.01, "mode": "slider", "max": 1}),
            vol.Optional(CONF_DIVERSITY, default=DEFAULT_DIVERSITY): NumberSelector({"min": 0, "step": 0.01, "mode": "slider", "max": 1}),
            vol.Optional(CONF_FREQUENCY_PENALTY, default=DEFAULT_FREQUENCY_PENALTY): NumberSelector({"min": 0, "step": 0.01, "mode": "slider", "max": 1}),
        })

        return self.async_show_form(step_id="model_parameters", data_schema=STEP_USER_DATA_SCHEMA)
    
    
    async def async_step_authorization(self, user_input: dict[str, any] | None = None) -> config_entries.ConfigFlowResult:
        """Final step of the flow: prompts the user for authorization.

        Args:
            user_input (dict | None): Dictionary containing the user input or None.
        Returns:
            ConfigFlowResult: Shows the form or creates the config entry.
        """
        
        if user_input is not None:
            self.data.update(user_input)
            return self.async_create_entry(title=f"Perplexity Assistant - {self.data[CONF_LANGUAGE]}{self.data[CONF_API_KEY][-4:]}", data=self.data)
        
        DEFAULT_PROVIDER = tts.async_default_engine(self.hass)

        tts_engine_selector = TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.TEXT,
                autocomplete="off",
            )
        )

        # Define the data schema for the form
        STEP_USER_DATA_SCHEMA = vol.Schema({
            vol.Optional(CONF_ALLOW_ENTITIES_ACCESS, default=DEFAULT_ALLOW_ENTITIES_ACCESS): BooleanSelector(),
            vol.Required(CONF_ENTITIES_SUMMARY_REFRESH_RATE, default=DEFAULT_ENTITIES_SUMMARY_REFRESH_RATE): NumberSelector({"min": 5, "step": 5, "mode": "box", "unit_of_measurement": "s", "max": 1800}),
            vol.Optional(CONF_ALLOW_ACTIONS_ON_ENTITIES, default=DEFAULT_ALLOW_ACTIONS_ON_ENTITIES): BooleanSelector(),
            vol.Optional(CONF_ENABLE_RESPONSE_ON_SPEAKERS, default=DEFAULT_ENABLE_RESPONSE_ON_SPEAKERS): BooleanSelector(),
            vol.Required(CONF_TTS_ENGINE, default=DEFAULT_PROVIDER): tts_engine_selector,
            vol.Optional(CONF_NOTIFY_RESPONSE, default=DEFAULT_NOTIFY_RESPONSE): BooleanSelector(),
            vol.Optional(CONF_ENABLE_WEBSEARCH, default=DEFAULT_ENABLE_WEBSEARCH): BooleanSelector(),
        })
        
        return self.async_show_form(step_id="authorization", data_schema=STEP_USER_DATA_SCHEMA, last_step=True,)

    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return PerplexityOptionsFlowHandler()
    
    
class PerplexityOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Perplexity Assistant options."""

    async def async_step_init(self, user_input=None):
        """Main options menu."""
        if user_input is not None:
            if user_input["menu"] == "api":
                return await self.async_step_api()
            if user_input["menu"] == "model":
                return await self.async_step_model()
            if user_input["menu"] == "authorization":
                return await self.async_step_authorization()
            if user_input["menu"] == "model_parameters":
                return await self.async_step_model_parameters()

        selector = SelectSelector(
            SelectSelectorConfig(
                options=['api', 'model', 'model_parameters', 'authorization'],
                mode=SelectSelectorMode.DROPDOWN,
                translation_key="menu"
            )
        )
        
        menu_schema = vol.Schema({
            vol.Required("menu"): selector
        })

        return self.async_show_form(
            step_id="init",
            data_schema=menu_schema,
        )

    async def async_step_api(self, user_input: dict[str, any] | None = None) -> config_entries.ConfigFlowResult:
        """Manage the options step.

        Args:
            user_input (dict | None): Dictionary containing the user input or None.
        Returns:
            ConfigFlowResult: Shows the form or creates the options entry.
        """
        errors = {}

        # If the user has submitted the form
        if user_input is not None:
            api_key: str = user_input.get(CONF_API_KEY, "")

            # Check if the API key has a valid format
            if not api_key.startswith("pplx-"):
                errors[CONF_API_KEY] = "invalid_api_key"
            elif len(api_key) != 53:
                errors[CONF_API_KEY] = "invalid_api_key_length"
            else:
                options = dict(self.config_entry.options)
                options.update(user_input)
                return self.async_create_entry(title="", data=options)

        text_selector = TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD,
                autocomplete="off",
            )
        )
        
        # Show the form to update options
        current_api_key: str = self.config_entry.options.get(CONF_API_KEY, self.config_entry.data.get(CONF_API_KEY, ""))

        # Define the options schema with current values as defaults
        options_schema = vol.Schema({
            vol.Required(CONF_API_KEY, default=current_api_key): text_selector,
        })

        return self.async_show_form(step_id="api", data_schema=options_schema, errors=errors,)
    
    async def async_step_model(self, user_input: dict[str, any] | None = None) -> config_entries.ConfigFlowResult:
        """Manage the options step.

        Args:
            user_input (dict | None): Dictionary containing the user input or None.
        Returns:
            ConfigFlowResult: Shows the form or creates the options entry.
        """
        # Show the form to update options
        current_model: str = self.config_entry.options.get(CONF_MODEL, self.config_entry.data.get(CONF_MODEL, DEFAULT_MODEL))
        current_language: str = self.config_entry.options.get(CONF_LANGUAGE, self.config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
        current_custom_system_prompt: str = self.config_entry.options.get(CONF_CUSTOM_SYSTEM_PROMPT, self.config_entry.data.get(CONF_CUSTOM_SYSTEM_PROMPT, ""))

        text_selector = TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.TEXT,
                autocomplete="off",
                multiline=True,
            )
        )
        
        # Define the options schema with current values as defaults
        options_schema = vol.Schema({
            vol.Required(CONF_LANGUAGE, default=current_language): SelectSelector(SelectSelectorConfig(options=SUPPORTED_LANGUAGES, mode=SelectSelectorMode.DROPDOWN)),
            vol.Required(CONF_MODEL, default=current_model): SelectSelector(SelectSelectorConfig(options=SUPPORTED_MODELS, mode=SelectSelectorMode.DROPDOWN)),
            vol.Optional(CONF_CUSTOM_SYSTEM_PROMPT, default=current_custom_system_prompt): text_selector,
        })
        
        if user_input is not None:
            if len(user_input.get(CONF_CUSTOM_SYSTEM_PROMPT, "")) > 250:
                return self.async_show_form(
                    step_id="model",
                    data_schema=options_schema,
                    errors={CONF_CUSTOM_SYSTEM_PROMPT: "max_length_exceeded"},
                )
            
            
            options = dict(self.config_entry.options)
            options.update(user_input)
            return self.async_create_entry(title="", data=options)

        return self.async_show_form(step_id="model", data_schema=options_schema,)
    
    async def async_step_model_parameters(self, user_input: dict[str, any] | None = None) -> config_entries.ConfigFlowResult:
        """Manage the options step.

        Args:
            user_input (dict | None): Dictionary containing the user input or None.
        Returns:
            ConfigFlowResult: Shows the form or creates the options entry.
        """
        # Show the form to update options
        current_max_tokens: str = self.config_entry.options.get(CONF_MAX_TOKENS, self.config_entry.data.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS))
        current_creativity: str = self.config_entry.options.get(CONF_CREATIVITY, self.config_entry.data.get(CONF_CREATIVITY, DEFAULT_CREATIVITY))
        current_diversity: str = self.config_entry.options.get(CONF_DIVERSITY, self.config_entry.data.get(CONF_DIVERSITY, DEFAULT_DIVERSITY))
        current_frequency_penalty: str = self.config_entry.options.get(CONF_FREQUENCY_PENALTY, self.config_entry.data.get(CONF_FREQUENCY_PENALTY, DEFAULT_FREQUENCY_PENALTY))
        
        # Define the options schema with current values as defaults
        options_schema = vol.Schema({
            vol.Required(CONF_MAX_TOKENS, default=current_max_tokens): NumberSelector({"min": 1, "max": 1000}),
            vol.Required(CONF_CREATIVITY, default=current_creativity): NumberSelector({"min": 0, "step": 0.01, "mode": "slider", "max": 1}),
            vol.Optional(CONF_DIVERSITY, default=current_diversity): NumberSelector({"min": 0, "step": 0.01, "mode": "slider", "max": 1}),
            vol.Optional(CONF_FREQUENCY_PENALTY, default=current_frequency_penalty): NumberSelector({"min": 0, "step": 0.01, "mode": "slider", "max": 1}),
        })
        
        if user_input is not None:
            options = dict(self.config_entry.options)
            options.update(user_input)
            return self.async_create_entry(title="", data=options)

        return self.async_show_form(step_id="model_parameters", data_schema=options_schema,)
    
    async def async_step_authorization(self, user_input: dict[str, any] | None = None) -> config_entries.ConfigFlowResult:
        """Manage the options step.

        Args:
            user_input (dict | None): Dictionary containing the user input or None.
        Returns:
            ConfigFlowResult: Shows the form or creates the options entry.
        """        
        if user_input is not None:
            options = dict(self.config_entry.options)
            options.update(user_input)
            return self.async_create_entry(title="", data=options)
            

        # Show the form to update options
        DEFAULT_PROVIDER = tts.async_default_engine(self.hass)
        current_enable_websearch: bool = self.config_entry.options.get(CONF_ENABLE_WEBSEARCH, self.config_entry.data.get(CONF_ENABLE_WEBSEARCH, DEFAULT_ENABLE_WEBSEARCH))
        current_allow_entities_access: bool = self.config_entry.options.get(CONF_ALLOW_ENTITIES_ACCESS, self.config_entry.data.get(CONF_ALLOW_ENTITIES_ACCESS, DEFAULT_ALLOW_ENTITIES_ACCESS))
        current_allow_actions_on_entities: bool = self.config_entry.options.get(CONF_ALLOW_ACTIONS_ON_ENTITIES, self.config_entry.data.get(CONF_ALLOW_ACTIONS_ON_ENTITIES, DEFAULT_ALLOW_ACTIONS_ON_ENTITIES))
        current_notify_response: bool = self.config_entry.options.get(CONF_NOTIFY_RESPONSE, self.config_entry.data.get(CONF_NOTIFY_RESPONSE, DEFAULT_NOTIFY_RESPONSE))
        current_enable_response_on_speakers: bool = self.config_entry.options.get(CONF_ENABLE_RESPONSE_ON_SPEAKERS, self.config_entry.data.get(CONF_ENABLE_RESPONSE_ON_SPEAKERS, DEFAULT_ENABLE_RESPONSE_ON_SPEAKERS))
        current_entities_summary_refresh_rate: int = self.config_entry.options.get(CONF_ENTITIES_SUMMARY_REFRESH_RATE, self.config_entry.data.get(CONF_ENTITIES_SUMMARY_REFRESH_RATE, DEFAULT_ENTITIES_SUMMARY_REFRESH_RATE))
        current_tts_engine: str = self.config_entry.options.get(CONF_TTS_ENGINE, self.config_entry.data.get(CONF_TTS_ENGINE, DEFAULT_PROVIDER))

        tts_engine_selector = TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.TEXT,
                autocomplete="off",
            )
        )

        # Define the options schema with current values as defaults
        options_schema = vol.Schema({
            vol.Optional(CONF_ALLOW_ENTITIES_ACCESS, default=current_allow_entities_access): BooleanSelector(),
            vol.Required(CONF_ENTITIES_SUMMARY_REFRESH_RATE, default=current_entities_summary_refresh_rate): NumberSelector({"min": 5, "step": 5, "mode": "box", "unit_of_measurement": "s", "max": 1800}),
            vol.Optional(CONF_ALLOW_ACTIONS_ON_ENTITIES, default=current_allow_actions_on_entities): BooleanSelector(),
            vol.Optional(CONF_ENABLE_RESPONSE_ON_SPEAKERS, default=current_enable_response_on_speakers): BooleanSelector(),
            vol.Required(CONF_TTS_ENGINE, default=current_tts_engine): tts_engine_selector,
            vol.Optional(CONF_NOTIFY_RESPONSE, default=current_notify_response): BooleanSelector(),
            vol.Optional(CONF_ENABLE_WEBSEARCH, default=current_enable_websearch): BooleanSelector(),
        })

        return self.async_show_form(step_id="authorization", data_schema=options_schema,)
