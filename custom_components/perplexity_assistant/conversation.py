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
from typing import List, Optional, Any

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
    
    def _get_config(self, key: str, default: Any = None) -> Any:
        """Helper to get configuration options with a default.

        Args:
            key (str): Configuration key.
            default (any): Default value if key is not found.
        Returns:
            any: Configuration value or default.
        """
        return self.config_entry.options.get(key, self.config_entry.data.get(key, default))

    @property
    def attribution(self) -> str:
        """Return the attribution for the integration."""
        return "Created by Pekul & Powered by Perplexity AI"

    @property
    def supported_languages(self) -> list[str]:
        """Return the list of supported languages."""
        return [lang['value'] for lang in SUPPORTED_LANGUAGES]

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


    async def _async_send_request(self, user_messages: list[dict], username: str = "UNKNOWN", override_model: str | None = None, force_websearch_access: bool = False) -> dict:
        """Send a request to the Perplexity API.

        Args:
            messages (list[dict]): The request payload.
            username (str): The name of the user making the request.
            force_web_search_access (bool): Whether to force web search access.
        Returns:
            dict: The response from the Perplexity API.
        """
        headers = {
            "Authorization": f"Bearer {self._get_config('api_key', '')}",
            "Content-Type": "application/json",
            "User-Agent": f"HomeAssistant/{HA_VERSION}"
        }
        
        entities_summary: str = "Access not allowed." if not self._get_config(CONF_ALLOW_ENTITIES_ACCESS, DEFAULT_ALLOW_ENTITIES_ACCESS) else self._generate_entities_summary()
        
        SYSTEM_STATUS = f"""
            DATE & TIME: {datetime.now()}
            HOME ASSISTANT VERSION: {HA_VERSION}
            ENTITIES: {entities_summary}
            YOUR NAME IS {self.agent_name}
            AUTHORIZATIONS
                - enable_vocal_notifications={self._get_config(CONF_ENABLE_RESPONSE_ON_SPEAKERS, DEFAULT_ENABLE_RESPONSE_ON_SPEAKERS)}
                - enable_actions_on_entities={self._get_config(CONF_ALLOW_ACTIONS_ON_ENTITIES, DEFAULT_ALLOW_ACTIONS_ON_ENTITIES)}
            USER NAME: {username}
            USER LANGUAGE: {self._get_config(CONF_LANGUAGE, 'en')}
            """
        
        messages = [ {"role": "system", "content": SYSTEM_PROMPT}, {"role": "system", "content": SYSTEM_STATUS} ]
        messages.extend(user_messages)
        
        payload = {
            "model": override_model if override_model else self._get_config(CONF_MODEL, DEFAULT_MODEL),
            "messages": messages,
            "stream": False,
            "max_tokens": self._get_config(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS),
            "temperature": self._get_config(CONF_CREATIVITY, DEFAULT_CREATIVITY),
            "top_p": self._get_config(CONF_DIVERSITY, DEFAULT_DIVERSITY),
            "frequency_penalty": self._get_config(CONF_FREQUENCY_PENALTY, DEFAULT_FREQUENCY_PENALTY),
            "response_format": self.RESPONSE_FORMAT,
            "disable_search": not self._get_config(CONF_ENABLE_WEBSEARCH, DEFAULT_ENABLE_WEBSEARCH) and not force_websearch_access
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(BASE_URL, json=payload, headers=headers) as resp:
                    _LOGGER.debug(f"Perplexity API raw request sent.\nRequest Headers: {headers}\nRequest Payload: {payload}")
                    
                    if resp.status != 200:
                        _LOGGER.error(f"Perplexity API error: status {resp.status}. Error response: {await resp.text()}")
                        return {"error": f"Status code: {resp.status}"}
                    
                    data: dict = await resp.json()
                    _LOGGER.debug(f"Perplexity API raw response received: {data}")
                    return data
        except Exception as e:
            _LOGGER.error("Exception while communicating with Perplexity API: %s", e)
            return {"error": str(e)}


    async def _execute_action(self, action: PerplexityAgentAction, response_text: str = "") -> None:
        """Execute a given action from the Perplexity response.
        
        Args:
            action (PerplexityAgentAction): The action to execute.
            response_text (str): The main response text from Perplexity.
        """
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
                params = action.parameters or {}
                await self.hass.services.async_call(action.domain, action.service, {"entity_id": action.target, **params})
        except Exception as e:
            _LOGGER.warning(f"Failed to execute action {action.domain}.{action.service} on {action.target}: {e}")


    def _process_response(self, data: dict, execute_actions: bool = True, force_actions_execution: bool = False) -> dict:
        """Process the raw response from Perplexity API.
        Executes any actions if present and authorized to do so.

        Args:
            data (dict): The raw response data.
            execute_actions (bool): Whether to execute actions in the response. DOES NOT OVERWRITE CONFIG SETTING.
        Returns:
            dict: Processed response with keys 'response', 'actions', 'error', and 'cost'.
        """
        if "error" in data:
            return {"response": "Error communicating with the Perplexity AI service.", "error": data['error'], "cost": 0.0}
        
        try:
            content: PerplexityAgentResponse = PerplexityAgentResponse.model_validate_json(data["choices"][0]["message"]["content"])
            cost: float = data.get("usage", {}).get("cost", {}).get("total_cost", 0.0)
            response_text: str = content.content
            
            _LOGGER.debug(f"Perplexity API has responded successfully (cost={cost}). Response: {content}")
            
            # Update cost sensors if they exist
            monthly_sensor: MonthlyBillSensor = self.hass.data.get("perplexity_assistant_sensors", {}).get("monthly_bill_sensor")
            monthly_sensor.increment_cost(cost) if monthly_sensor else None
            alltime_sensor: AlltimeBillSensor = self.hass.data.get("perplexity_assistant_sensors", {}).get("alltime_bill_sensor")
            alltime_sensor.increment_cost(cost) if alltime_sensor else None
            
            # Send notification if enabled
            if self._get_config(CONF_NOTIFY_RESPONSE, DEFAULT_NOTIFY_RESPONSE):
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
            if (execute_actions and content.actions and self._get_config(CONF_ALLOW_ACTIONS_ON_ENTITIES, False)) or force_actions_execution:
                for action in content.actions:
                    # Schedule coroutine on HA's event loop (non-blocking)
                    self.hass.async_create_task(self._execute_action(action, response_text))

            return {"response": response_text, "error": None, "cost": cost}
        except Exception as e:
            _LOGGER.error(f"Error processing Perplexity response: {e}")
            return {"response": "Error processing response from the Perplexity AI service.", "error": str(e), "cost": 0.0}


    # Service call handler
    async def async_ask(self, call: ServiceCall) -> dict:
        """Service call handler.
        Send a request to Perplexity based on a service call.

        Args:
            call (ServiceCall): The service call containing user input.
        Returns:
            dict: The response from Perplexity: {"response": str, "actions": list, "error": str | None, "cost": float}.
        """
        prompt = call.data.get("prompt", "")
        model = call.data.get("model", None)
        execute_actions = call.data.get("execute_actions", True)
        force_actions_execution = call.data.get("force_actions_execution", False)
        enable_websearch = call.data.get("enable_websearch", None)
        response: dict = {"response": "", "actions": [], "error": None, "cost": 0.0}
        
        if not prompt:
            response['response'] = "No prompt provided."
            response['error'] = "No prompt provided."
        else:
            messages: list[dict] = [ {"role": "user", "content": f"USER SYSTEM PROMPT: {self._get_config(CONF_CUSTOM_SYSTEM_PROMPT, '')} | USER PROMPT: {prompt}"} ]
            data = await self._async_send_request(messages, "AUTOMATED SERVICE CALL", override_model=model, force_websearch_access=enable_websearch)
            response = self._process_response(data, execute_actions=execute_actions, force_actions_execution=force_actions_execution)
        
        self.hass.bus.async_fire(f"{DOMAIN}_response", {"response": response})
        return response


    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        """Process agent conversation input.
        Send a request to Perplexity based on user input.

        Args:
            user_input (ConversationInput): The user's input.
        Returns:
            ConversationResult: The response formatted for Home Assistant.
        """
        # Get config entry options
        prompt: str = user_input.text
        user_name = "UNKNOWN"

        if user_input.context and user_input.context.user_id:
            user = await self.hass.auth.async_get_user(user_input.context.user_id)
            user_name = user.name if user else "UNKNOWN"
        
        user_messages: list[dict] = [ {"role": "user", "content": f"USER SYSTEM PROMPT: {self._get_config(CONF_CUSTOM_SYSTEM_PROMPT, '')} | USER PROMPT: {prompt}"} ]
        data: dict = await self._async_send_request(user_messages, user_name)
        processed_response: dict = self._process_response(data)

        response = IntentResponse(language=self._get_config(CONF_LANGUAGE, DEFAULT_LANGUAGE))
        response.async_set_speech(processed_response.get("response", "Unknown response from Perplexity AI service."))
        return ConversationResult(response=response)
