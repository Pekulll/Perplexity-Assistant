<div align="center">
	<h1>Perplexity Assistant for Home Assistant</h1>
	<p>Your privacy-friendly AI helper powered by <a href="https://www.perplexity.ai/">Perplexity AI</a>, integrated directly into Home Assistant.</p>
	<p>
		<strong>Status:</strong> Experimental • <strong>Version:</strong> 1.2.0 • <strong>Integration Type:</strong> Service
	</p>
</div>

---

## ✨ Overview

Perplexity Assistant brings the Perplexity conversational AI experience into Home Assistant. It lets you:

* Ask natural language questions via the conversation system or a custom service (`perplexity_assistant.ask`).
* Get concise smart-home–oriented responses (with optional persistent notifications).
* Provide a custom system prompt to tune the assistant's behavior.
* Allow controlled access to entity states for contextual answers (optional).
* Allow the assistant to interact with your connected devices (e.g., lights, sensors).
* Track estimated API usage cost with two diagnostic sensors: Monthly cost and All‑time cost (placeholder until official billing endpoints become available).

> The assistant is designed to produce safe, short, clear responses suitable for voice TTS or dashboard display.

## 🚀 Features

| Feature | Description |
|---------|-------------|
| Conversation Agent | Registers as a Home Assistant conversation provider. |
| Service Call (`ask`) | Send prompts from script/automations + override model/websearch/action behavior per request. |
| Custom System Prompt | Override or extend built-in behavioral instructions. |
| Entity Context (optional) | Provides a summary of your entities to the model. |
| Action (optional) | Model can directly interact with your connected devices, if authorized to. |
| Notification (optional) | Responses as notifications. |
| Cost Sensors | Track monthly and all-time (approx) usage cost. |
| Options Flow | Modify API key, language, model, permissions post-install. |
| Multi‑Language UI | Translations: en, fr, es, de, it, pt, nl, zh, ja, ko. |

## 🧩 Requirements

Before installing:

