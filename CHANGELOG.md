# Changelog

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
