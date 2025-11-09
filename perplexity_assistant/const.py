"""Global constants for the Perplexity Assistant Home Assistant integration."""

# Unique domain identifier for the integration
DOMAIN = "perplexity_assistant"

CONF_API_KEY = "api_key"
CONF_MODEL = "model"
CONF_LANGUAGE = "language"

BASE_URL = "https://api.perplexity.ai/chat/completions"
SUPPORTED_MODELS = [
    "sonar-small-online",
    "sonar-medium-online",
    "sonar-large-online",
    "gpt-5",
    "gpt-4",
    "gpt-3.5-turbo",
]
SUPPORTED_LANGUAGES = ["en", "fr", "es", "de", "it"]

DEFAULT_MODEL = "sonar-small-online"
DEFAULT_LANGUAGE = "en"