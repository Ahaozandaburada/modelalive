# Reddit — r/LocalLLaMA

**Flair:** Resources / Discussion  
**When:** Weekday morning US time (overlap EU evening)

---

## Title

`modelalive` — pre-flight check for Ollama tags and OpenRouter slugs before they break your app

---

## Body

If you run local models via Ollama or route through OpenRouter, model strings are messy (`llama3.2:latest`, `anthropic/claude-sonnet-4-6`, etc.).

I built **Model Alive** — a small `pip install modelalive` gate that runs **before** your inference call:

```bash
pip install modelalive

# Ollama tag → canonical weights
modelalive check ollama/llama3.2:latest

# OpenRouter slug → provider canonical ID
modelalive check openrouter/anthropic/claude-sonnet-4-6

# Retired cloud model → see replacement
modelalive ensure claude-sonnet-4-20250514
# → claude-sonnet-4-6
```

**Alive** = official lifecycle (retired/deprecated) from provider docs.  
**Stable** (optional) = same model name, different behavior — ghost drift probe for CI.

- 765 models, offline registry (no network needed for `check`)
- GitHub Action for CI
- Hosted status API: https://modelalive.fly.dev/status

Repo: https://github.com/Ahaozandaburada/modelalive

Not claiming 100% coverage — unknown local tags pass by default. `--strict-unknown` for CI.

Would love feedback on Ollama/HF slug coverage. Issue template to add models: https://github.com/Ahaozandaburada/modelalive/issues/new?template=add-model.yml

---

## Comment to pin (optional)

Examples folder: https://github.com/Ahaozandaburada/modelalive/tree/main/examples  
LiteLLM hook: `from modelalive.integrations.litellm import patch_litellm; patch_litellm()`
