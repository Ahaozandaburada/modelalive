# Registry changelog

All notable registry changes are logged here.

## 2026-06-28 — v1.0.0

### Added
- **Together AI parser** — 200+ serverless deprecations from official `.md` docs
- **Anthropic HTML parser** — status + history tables
- OpenRouter crosswalk in drift sync pipeline

### Totals
- **466 models**, **130+ aliases**, **20 providers**

## 2026-06-28 — v0.7.0

### Added
- **OpenAI doc parser** — 93 models from official deprecations page (+33 net new)
- Daily **drift-pr** workflow for automated registry PRs
- CLI tests (14), TS `resolveDetail` + `gate` + `normalizeModel`

### Totals
- **157 models**, 97 OpenAI, 16 aliases

## 2026-06-28 — v0.6.0

### Added
- **Bedrock** crosswalk aliases (`anthropic.claude-*-v1:0` → canonical Anthropic IDs)
- **Mistral** provider: 4 models + `-latest` aliases
- **Groq** provider (from 0.5.0): 3 models

### Totals
- 124 models, 16 aliases, 6 provider sources

## 2026-06-28 — v0.5.0

- Groq seed merged (+3 models)
- Registry seed merge now syncs provider `sources`

## 2026-06-28 — v0.4.0

- 116 models via seed merge system (OpenAI, Anthropic, Google)
- Drift-check CI workflow

## 2026-06-28 — v0.3.0

- Registry v2 schema with source URLs
- Replacement chain validation
