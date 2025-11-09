"""Config flow for Perplexity Assistant integration in Home Assistant."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_API_KEY, CONF_MODEL, CONF_LANGUAGE, DEFAULT_MODEL, DEFAULT_LANGUAGE, SUPPORTED_MODELS, SUPPORTED_LANGUAGES


# User input schema: only the API key is requested.
STEP_USER_DATA_SCHEMA = vol.Schema({
        vol.Required(
            "api_key",
            description="API Key for Perplexity AI. You can get it from: https://platform.perplexity.ai/"
        ): vol.All(str, vol.Length(min=53, max=53)),
        vol.Optional(
            "language",
            default=DEFAULT_LANGUAGE,
            description="Language for the conversation."
        ): vol.In(SUPPORTED_LANGUAGES),
        vol.Optional(
            "model",
            default=DEFAULT_MODEL,
            description="Model to use for the conversation."
        ): vol.In(SUPPORTED_MODELS),
    })

# Form texts (you can also put them in translations/<lang>/strings.json)
FORM_TITLE = "Perplexity Assistant"
FORM_DESCRIPTION = "Enter your Perplexity API Key. You can get it from: https://platform.perplexity.ai/"

class PerplexityConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow handler for configuration via the UI."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, any] | None = None):
        """First step of the flow: prompts the user for the API key.

        Args:
            user_input (dict | None): Dictionary containing the user input or None.
        Returns:
            ConfigFlowResult: Shows the form or creates the config entry.
        """
        errors = {}

        # If the user has submitted the form
        if user_input is not None:
            api_key = user_input.get("api_key", "")

            # Check if the API key has a valid format
            if not api_key.startswith("pplx-"):
                errors["api_key"] = "invalid_api_key"
            else:
                # If the API key is valid, create the config entry
                return self.async_create_entry(title="Perplexity Assistant", data=user_input)

        # Otherwise, show the form
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            last_step=True,
        )
    
class PerplexityOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Perplexity Assistant options."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow handler.

        Args:
            config_entry (ConfigEntry): The configuration entry.
        """
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, any] | None = None):
        """Manage the options step.

        Args:
            user_input (dict | None): Dictionary containing the user input or None.
        Returns:
            ConfigFlowResult: Shows the form or creates the options entry.
        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Show the form to update options
        current_model = self.config_entry.options.get(CONF_MODEL, DEFAULT_MODEL)
        current_language = self.config_entry.options.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)

        options_schema = vol.Schema({
            vol.Optional(
                CONF_MODEL,
                default=current_model,
                description="Model to use for the conversation."
            ): vol.In(MODEL_OPTIONS),
            vol.Optional(
                CONF_LANGUAGE,
                default=current_language,
                description="Language for the conversation."
            ): vol.In(LANG_OPTIONS),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
