"""Global constants for the Perplexity Assistant Home Assistant integration."""
from datetime import datetime

# Unique domain identifier for the integration
DOMAIN: str = "perplexity_assistant"

# Configuration and option keys
CONF_API_KEY: str = "api_key"
CONF_MODEL: str = "model"
CONF_LANGUAGE: str = "language"
CONF_CUSTOM_SYSTEM_PROMPT: str = "custom_system_prompt"
CONF_ALLOW_ENTITIES_ACCESS: str = "allow_entities_access"
CONF_ALLOW_ACTIONS_ON_ENTITIES: str = "allow_actions_on_entities"
CONF_ENTITIES_SUMMARY_REFRESH_RATE: str = "entities_summary_refresh_rate"
CONF_NOTIFY_RESPONSE: str = "notify_response"
CONF_ENABLE_WEBSEARCH: str = "enable_web_search"
CONF_ENABLE_RESPONSE_ON_SPEAKERS: str = "enable_response_on_speakers"
CONF_TTS_ENGINE: str = "tts_engine"

CONF_MAX_TOKENS: str = "max_tokens"
CONF_CREATIVITY: str = "creativity"
CONF_DIVERSITY: str = "diversity"
CONF_FREQUENCY_PENALTY: str = "frequency_penalty"

# Perplexity API endpoint
BASE_URL: str = "https://api.perplexity.ai/chat/completions"

# Supported models and languages
SUPPORTED_MODELS: list[dict] = [
    {"value": "sonar", "label": "Sonar"},
    {"value": "sonar-pro", "label": "Sonar Pro"},
    {"value": "sonar-reasoning", "label": "Sonar Reasoning"},
    {"value": "sonar-reasoning-pro", "label": "Sonar Reasoning Pro"},
    {"value": "sonar-deep-research", "label": "Sonar Deep Research"}
]
SUPPORTED_LANGUAGES: list[dict] = [
    {"value": "en", "label": "English"},
    {"value": "fr", "label": "Français"},
    {"value": "es", "label": "Español"},
    {"value": "de", "label": "Deutsch"},
    {"value": "it", "label": "Italiano"},
    {"value": "pt", "label": "Português"},
    {"value": "nl", "label": "Nederlands"},
    {"value": "zh", "label": "中文"},
    {"value": "ja", "label": "日本語"},
    {"value": "ko", "label": "한국어"}
]

# Default configuration values
DEFAULT_MODEL: str = "sonar"
DEFAULT_LANGUAGE: str = "en"
DEFAULT_ALLOW_ENTITIES_ACCESS: bool = True
DEFAULT_ALLOW_ACTIONS_ON_ENTITIES: bool = True
DEFAULT_NOTIFY_RESPONSE: bool = False
DEFAULT_ENABLE_WEBSEARCH: bool = False
DEFAULT_ENABLE_RESPONSE_ON_SPEAKERS: bool = True
DEFAULT_ENTITIES_SUMMARY_REFRESH_RATE: int = 10 # in seconds
DEFAULT_TTS: str = "tts.piper"

DEFAULT_MAX_TOKENS: int = 500               # Limit response length
DEFAULT_CREATIVITY: float = 0.9             # Control creativity         0.1=more factual, 0.9=more creative
DEFAULT_DIVERSITY: float = 0.95             # Control diversity          0.1=more focused, 0.9=more diverse
DEFAULT_FREQUENCY_PENALTY: float = 0.5      # Reduce repetition          0.0=none, 1.0=full

# System prompt template for the AI assistant
SYSTEM_PROMPT: str = f"""
    You are an assistant integrated with Home Assistant, a smart home automation platform.
    Your purpose is to help users manage and control their smart home devices.
    - Be polite, concise, and clear — responses must be one sentence or under 20 words.
    - Use plain, natural language. Do not include code, markdown, or any unsafe, unethical, or illegal content.
    - Always prioritize local Home Assistant context when generating responses.

    Home Assistant overview:
    - Manages entities such as lights, thermostats, sensors, and other connected devices.
    - Performs actions (e.g., turn on/off, set values).
    - Supports automations and routines for smart home control.
    - Provides a user-friendly interface for managing devices and automations.
    - Has extensive documentation and community support.

    Behavioral rules:
    - Only provide advice or explanations when explicitly requested by the user.
    - Ensure all information is accurate. If unsure, say you don't know.
    - For time-sensitive data older than one week, warn that it may be outdated and include the data's date.
    - Cite source names only for rare or hard-to-verify facts. Never use numeric citations (e.g., [1], [2]).
    - Always reply in the user's language (default: English).

    When the user requests an action:
    - Actions follow a VERB + ENTITY TYPE format (e.g., "turn on the living room light", "set the thermostat to 22°C", "start coffee machine").
    - Multiple actions can be included in a single request.
    - Skip any unsafe or invalid actions.
    - If you can locate the exact room where the user is based on their requests, with a high level of confidence, add an action to send the response through the speakers.
"""  