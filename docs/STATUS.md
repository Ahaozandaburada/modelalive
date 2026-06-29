# Model Alive — Quality scorecard

Last updated: **v1.5.1**

| Area | Score | Evidence |
|------|-------|----------|
| **Alive (lifecycle)** | 10/10 | 517 models, drift CI, Python + TS + Go SDK |
| **Stable (behavioral drift)** | 10/10 | 5-prompt fingerprint, 5 probe backends, CLI + API + Action |
| **Core SDK + CLI** | 10/10 | Python CLI + 195+ tests |
| **Registry coverage** | 10/10 | 517 models, 21 providers, Bedrock/Azure |
| **HTTP API** | 10/10 | ETag/304, RFC 7807 stable-drift, `/status` + stable endpoints |
| **Ecosystem** | 10/10 | GitHub Action (lifecycle + stable), pre-commit, adoption kit |

## Two-layer gate

| Layer | Question | Command |
|-------|----------|---------|
| **Alive** | Is the model ID officially retired? | `modelalive check` |
| **Stable** | Same ID, different behavior? | `modelalive stable check` |

## Stable stack

| Component | Status |
|-----------|--------|
| Python SDK | `compare_fingerprints`, `assert_stable`, `validate_fingerprint` |
| TypeScript SDK | `compareFingerprints`, `assertStable` |
| Go SDK | `CompareFingerprints`, `AssertStable` |
| Probe backends | Anthropic, Google, OpenAI-compatible, OpenRouter, Bedrock (boto3) |
| HTTP API | `/v1/stable/prompts`, `/fingerprint`, `/compare` |
| Config | `[[stable]]` in `modelalive.toml` + `check-config` |
| CI | `stable-offline.yml`, Action `stable-baseline` input |
| Example baselines | `examples/baselines/*.json` |

## Public status

- HTML: https://modelalive.fly.dev/status
- JSON: https://modelalive.fly.dev/v1/status
- Stable: https://modelalive.fly.dev/v1/stable/prompts

## SDKs

| Language | Install |
|----------|---------|
| Python | `pip install modelalive[stable]` |
| TypeScript | `npm install modelalive` |
| Go | `go get github.com/Ahaozandaburada/modelalive/go/modelalive` |

Track history: [CHANGELOG.md](../CHANGELOG.md) · [STABLE.md](STABLE.md)
