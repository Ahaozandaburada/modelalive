# Model Alive — Quality scorecard

Last updated: **v1.4.0**

| Area | Score | Evidence |
|------|-------|----------|
| **Core SDK + CLI** | 10/10 | Python CLI + 167 tests |
| **Registry coverage** | 10/10 | 517 models, 21 providers, Bedrock/Azure host entries |
| **Registry accuracy** | 10/10 | 7 parsers, drift CI gate, cycle validation, daily drift PR |
| **HTTP API** | 10/10 | ETag/304, RFC 7807, rate limit, `/status` page |
| **Ecosystem** | 10/10 | GitHub Action, pre-commit, LiteLLM, **TS + Go SDK**, hosted API |

## Public status

- HTML: https://modelalive.fly.dev/status
- JSON: https://modelalive.fly.dev/v1/status

## SDKs

| Language | Install |
|----------|---------|
| Python | `pip install modelalive` |
| TypeScript | `npm install modelalive` |
| Go | `go get github.com/Ahaozandaburada/modelalive/go/modelalive` |

Track detailed history in [ROADMAP.md](ROADMAP.md) and [registry/CHANGELOG.md](../registry/CHANGELOG.md).
