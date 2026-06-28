# Accuracy policy

Model Alive is a **pre-flight advisory** service. We optimize for speed, source transparency, and low false-positive rates — not legal guarantees.

## Sources

Every verified registry entry maps to an official provider deprecation page:

| Provider | Source |
|----------|--------|
| Anthropic | [Model deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations) |
| OpenAI | [API deprecations](https://developers.openai.com/api/docs/deprecations) |
| Google | [Gemini deprecations](https://ai.google.dev/gemini-api/docs/deprecations) |
| Groq | [Groq deprecations](https://console.groq.com/docs/deprecations) |

Each entry includes `source`, `source_url`, and `source_checked_at` in API/SDK responses.

## Unknown models

Models **not in the registry** return:

- `status: unknown`
- `confidence: unknown`
- `alive: true` (default — we do not block unverified IDs)

Enable strict mode for production:

```bash
export MODELALIVE_STRICT=1
modelalive check "$MODEL_ID"
```

## If we are wrong

1. **False retired (worst):** We mark a live model as dead → you migrate unnecessarily.  
   Mitigation: source links on every response, public registry changelog, drift CI.

2. **False alive:** Model is dead but not in registry → your provider returns 404.  
   Mitigation: weekly refresh workflow, community issues, `modelalive scan`.

## Report an error

Open an issue: https://github.com/Ahaozandaburada/modelalive/issues

Include: model ID, expected status, link to provider announcement.

Target: fix within **24 hours** for confirmed errors on tier-1 providers.

## SLA (hosted API — future)

When `api.modelalive.dev` launches:

- Registry updates within 24h of provider announcement
- 99.9% API uptime target
- Public status page

Self-hosted / PyPI users always have the bundled registry version in `registry_version`.
