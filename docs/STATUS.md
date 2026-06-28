# Model Alive — Quality scorecard

Last updated: **v1.3.0**

| Area | Score | Evidence |
|------|-------|----------|
| **Core SDK + CLI** | 10/10 | `check`, `ensure`, `scan`, env flags, 160+ tests |
| **Registry coverage** | 9/10 | 517 models, 21 providers, Bedrock/Azure host entries |
| **Registry accuracy** | 9/10 | 7 doc parsers, drift CI fails on stale registry, cycle validation |
| **HTTP API** | 10/10 | ETag/`If-None-Match`, RFC 7807, rate limit, request ID, OpenAPI |
| **Ecosystem** | 9/10 | GitHub Action, pre-commit, LiteLLM, TS SDK parity, hosted API |

## What “10/10” means here

- Every tier-1 provider has an official source URL + parser or manual seed
- `modelalive validate --strict` + replacement/alias cycle checks pass in CI
- `scripts/check_registry_drift.py` fails if committed registry ≠ live docs
- Hosted API supports conditional GET caching on registry-backed routes

## Remaining for absolute perfection

- Go/Rust SDKs
- Public status page (`status.modelalive.dev`)
- Stripe billing activation (optional)
- Groq SPA doc parser (currently offline/manual seed)

Track detailed tasks in [ROADMAP.md](ROADMAP.md).
