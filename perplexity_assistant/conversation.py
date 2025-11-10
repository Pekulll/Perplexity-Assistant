"""Home Assistant conversation agent interface for Perplexity."""
import logging
from homeassistant.components.conversation import AbstractConversationAgent, ConversationInput, ConversationResult
from homeassistant.core import ServiceCall
from homeassistant.helpers.intent import IntentResponse
import voluptuous as vol
import asyncio
import aiohttp
from datetime import datetime
from .const import BASE_URL, SUPPORTED_LANGUAGES, SYSTEM_PROMPT

_LOGGER = logging.getLogger(__name__)

class PerplexityAgent(AbstractConversationAgent):
    """Home Assistant conversation agent based on the Perplexity API."""

    def __init__(self, hass, config_entry_id, session, api_key: str, model: str, language: str, notify_response: bool = False, custom_system_prompt: str = ""):
        """Initialize the Perplexity agent.

        Args:
            hass (HomeAssistant): Home Assistant instance.
            api_key (str): Perplexity API key.
            model (str): Model name (e.g. sonar-small, sonar-pro...).
        """
        self.hass = hass
        self.config_entry_id = config_entry_id
        self.api_key = api_key
        self.model = model
        self.language = language
        self.notify_response = notify_response
        self.custom_system_prompt = custom_system_prompt
        self.session = session

    @property
    def attribution(self):
        return "Created by Pekul & Powered by Perplexity AI"

    @property
    def supported_languages(self):
        # Perplexity supports multiple languages; here is only a sample list
        return SUPPORTED_LANGUAGES

    def _generate_entities_summary(self) -> str:
        """Generate a summary of Home Assistant entities for context.

        Returns:
            str: Summary of entities.
        """
        _LOGGER.debug("Generating entities summary for Perplexity context.")
        entities = self.hass.states.async_all()
        summary = f"The Home Assistant instance has {len(entities)} entities."
                
        for entity in entities:
            summary += f"\n- {entity.entity_id}: {entity.state}"
            
        return summary

    async def async_ask(self, call: ServiceCall) -> ConversationResult:
        """Process user input and return the response from Perplexity.

        Args:
            user_input (ConversationInput): The user's input.
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
        config_entry = self.hass.config_entries.async_get_entry(self.config_entry_id)
        entities_access = config_entry.options.get("allow_entities_access", False)
        action_on_entities = config_entry.options.get("allow_actions_on_entities", False)
        
        prompt = user_input.text
        entities_summary = "Access not allowed." if not entities_access else self._generate_entities_summary()

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

        # Requête HTTP asynchrone
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(BASE_URL, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        _LOGGER.error(f"Perplexity API error: status {resp.status}. Error response: {await resp.text()}")
                        content = f"Error communicating with the Perplexity AI service. Status code: {resp.status}"
                    else:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        cost = data.get("usage", {}).get("cost", {}).get("total_cost", 0.0)
                        
                        _LOGGER.debug(f"Perplexity API has responded successfully (cost={cost}). Response: {content}")
                        monthly_sensor = self.hass.data.get("perplexity_assistant_sensors", {}).get("monthly_bill_sensor")
                        alltime_sensor = self.hass.data.get("perplexity_assistant_sensors", {}).get("alltime_bill_sensor")
                        
                        monthly_sensor.increment_cost(cost) if monthly_sensor else None
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
                    if "ACTION:" in content and action_on_entities:
                        for line in content.splitlines():
                            if not line.startswith("ACTION:"):
                                continue
                            
                            action_part = line[len("ACTION: "):].split(" - ")
                            
                            if len(action_part) != 2:
                                _LOGGER.warning(f"Invalid ACTION format in response: {line}")
                                continue
                            
                            action, target = action_part[0].strip(), action_part[1].strip()
                            domain, service = action.split(".")
                            await self.hass.services.async_call(domain, service, {"entity_id": target})
                            # self.hass.async_create_task(self.hass.services.async_call(action,target,{},))

                    response = IntentResponse(language=self.language)
                    response.async_set_speech(content)
                    return ConversationResult(response=response)
        except Exception as e:
            _LOGGER.error("Exception while communicating with Perplexity API: %s", e)
            response = IntentResponse(language=self.language)
            response.async_set_speech("Error communicating with the Perplexity AI service.")
            return ConversationResult(response=response)
