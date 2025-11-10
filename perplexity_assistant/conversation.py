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

from perplexity_assistant.sensor import AlltimeBillSensor, MonthlyBillSensor

from .const import *


_LOGGER = logging.getLogger(__name__)

class PerplexityAgent(AbstractConversationAgent):
    """Home Assistant conversation agent based on the Perplexity API."""

    def __init__(self, hass: HomeAssistant, config_entry_id: str) -> None:
        """Initialize the Perplexity agent.

        Args:
            hass (HomeAssistant): Home Assistant instance.
            config_entry_id (str): Configuration entry ID.
        """
        self.hass: HomeAssistant = hass
        self.config_entry: ConfigEntry = self.hass.config_entries.async_get_entry(config_entry_id)
        self.api_key: str = self.config_entry.options.get(CONF_API_KEY, "")
        self.model: str = self.config_entry.options.get(CONF_MODEL, "sonar")
        self.language: str = self.config_entry.options.get(CONF_LANGUAGE, "en")
        self.notify_response: bool = self.config_entry.options.get(CONF_NOTIFY_RESPONSE, False)
        self.allow_entities_access: bool = self.config_entry.options.get(CONF_ALLOW_ENTITIES_ACCESS, False)
        self.allow_actions_on_entities: bool = self.config_entry.options.get(CONF_ALLOW_ACTIONS_ON_ENTITIES, False)
        self.custom_system_prompt: str = self.config_entry.options.get(CONF_CUSTOM_SYSTEM_PROMPT, "")
        
        self._summary: str | None = None
        self._last_summary_update: datetime | None = None

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
            # Regenerate summary every 24 hours
            if (datetime.now() - self._last_summary_update).total_seconds() < 86400:
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
        entities_summary: str = "Access not allowed." if not self.allow_entities_access else self._generate_entities_summary()
    
        prompt: str = user_input.text

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": f"Here is a summary of the Home Assistant entities for context: {entities_summary}"},
                {"role": "user", "content": f"USER SYSTEM PROMPT: {self.custom_system_prompt} | USER PROMPT: {prompt}"}
            ],
            "stream": False
        }

        # Send the request to Perplexity API
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(BASE_URL, json=payload, headers=headers) as resp:
                    if resp.status != 200: # Handle non-200 responses
                        _LOGGER.error(f"Perplexity API error: status {resp.status}. Error response: {await resp.text()}")
                        content: str = f"Error communicating with the Perplexity AI service. Status code: {resp.status}"
                    else: # Successful response
                        data: dict = await resp.json()
                        content: str = data["choices"][0]["message"]["content"]
                        cost: float = data.get("usage", {}).get("cost", {}).get("total_cost", 0.0)
                        
                        _LOGGER.debug(f"Perplexity API has responded successfully (cost={cost}). Response: {content}")
                        
                        # Update cost sensors if they exist
                        monthly_sensor: MonthlyBillSensor = self.hass.data.get("perplexity_assistant_sensors", {}).get("monthly_bill_sensor")
                        monthly_sensor.increment_cost(cost) if monthly_sensor else None
                        alltime_sensor: AlltimeBillSensor = self.hass.data.get("perplexity_assistant_sensors", {}).get("alltime_bill_sensor")
                        alltime_sensor.increment_cost(cost) if alltime_sensor else None
                        
                        if self.notify_response:
                            self.hass.async_create_task(
                                self.hass.services.async_call(
                                    "notify",
                                    "persistent_notification",
                                    {
                                        "title": "Perplexity Assistant",
                                        "message": content,
                                    },
                                )
                            )
                    
                    # Handle ACTION commands in the response
                    if "ACTION:" in content and self.allow_actions_on_entities:
                        for line in content.splitlines():
                            if not line.startswith("ACTION:"):
                                continue
                            
                            action_part: list[str] = line[len("ACTION: "):].split(" - ") # Split into action, target, parameters
                            
                            if len(action_part) < 2: # Invalid format
                                _LOGGER.warning(f"Invalid ACTION format in response: {line}")
                                continue
                            
                            action: str = action_part[0].strip() # Get action
                            target: str = action_part[1].strip() # Get target
                            parameters: dict = json.loads(action_part[2]) if len(action_part) > 2 else {} # Get parameters if present
                            domain, service = action.split(".") # Split action into domain and service
                            await self.hass.services.async_call(domain, service, {"entity_id": target, **parameters})

                    response = IntentResponse(language=self.language)
                    response.async_set_speech(content)
                    return ConversationResult(response=response)
        except Exception as e: # Handle exceptions
            _LOGGER.error("Exception while communicating with Perplexity API: %s", e)
            response = IntentResponse(language=self.language)
            response.async_set_speech("Error communicating with the Perplexity AI service.")
            return ConversationResult(response=response)
