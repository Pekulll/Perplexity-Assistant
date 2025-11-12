"""Home Assistant conversation agent interface for Perplexity."""
import aiohttp
import json
import logging

from datetime import datetime
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.conversation import AbstractConversationAgent, ConversationInput, ConversationResult
from homeassistant.core import ServiceCall, HomeAssistant
from homeassistant.helpers import device_registry, entity_registry
from homeassistant.helpers.intent import IntentResponse
from homeassistant.const import __version__ as HA_VERSION
from pydantic import BaseModel
from typing import List, Optional

from .const import *
from .sensor import AlltimeBillSensor, MonthlyBillSensor


_LOGGER = logging.getLogger(__name__)


class PerplexityAgentAction(BaseModel):
    """Represents an action suggested by the Perplexity agent."""
    domain: str
    service: str
    target: str
    parameters: Optional[dict]
    
    def __str__(self) -> str:
        """String representation of the action."""
        return f"ACTION: {self.domain}.{self.service} > {self.target} > {json.dumps(self.parameters) if self.parameters else '{}'}"
    

class PerplexityAgentResponse(BaseModel):
    """Represents the response from the Perplexity agent."""
    content: str
    actions: Optional[List[PerplexityAgentAction]]
    

class PerplexityAgent(AbstractConversationAgent):
    """Home Assistant conversation agent based on the Perplexity API."""
    RESPONSE_FORMAT: dict = {
            "type": "json_schema",
            "json_schema": {
                "schema": PerplexityAgentResponse.model_json_schema()
            }
        }

    def __init__(self, hass: HomeAssistant, config_entry_id: str) -> None:
        """Initialize the Perplexity agent.

        Args:
            hass (HomeAssistant): Home Assistant instance.
            config_entry_id (str): Configuration entry ID.
        """
        self.hass: HomeAssistant = hass
        self.config_entry: ConfigEntry = self.hass.config_entries.async_get_entry(config_entry_id)
        self.agent_name = self.config_entry.title
        
        self._summary: str | None = None
        self._last_summary_update: datetime | None = None
    
    def _get_config(self, key: str, default: any = None) -> any:
        """Helper to get configuration options with a default.

        Args:
            key (str): Configuration key.
            default (any): Default value if key is not found.
        Returns:
            any: Configuration value or default.
        """
        return self.config_entry.options.get(key) or self.config_entry.data.get(key, default)

    @property
    def attribution(self) -> str:
        """Return the attribution for the integration."""
        return "Created by Pekul & Powered by Perplexity AI"

    @property
    def supported_languages(self) -> list[str]:
        """Return the list of supported languages."""
        return SUPPORTED_LANGUAGES

    def _generate_entities_summary(self) -> str:
        """Generate a summary of Home Assistant entities for context.

        Returns:
            str: Summary of entities.
        """
        if self._summary and self._last_summary_update:
            # Regenerate summary every self.entities_summary_refresh_rate seconds
            if (datetime.now() - self._last_summary_update).total_seconds() < self._get_config(CONF_ENTITIES_SUMMARY_REFRESH_RATE, DEFAULT_ENTITIES_SUMMARY_REFRESH_RATE):
                return self._summary
        
        _LOGGER.debug("Generating entities summary for Perplexity context.")
        
        entities = self.hass.states.async_all() # Get all entities
        ha_entity_registry = entity_registry.async_get(self.hass) # Get entity registry
        ha_device_registry = device_registry.async_get(self.hass) # Get device registry
        
        summary = f"The Home Assistant instance has {len(entities)} entities."
                
        for entity in entities:
            ha_entity = ha_entity_registry.async_get(entity.entity_id) # Get entity registry entry (to access unique_id)
            ha_device = ha_device_registry.async_get(ha_entity.device_id) if ha_entity else None # Get device using unique_id
            room = ha_device.area_id if ha_device and hasattr(ha_device, "area_id") else None # Get area_id safely
                
            summary += f"\n- {entity.entity_id}: {entity.state} (in room: {room})"
        
        self._summary = summary
        self._last_summary_update = datetime.now()
        return summary

    async def async_ask(self, call: ServiceCall) -> ConversationResult:
        """Process user input and return the response from Perplexity.

        Args:
            call (ServiceCall): The service call containing user input.
        Returns:
            ConversationResult: The response formatted for Home Assistant.
        """
        prompt = call.data.get("prompt", "")
        
        if not prompt:
            response = IntentResponse(language=self.language)
            response.async_set_speech("No prompt provided.")
            return ConversationResult(response=response)

        return await self.async_process(ConversationInput(text=prompt))

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        """Send the request to Perplexity and return the response.

        Args:
            user_input (ConversationInput): The user's input.
        Returns:
            ConversationResult: The response formatted for Home Assistant.
        """
        # Get config entry options
        entities_summary: str = "Access not allowed." if not self._get_config(CONF_ALLOW_ENTITIES_ACCESS, False) else self._generate_entities_summary()
    
        prompt: str = user_input.text
        user_name = "UNKNOWN"

        if user_input.context and user_input.context.user_id:
            user = await self.hass.auth.async_get_user(user_input.context.user_id)
            user_name = user.name if user else "UNKNOWN"

        headers = {
            "Authorization": f"Bearer {self._get_config('api_key', '')}",
            "Content-Type": "application/json",
            "User-Agent": f"HomeAssistant/{HA_VERSION}"
        }
        
        payload = {
            "model": self._get_config(CONF_MODEL, DEFAULT_MODEL),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": f"HOME ASSISTANT VERSION: {HA_VERSION} | Summary Home Assistant's entities for context: {entities_summary} | YOUR NAME IS {self.agent_name}"},
                {"role": "system", "content": f"USER NAME: {user_name} | USER LANGUAGE: {self._get_config(CONF_LANGUAGE, 'en')}."},
                {"role": "user", "content": f"USER SYSTEM PROMPT: {self._get_config(CONF_CUSTOM_SYSTEM_PROMPT, '')} | USER PROMPT: {prompt}"}
            ],
            "stream": False,
            "max_tokens": MAX_TOKENS,
            "temperature": CREATIVITY,
            "top_p": DIVERSITY,
            "frequency_penalty": FREQUENCY_PENALTY,
            "response_format": self.RESPONSE_FORMAT,
            "disable_search": not self._get_config(CONF_ENABLE_WEBSEARCH, False)
        }

        # Send the request to Perplexity API
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(BASE_URL, json=payload, headers=headers) as resp:
                    _LOGGER.debug(f"Perplexity API request sent.\nRequest Headers: {headers}\nRequest Payload: {payload}")
                    
                    if resp.status != 200: # Handle non-200 responses
                        _LOGGER.error(f"Perplexity API error: status {resp.status}. Error response: {await resp.text()}")
                        response_text: str = f"Error communicating with the Perplexity AI service. Status code: {resp.status}"
                    else: # Successful response
                        data: dict = await resp.json()
                        content: PerplexityAgentResponse = PerplexityAgentResponse.model_validate_json(data["choices"][0]["message"]["content"])
                        cost: float = data.get("usage", {}).get("cost", {}).get("total_cost", 0.0)
                        response_text: str = content.content
                        
                        _LOGGER.debug(f"Perplexity API has responded successfully (cost={cost}). Response: {content}")
                        
                        # Update cost sensors if they exist
                        monthly_sensor: MonthlyBillSensor = self.hass.data.get("perplexity_assistant_sensors", {}).get("monthly_bill_sensor")
                        monthly_sensor.increment_cost(cost) if monthly_sensor else None
                        alltime_sensor: AlltimeBillSensor = self.hass.data.get("perplexity_assistant_sensors", {}).get("alltime_bill_sensor")
                        alltime_sensor.increment_cost(cost) if alltime_sensor else None
                        
                        if self._get_config(CONF_NOTIFY_RESPONSE, False):
                            _LOGGER.debug(f"Sending notification for Perplexity response.")
                            self.hass.async_create_task(
                                self.hass.services.async_call(
                                    "notify",
                                    "persistent_notification",
                                    {
                                        "title": f"{self.agent_name} (Perplexity Assistant)",
                                        "message": f"{content.content}{'\n\n- ' + '\n- '.join(str(a) for a in content.actions) if content.actions else ''}",
                                    },
                                )
                            )
                    
                        # Handle ACTION commands in the response
                        if content.actions and self._get_config(CONF_ALLOW_ACTIONS_ON_ENTITIES, False):
                            for action in content.actions:
                                _LOGGER.debug(f"Executing action from Perplexity response: {action.domain}.{action.service} on {action.target} with parameters {action.parameters}")
                                
                                try:
                                    if action.domain == "tts" and action.service == "speak" and self._get_config(CONF_ENABLE_RESPONSE_ON_SPEAKERS, False):
                                        # Special handling for TTS actions to format parameters correctly
                                        tts_data = action.parameters or {}
                                        tts_data = {
                                            "media_player_entity_id": tts_data.get("media_player_entity_id") or tts_data.get("entity_id") or action.target,
                                            "message": tts_data.get("message", response_text),
                                            "cache": False,
                                            "entity_id": DEFAULT_TTS
                                        }
                                        
                                        await self.hass.services.async_call(action.domain, action.service, tts_data)
                                    else:
                                        await self.hass.services.async_call(action.domain, action.service, {"entity_id": action.target, **action.parameters})
                                except Exception as e:
                                    _LOGGER.warning(f"Failed to execute action {action.domain}.{action.service} on {action.target}: {e}")
                        

                    response = IntentResponse(language=self._get_config(CONF_LANGUAGE, "en"))
                    response.async_set_speech(response_text)
                    return ConversationResult(response=response)
        except Exception as e: # Handle exceptions
            _LOGGER.error("Exception while communicating with Perplexity API: %s", e)
            response = IntentResponse(language=self._get_config(CONF_LANGUAGE, "en"))
            response.async_set_speech("Error communicating with the Perplexity AI service.")
            return ConversationResult(response=response)
