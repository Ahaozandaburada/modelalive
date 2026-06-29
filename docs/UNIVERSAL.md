# Universal LLM registry (v1.6+)

Model Alive is the pre-flight lifecycle gate for **every major LLM inference surface** — not just OpenAI, Anthropic, and Google.

## What “universal” means here

| Included | Not included |
|----------|----------------|
| First-party APIs (OpenAI, Anthropic, Google, xAI, Cohere, DeepSeek, Mistral, …) | Models that never appear in any public catalog |
| Inference hosts (Groq, Together, Fireworks, Cerebras, …) | Private fine-tunes with no public base mapping |
| Cloud gateways (AWS Bedrock, Azure OpenAI) | Guaranteed zero false positives |
| Aggregators (OpenRouter — **live catalog sync**) | Behavioral drift (use **Stable** for that) |
| Local runtimes (Ollama tags, `:latest`, size tags) | |
| Hugging Face Inference slugs | |
| LiteLLM routes (`litellm/anthropic/claude-…`) | |

**Universal** = one normalization + resolution path before any request, regardless of how your stack formats the model string.

## Resolution pipeline

```
raw model string
  → normalize_model()     # strip openrouter/, ollama/, hf/, ft:, :latest, us. bedrock prefix
  → universal_resolve()   # aliases + case-insensitive + slash heuristics
  → alive() / ensure()    # lifecycle gate
```

Examples:

```bash
modelalive check openrouter/anthropic/claude-sonnet-4-6
modelalive check ollama/llama3.2:latest
modelalive check meta-llama/llama-3.3-70b-instruct   # HF lowercase → canonical
modelalive check us.anthropic.claude-sonnet-4-6-v1:0
```

## Provider tiers

| Tier | Examples | Model ID style |
|------|----------|----------------|
| **First-party API** | OpenAI, Anthropic, xAI, Cohere, DeepSeek, Mistral, Perplexity | `gpt-5.5`, `claude-sonnet-4-6` |
| **Model vendor** | Meta Llama | `meta-llama/Llama-3.3-70B-Instruct` |
| **Inference host** | Groq, Together, Fireworks, Cerebras | Host path, e.g. `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| **Cloud gateway** | AWS Bedrock, Azure OpenAI | `anthropic.claude-sonnet-4-6-v1:0` |
| **Aggregator** | OpenRouter (live sync) | `anthropic/claude-sonnet-4-6` → canonical |
| **Local** | Ollama | `llama3.2:latest` → canonical weights |
| **HF Inference** | Hugging Face | `meta-llama/llama-3.3-70b-instruct` |

## OpenRouter live sync

Daily drift sync runs `scripts/fetch_openrouter_models.py`, which:

1. Fetches `https://openrouter.ai/api/v1/models`
2. Maps known slugs to canonical registry entries
3. Registers unmapped routes as `provider: openrouter` (active passthrough)

Re-run manually:

```bash
python scripts/fetch_openrouter_models.py
python scripts/merge_seeds.py && python scripts/sync_registry.py
```

## LiteLLM as universal adapter

```python
from modelalive.integrations.litellm import patch_litellm

patch_litellm()  # wraps litellm.completion — ensure() on every call
```

Any LiteLLM route benefits from the same normalization and resolution.

## Adding a provider

1. Add `registry/seeds/{provider}.json` with `sources`, `models`, optional `aliases`
2. Register in `registry/providers.json`
3. `python scripts/merge_seeds.py && modelalive validate --strict`
4. Open PR — drift CI validates source URLs

## Goal

Every model ID your app might send to **any** LLM API — one `modelalive.ensure()` call before the request.

Honest limit: coverage grows with drift sync and community PRs; unknown models still pass by default unless `--strict-unknown`.
