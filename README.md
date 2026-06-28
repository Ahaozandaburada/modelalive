# Model Alive

Pre-flight check before every LLM API call: **is this model ID still alive?**

Hardcoded model IDs break silently until production fails. Anthropic retired Claude Sonnet 4 and Opus 4 on **June 15, 2026**. Mythos Preview retires **June 30, 2026**. Model Alive answers in one call.

## Quick start

```bash
pip install -e ".[dev]"
modelalive check claude-sonnet-4-20250514
```

```
DEAD: claude-sonnet-4-20250514 (retired)
  replacement: claude-sonnet-4-6
```

## Python SDK

```python
import modelalive

# Raises ModelRetiredError if dead
modelalive.check("claude-sonnet-4-20250514")

# Non-throwing status
result = modelalive.alive("claude-mythos-preview")
print(result.days_until_retirement)  # 2 (as of 2026-06-28)

# Auto-replace before calling your provider
model_id = modelalive.resolve("claude-sonnet-4-20250514")
# → "claude-sonnet-4-6"
```

## HTTP API

```bash
uvicorn api.main:app --reload --port 8787
```

```bash
curl "http://localhost:8787/v1/alive?model=claude-sonnet-4-20250514"
```

```json
{
  "model": "claude-sonnet-4-20250514",
  "alive": false,
  "status": "retired",
  "provider": "anthropic",
  "retired_at": "2026-06-15",
  "replacement": "claude-sonnet-4-6",
  "breaking_changes": [],
  "migrate_url": "https://platform.claude.com/docs/en/about-claude/model-deprecations"
}
```

Retired models return **HTTP 410**.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/alive?model=` | Lifecycle check |
| GET | `/v1/resolve?model=` | Best model ID to use |
| GET | `/v1/registry` | Full registry (optional `?status=retired`) |
| GET | `/v1/health` | Health + registry version |

## Registry

Curated deprecation data lives in `registry/models.json`. Update when providers announce retirements.

## License

MIT
