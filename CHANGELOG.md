# Changelog

## 1.0.0 — Class-leading registry + production API

- **466 models**, **130+ aliases**, **20 providers**
- **Together AI parser** — 200+ serverless deprecations from official docs (`.md` source)
- **Anthropic parser** — HTML deprecation tables → seed sync
- **API middleware** — `X-Request-ID` tracing, optional `MODELALIVE_RATE_LIMIT`
- **LiteLLM integration** — `modelalive.integrations.litellm.patch_litellm()`
- **Publish CI** — PyPI + npm on `v*` tags (`.github/workflows/publish.yml`)
- **docs/CONTRIBUTING.md** — provider contribution guide
- **125 tests** — Every LLM: Qwen, DeepSeek, Llama, Ollama

- **20 providers** — Qwen (DashScope), NVIDIA NIM, Ollama (local tags) + existing 17
- **259 models**, **125 aliases** — OpenRouter crosswalk generator (`scripts/generate_openrouter_crosswalk.py`)
- **DeepSeek v4** — `deepseek-v4-pro`, `deepseek-v4-flash` + expanded R1/V3 lifecycle
- **Meta Llama 3.2** — vision (11B/90B), 1B/3B instruct variants
- **Groq** — Qwen QwQ, Gemma2, Llama 3.2 vision previews, DeepSeek R1 distill
- **Ollama tag aliases** — `llama3.3`, `qwen3`, `deepseek-v3` → canonical IDs
- **merge_seeds.py** — rebuilds aliases from seeds (no stale self-referencing cycles)
- **118 tests**

## 0.8.0 — Universal LLM registry

- **17 providers**: xAI, Cohere, DeepSeek, Meta, Together, Fireworks, Cerebras, Perplexity, OpenRouter, Azure + existing
- **OpenRouter crosswalk** — `anthropic/claude-sonnet-4-6` → canonical ID
- **Host-specific lifecycle** — same weights, different retirement on Groq vs Together vs Fireworks
- `modelalive providers` + `GET /v1/providers`
- [docs/UNIVERSAL.md](docs/UNIVERSAL.md) — architecture for every inference surface

## 0.7.0

- **157 models** (+33 OpenAI via doc parser), **97 OpenAI** entries
- `scripts/parse_openai_deprecations.py` — auto-parse OpenAI deprecation tables
- `scripts/sync_drift.py` + daily **drift-pr** GitHub workflow
- **14 CLI tests** — check, ensure, scan, validate, bedrock alias
- TypeScript: `resolveDetail()`, `gate()`, `normalizeModel()`, Bedrock + ft: parity
- CLI `--provider` supports groq, mistral, bedrock
- **102+ tests**

## 0.6.0

- **`gate()`** context manager + **`require_alive`** decorator
- **`resolve_detail()`** — replacement chain + merged `breaking_changes`
- **Bedrock** model ID aliases (`anthropic.claude-*-v1:0`)
- **Mistral** provider seed (4 models)
- **Fine-tuned** OpenAI IDs (`ft:gpt-4o-mini:...` → base model lookup)
- **`MODELALIVE_REGISTRY_PATH`** / **`MODELALIVE_REGISTRY_URL`** env overrides
- API: `X-Model-Status`, `X-Replacement`, `ETag`, `GET /v1/models/{id}`, `POST /v1/ensure`
- API: `application/problem+json` for unknown models, stale registry health warning
- **88 tests** (+25), Hypothesis property tests
- `docs/QUICKSTART.md`, `SECURITY.md`, `registry/CHANGELOG.md`
- LangChain + LiteLLM integration examples

## 0.5.0

- **119 models** (+3 Groq) — seed merge now syncs provider sources
- TypeScript SDK (`js/`) — `alive`, `check`, `resolve`, `ensure`
- `GET /openapi.json` — machine-readable API schema
- `docs/ACCURACY.md` — source transparency and error reporting policy
- `.pre-commit-config.yaml` — validate + test hooks
- `examples/openai_preflight.py` — integration pattern
- `modelalive check-config` — validate `modelalive.toml` project config
- **63 tests** (+35)

## 0.4.0

- **116 models** (+48) via registry seed merge system
- `modelalive scan` — find retired/deprecated models in your codebase
- `modelalive expiring` — models retiring within N days
- `MODELALIVE_STRICT`, `MODELALIVE_WARN_DAYS`, `MODELALIVE_WARN_DEPRECATED` env vars
- `ModelExpiringSoonError` + `--warn-days` flag
- `GET /v1/expiring`, `py.typed`, drift-check CI workflow
- 28 tests

## 0.3.0

- Add `ensure()` pre-flight gate — validate and return safe model ID
- Add `resolve()` replacement chains (follows retired → active paths)
- Add `strict_unknown` mode for production CI gates
- Add `modelalive info`, `modelalive ensure` CLI commands
- Add `GET /v1/ensure` API endpoint
- Harden registry validation (replacement chains must end at active models)
- Expand registry: more Google/OpenAI models, new aliases
- Fix API test suite (all tests run, no skips)
- `list` and `/v1/registry` use effective status (date-aware)

## 0.2.1

- Registry v2 with source URLs and Anthropic/OpenAI/Google coverage
- Validation pipeline, batch API, GitHub Action, Docker/Fly.io configs
- Weekly registry refresh workflow

## 0.1.0

- Initial release: `alive`, `check`, `resolve`, CLI, FastAPI
