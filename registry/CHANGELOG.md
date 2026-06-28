# Registry changelog

All model lifecycle changes are tracked here. Automated drift PRs append entries.

## 2026-06-28 — v1.2.0 host expansion

- **+32** Bedrock and Azure host-specific model entries
- Bedrock replacements now point to Bedrock inference profile IDs
- Regional aliases: `us.*`, `eu.*` → primary Bedrock ID

## 2026-06-28 — v1.0.x universal expansion

- Together parser: 200+ serverless models
- Anthropic, Google, Fireworks doc parsers
- OpenRouter crosswalk (65+ slugs)
- Qwen, DeepSeek, Ollama, NVIDIA NIM seeds

## 2026-06-28 — v0.4.0 seed system

- Introduced `registry/seeds/` merge pipeline
- Groq retired models: llama3-70b-8192, mixtral-8x7b-32768
