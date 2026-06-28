# Universal LLM registry

Model Alive is **not** an OpenAI + Anthropic + Google tool. It is the pre-flight lifecycle gate for **every LLM inference surface** your code might call.

## Provider tiers

| Tier | Examples | Model ID style |
|------|----------|----------------|
| **First-party API** | OpenAI, Anthropic, xAI, Cohere, DeepSeek, Mistral, Perplexity | `gpt-5.5`, `claude-sonnet-4-6`, `grok-4.3` |
| **Model vendor** | Meta Llama | `meta-llama/Llama-3.3-70B-Instruct` |
| **Inference host** | Groq, Together, Fireworks, Cerebras | Host path, e.g. `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| **Cloud gateway** | AWS Bedrock, Azure OpenAI | `anthropic.claude-sonnet-4-6-v1:0`, deployment aliases |
| **Aggregator** | OpenRouter, LiteLLM routes | `anthropic/claude-sonnet-4-6` → canonical via alias |

## Canonical vs host-specific

- **Direct API models** use the provider's native ID (short form).
- **Hosted copies** of the same weights may retire on different dates — each host gets its own registry entry with `provider: together|fireworks|groq`.
- **Crosswalk aliases** map aggregator slugs (`openai/gpt-4o`) and gateway IDs to canonical entries.

## Adding a provider

1. Add `registry/seeds/{provider}.json` with `sources`, `models`, optional `aliases`
2. Register in `registry/providers.json`
3. `python scripts/merge_seeds.py && modelalive validate --strict`
4. Open PR — drift CI validates source URLs

## Goal

Every model ID your app might send to **any** LLM API — one `modelalive.ensure()` call before the request.
