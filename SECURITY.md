# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.6.x   | ✅        |
| 0.5.x   | ✅        |
| < 0.5   | ❌        |

## Reporting a vulnerability

Email or open a **private** security advisory on GitHub:

https://github.com/Ahaozandaburada/modelalive/security/advisories/new

Please include:

- Description and impact
- Steps to reproduce
- Affected versions

Target response: **72 hours** acknowledgment, **7 days** for critical fixes.

## Scope

- Python package (`modelalive`)
- HTTP API (`api/`)
- Bundled registry JSON (supply-chain integrity)

Out of scope: third-party LLM provider APIs, hosted deployment infra (report separately when live).

## Registry integrity

- All registry changes go through `modelalive validate --strict` in CI
- Replacement chains must end at active models
- Drift-check workflow runs daily against provider docs

## Secrets

Never commit API keys, PyPI tokens, or Fly.io tokens. Use environment variables:

- `MODELALIVE_STRICT`
- `MODELALIVE_REGISTRY_PATH` / `MODELALIVE_REGISTRY_URL`