* A valid Perplexity API Key (create one at: https://www.perplexity.ai/account/api/keys )
* Home Assistant 2025.1x or later (tested on recent versions supporting modern conversation API)
* Internet connectivity (cloud polling)

## 📦 Installation

1. Copy the `custom_components/perplexity_assistant` directory into your Home Assistant `config/custom_components` folder.
2. Restart Home Assistant.
3. Go to: Settings → Devices & Services → Add Integration → Search for "Perplexity Assistant".
4. Enter your API key and desired options.
5. Finish the flow — the integration sets up the conversation agent and sensors (if enabled).

### HACS (Planned)
HACS support is not yet published.

## ⚙️ Configuration (Initial Flow)

During setup you can specify:

* API Key (required, must start with `pplx-` and length 53)
* Language (default: `en`)
* Model (default: `sonar` — other options include `sonar-pro`, `sonar-reasoning`, etc.)
* Custom System Prompt (short textual instruction override, up to 250 chars)
* Model's parameters: max number of tokens, creativity, diversity, and frequency penalty
* Allow Entities Access (if enabled, entity states summary is sent to the model)
* Allow Actions On Entities (if enabled, Perplexity Assistant will be able to control your home)
* Allow Perplexity Assistant to give you vocal responses.
* TTS Engine to use.
* Enable Websearch (if enabled, Perplexity will be able to search information on internet)
* Notify Each Response (persistent notification of outputs)

## 🔁 Options Flow (Post-Install)

Navigate to the integration card → Configure to update the above fields. Changes take effect immediately after saving.

## 🗣️ Conversation Agent

You can use voice assistants or the built-in conversation interface. When registered, Perplexity Assistant becomes an available conversation agent.

## 🛎 Service: `perplexity_assistant.ask`

The integration exposes a single service to send ad‑hoc prompts with optional per‑call overrides. These overrides never persist — they apply only to that invocation.

| Field | Type | Required | Behavior |
|-------|------|----------|----------|
| `prompt` | string | yes | The natural language instruction/question. |
| `model` | string | no | Overrides configured model for this request. Falls back to integration model. |
| `enable_websearch` | boolean | no | Forces web search on/off regardless of global setting (true = enable; false = disable). |
| `execute_actions` | boolean | no | If true, any valid detected ACTION lines are executed (subject to global allow actions). |
| `force_actions_execution` | boolean | no | Hard override: executes detected actions even if global actions are disabled. Use cautiously. |

### Example: Developer Tools Service Call
```yaml
service: perplexity_assistant.ask
data:
  prompt: "Set the bedroom light to 50% and tell me current temperature"
  model: sonar-pro
  enable_websearch: false
  execute_actions: true
```

### Example: Script
```yaml
script:
  bedtime_assistant_query:
    sequence:
      - service: perplexity_assistant.ask
        data:
          prompt: "Dim lights in the bedroom and report motion sensors status"
          execute_actions: true
```

### Example: Automation Triggered by Time
```yaml
automation:
  - alias: Morning Summary
    trigger:
      - platform: time
        at: "07:30:00"
    action:
      - service: perplexity_assistant.ask
        data:
          prompt: "Give me a concise status of lights and climate; if heater is off and <20C turn it on"
          execute_actions: true
```

### Safety Notes
* Prefer `execute_actions: true` over `force_actions_execution: true` unless you fully trust model output.
* Always validate entity IDs exist before executing.
* Avoid sensitive operations (locks, alarms) until granular permission filtering is added.

## 🌐 Localization

Supported UI languages: **English (en), Français (fr), Español (es), Deutsch (de), Italiano (it), Português (pt), Nederlands (nl), 中文 (zh), 日本語 (ja), 한국어 (ko)**.

Adding a new language:
1. Copy an existing file in `custom_components/perplexity_assistant/translations/` (e.g., `en.json`) to `<lang>.json`.
2. Translate every value (do not leave English fallbacks unless absolutely necessary).
3. Ensure key parity with `strings.json` plus `selector` & `services` blocks.
4. Submit a PR; include proof-read localizations.

If a string is missing, Home Assistant will fall back to English.


## 💸 API cost
The following sheet represents the average cost by tested models:

| Model | Request Cost | Input Token Cost | Output Token Cost | Average Prompt Cost |
|-------|--------------|------------------|-------------------|---------------------|
| sonar | $0.005 | $0.000001 | $0.000001 | $0.00674 |
| sonar-pro | $0.006 | $0.000003 | $0.000015 | $0.0178 |

## 📊 Sensors

Two diagnostic sensors are created:

| Sensor Name | Description |
|-------------|-------------|
| `sensor.perplexity_monthly_bill` | Aggregates cost for current month (resets monthly). |
| `sensor.perplexity_bill` | Aggregates total cost across all usage. |

> Cost values are based on the `usage.cost.total_cost` field in responses. If API cost data changes or is unavailable these may remain 0 or inaccurate.

## 🔐 Privacy & Safety

* No entity states are sent unless you explicitly enable “Allow access to Home Assistant entities”.
* Action execution is opt-in; by default responses are inert.
* The actions to be performed are chosen so as not to harm any human or system.

## 🛠 Developer Guide

### Project Layout

```
custom_components/
	perplexity_assistant/
		translations/
			en.json				 # English translation
			fr.json				 # French translation
			...
		__init__.py              # Entry setup/unload, service registration, platform forwarding
		config_flow.py           # Config + options flow definitions
		const.py                 # Constants (models, languages, system prompt)
		conversation.py          # Conversation agent implementation
		sensor.py                # Diagnostic cost sensors (monthly + all-time)
		services.yaml            # Service schema definition
		strings.json             # UI strings for config/options flow
		manifest.json            # Integration metadata
hacs.json						 # Special manifest file for HACS
LICENSE							 # MIT License
README.md                		 # Documentation
```

### Key Components
* `async_setup_entry` registers the agent + service and forwards platforms.
* `conversation.py` implements `AbstractConversationAgent` with cost tracking and optional entity/context injection.
* `sensor.py` exposes cost aggregation; methods `increment_cost()` are invoked after successful API responses.

### Contributing
1. Fork the repository.
2. Create a feature branch: `git checkout -b feat/your-feature`.
3. Make changes + add/update tests.
4. Run formatting (e.g., `ruff`, `black`) as desired.
5. Submit a PR with a clear description.

### Release & Versioning
Uses semantic versioning: `MAJOR.MINOR.PATCH`.
* Increment PATCH for bug fixes.
* Increment MINOR for backward-compatible features.
* Increment MAJOR for breaking changes.

## 🧪 Troubleshooting

| Issue | Possible Cause | Fix |
|-------|----------------|-----|
| Invalid API key error | Key format mismatch | Re-generate and ensure it starts with `pplx-` and is 53 chars. |
| Empty responses | API transient error | Check logs; enable debug logging for `perplexity_assistant`. |
| Actions ignored | Actions disabled | Enable “Allow actions on entities” in options. |
| Costs remain 0 | API didn’t return cost usage | Confirm Perplexity response structure. |

### Enable Debug Logging
Add to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    perplexity_assistant: debug
```

## 🗺 Roadmap

* [WIP] HACS distribution.
* [WIP] More translation + localization improvements.
* Conversation memory.
* Optional streaming mode (real-time tokens).
* Request counter sensor.

## 📝 License

This project is distributed under the MIT License.

## 🙏 Acknowledgments

* Powered by Perplexity AI
* Thanks to Home Assistant’s openness, extensibility and team
* Created by Pekul (@Pekulll)

---

For questions or issues, open an issue on GitHub: https://github.com/Pekulll/perplexity-assistant/issues

