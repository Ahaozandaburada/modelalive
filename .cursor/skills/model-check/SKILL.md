---
name: model-check
description: Validates LLM model IDs for retirement, deprecation, and replacements using Model Alive. Use when adding or changing model IDs, LLM config, .env variables, API client setup, LiteLLM/proxy config, Bedrock/Azure/OpenRouter IDs, or when the user asks if a model is still alive, deprecated, or what to replace it with.
---

# Model Alive — model ID pre-flight

## When to run

- User adds/changes `model=`, `MODEL`, or provider model strings
- Before committing env files or deployment config with LLM IDs
- User asks "is X still available?" or "what replaces Y?"

## Quick commands

```bash
pip install modelalive   # or: npm install modelalive
modelalive check MODEL_ID
modelalive ensure MODEL_ID      # prints safe ID
modelalive resolve MODEL_ID     # best ID + breaking changes
modelalive info MODEL_ID        # full lifecycle JSON
modelalive scan .               # find hardcoded IDs in repo
modelalive stable check MODEL -b .modelalive/stable.json  # ghost drift
modelalive expiring --days 30   # upcoming retirements
```

Strict mode: `MODELALIVE_STRICT=1 modelalive check MODEL_ID`

## Code patterns (prefer these)

**Python**

```python
import modelalive

model = modelalive.ensure(user_model_id)
# or
with modelalive.gate(model_id) as safe:
    client.chat.completions.create(model=safe, ...)
```

**TypeScript**

```typescript
import { ensure, check } from "modelalive";
const model = ensure(process.env.LLM_MODEL!);
```

**Go**

```go
import "github.com/Ahaozandaburada/modelalive/go/modelalive"
safe, err := modelalive.Ensure("claude-sonnet-4-20250514")
```

## HTTP (no local install)

```bash
curl -s "https://modelalive.fly.dev/v1/alive?model=MODEL_ID"
curl -s "https://modelalive.fly.dev/v1/ensure?model=MODEL_ID"
```

Retired models return HTTP 410 on `/v1/alive`.

## If check fails

1. Read `replacement` and `source_url` from CLI JSON (`--json`) or API response
2. Update code/config to the replacement (or `ensure()` output)
3. Re-run `modelalive check` on all affected IDs
4. Mention breaking changes from `resolve` if any

## Project config

If `modelalive.toml` exists, run `modelalive check-config` after edits.

## Do not

- Guess replacement model names from memory
- Skip validation for "just a preview/dev" models
- Block on `unknown` unless `MODELALIVE_STRICT=1` or user wants strict CI

More: [docs/ADOPTION.md](../../docs/ADOPTION.md) · [docs/QUICKSTART.md](../../docs/QUICKSTART.md)
