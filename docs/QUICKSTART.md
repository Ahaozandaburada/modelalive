# Quickstart (60 seconds)

## Install

```bash
pip install modelalive
# or: npm install modelalive
```

## Pre-flight before every API call

```python
import modelalive

# Auto-replace retired models — use this in production
model_id = modelalive.ensure("claude-sonnet-4-20250514")
# → "claude-sonnet-4-6"

client.chat.completions.create(model=model_id, messages=[...])
```

## CI gate (fail on retired)

```bash
modelalive check claude-sonnet-4-20250514   # exit 1
modelalive ensure claude-sonnet-4-20250514  # prints safe ID
```

Strict production mode:

```bash
export MODELALIVE_STRICT=1
modelalive check "$MODEL_ID"   # fails on unknown models too
```

## Scan your codebase

```bash
modelalive scan .
modelalive expiring --days 30
```

## Project config

`modelalive.toml`:

```toml
models = [
  "claude-sonnet-4-6",
  "gpt-5.5",
]

[ci]
strict_unknown = true   # optional — overrides $MODELALIVE_STRICT when set
warn_deprecated = true
warn_days = 14
```

Without `[ci]`, `check-config` honors `MODELALIVE_STRICT`, `MODELALIVE_WARN_DEPRECATED`, and `MODELALIVE_WARN_DAYS`.

```bash
modelalive check-config
```

## GitHub Actions

```yaml
- uses: Ahaozandaburada/modelalive@main
  with:
    models: claude-sonnet-4-6 gpt-5.5
    strict-unknown: "true"
```

## Self-host API

```bash
docker compose up --build
curl "http://localhost:8787/v1/alive?model=gemini-2.0-flash"
curl "http://localhost:8787/v1/ensure?model=claude-sonnet-4-20250514"
```

## Bedrock / OpenRouter / fine-tuned IDs

```python
modelalive.alive("anthropic.claude-sonnet-4-6-v1:0")  # Bedrock → active
modelalive.alive("openai/gpt-4o")                     # OpenRouter → gpt-4o
modelalive.alive("fireworks/kimi-k2p5")               # host-specific lifecycle
modelalive.alive("ft:gpt-4o-mini:org:name:id")        # → gpt-4o-mini
```

```bash
modelalive providers   # 17 inference surfaces
```
