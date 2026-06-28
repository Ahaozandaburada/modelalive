# Model Alive

**517 models · 21 providers · 130+ aliases** — OpenAI, Anthropic, Google, Qwen, DeepSeek, Llama, Groq, Together, Fireworks, **Bedrock**, **Azure**, OpenRouter, Ollama, and more.

Hardcoded model IDs break silently until production fails. Model Alive answers in one call — with **source links**, **breaking change** notes, and **host-aware** lifecycle status.

**[Quality scorecard →](docs/STATUS.md)** · **[Universal registry guide →](docs/UNIVERSAL.md)** · **[60-second quickstart →](docs/QUICKSTART.md)**

## Install

```bash
pip install modelalive
```

JavaScript/TypeScript:

```bash
npm install modelalive
```

Go:

```bash
go get github.com/Ahaozandaburada/modelalive/go/modelalive
```

## Quick examples

```bash
# Retired model → exit 1
modelalive check claude-sonnet-4-20250514

# Resolve alias + replacement
modelalive resolve claude-3-5-sonnet-latest

# List all retired Anthropic models
modelalive list --status retired --provider anthropic

# Validate registry integrity
modelalive validate --strict

# Pre-flight: print safe model ID (auto-replaces retired)
modelalive ensure claude-sonnet-4-20250514

# Production CI: fail on unknown models too
modelalive check "$MODEL_ID" --strict-unknown --warn-deprecated
```

```python
import modelalive

# Pre-flight: auto-replace retired models
model_id = modelalive.ensure("claude-sonnet-4-20250514")
# → "claude-sonnet-4-6"

# Context manager for call sites
with modelalive.gate("gemini-2.0-flash") as safe:
    call_api(safe)  # → gemini-3.5-flash

result = modelalive.alive("claude-mythos-preview")
print(result.days_until_retirement)  # 2 (as of 2026-06-28)
print(result.source_url)             # Anthropic deprecation docs
print(result.confidence)             # "verified"
```

## TypeScript / Node

```bash
cd js && npm install && npm run build
```

```typescript
import { alive, ensure, resolve } from "modelalive";

ensure("claude-sonnet-4-20250514"); // → "claude-sonnet-4-6"
alive("gemini-2.0-flash").status;     // → "retired"
```

## HTTP API

```bash
uvicorn api.main:app --port 8787
```

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/alive?model=` | Lifecycle check (410 if retired) |
| POST | `/v1/alive/batch` | Check up to 100 models |
| GET | `/v1/ensure?model=` | Pre-flight: return safe model ID |
| GET | `/v1/resolve?model=` | Best model ID + breaking changes |
| GET | `/v1/registry` | Filter by `status`, `provider` |
| GET | `/v1/sources` | Official doc URLs + last checked date |
| GET | `/v1/validate` | Registry integrity report |
| GET | `/v1/expiring?days=` | Models retiring within N days |
| GET | `/openapi.json` | OpenAPI 3 schema |
| GET | `/v1/health` | Version + model count |

## CI gate (GitHub Actions)

```yaml
- uses: Ahaozandaburada/modelalive@main
  with:
    models: claude-sonnet-4-20250514 gpt-5-2025-08-07
    warn-deprecated: "true"
```

Or plain shell:

```yaml
- run: pip install modelalive && modelalive check ${{ env.MODEL_ID }}
```

## Trust & accuracy

Every verified entry includes:

- **`source`** — provider key (`anthropic`, `openai`, `google`, `groq`)
- **`source_url`** — official deprecation page (returned in API/SDK)
- **`source_checked_at`** — date registry was last synced with docs
- **`confidence`** — `verified` (in registry) or `unknown` (not listed)

Registry rules enforced in CI:

- Retired/deprecated models must have `replacement` + `retired_at`
- Past `retired_at` auto-marks model dead even if status lags
- Aliases resolve before lookup (`claude-3-5-sonnet-latest` → dated snapshot)
- `modelalive validate --strict` fails on errors before release

**Canonical registry:** edit `registry/models.json`, then:

```bash
python scripts/sync_registry.py   # copies to package bundle
modelalive validate --strict
pytest
```

Sources (as of 2026-06-28):

- [Anthropic model deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations)
- [OpenAI API deprecations](https://developers.openai.com/api/docs/deprecations)

## Response shape

```json
{
  "queried_model": "claude-sonnet-4-20250514",
  "canonical_model": "claude-sonnet-4-20250514",
  "alive": false,
  "status": "retired",
  "provider": "anthropic",
  "retired_at": "2026-06-15",
  "replacement": "claude-sonnet-4-6",
  "breaking_changes": [],
  "source_url": "https://platform.claude.com/docs/en/about-claude/model-deprecations",
  "source_checked_at": "2026-06-28",
  "confidence": "verified"
}
```

## Coverage

| Provider | Active | Deprecated | Retired |
|----------|--------|------------|---------|
| Anthropic | Sonnet 4.6, Opus 4.8, Haiku 4.5, Mythos 5, … | Opus 4.1, Mythos Preview | Sonnet 4, Opus 4, 3.x series |
| OpenAI | gpt-5.5, gpt-4o, … | gpt-5 snapshots, gpt-5.2-chat-latest, … | gpt-4-0314, gpt-3.5-turbo-0301, … |
| Google | gemini-3.5-flash, … | 2.5 Flash, embeddings, image previews | gemini-2.0-flash (June 1), gemini-3-pro-preview |
| Groq | llama-3.3-70b-versatile, … | — | llama3-70b-8192, mixtral-8x7b-32768 |

See [docs/ACCURACY.md](docs/ACCURACY.md) for source policy and error reporting.

Unknown models return `status: unknown`, `confidence: unknown`, `alive: true` — we never block what we haven't verified.

## Docker (self-host API)

```bash
docker compose up --build
curl "http://localhost:8787/v1/alive?model=gemini-2.0-flash"
```

Deploy to Fly.io:

```bash
fly launch --copy-config --yes
fly deploy
```

## Keep registry fresh

```bash
pip install modelalive[http]
python scripts/refresh_sources.py   # fetch provider docs, update checked_at
modelalive validate --strict
python scripts/sync_registry.py
```

Weekly automated refresh runs via `.github/workflows/registry-refresh.yml`.

Sources (as of 2026-06-28):

- [Anthropic model deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations)
- [OpenAI API deprecations](https://developers.openai.com/api/docs/deprecations)
- [Google Gemini deprecations](https://ai.google.dev/gemini-api/docs/deprecations)

## License

MIT
