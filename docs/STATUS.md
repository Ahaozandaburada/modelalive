# Model Alive — Quality scorecard

Last updated: **v1.5.1**

**Top tier: Production-ready** — shippable, documented, tested, and suitable for CI/production gates.  
**Not claimed:** flawless detection, 100% model coverage, or zero false positives/negatives.

| Area | Status | Evidence |
|------|--------|----------|
| **Alive (lifecycle)** | **Production-ready** | 517 models, drift CI, Python + TS + Go SDK, source links |
| **Stable (behavioral drift)** | **Production-ready** | 5-prompt fingerprint, 5 probe backends, CLI + API + Action |
| **Core SDK + CLI** | Production-ready | Python CLI + 195 tests |
| **Registry coverage** | Production-ready | 517 models, 21 providers, Bedrock/Azure host entries |
| **HTTP API** | Production-ready | ETag/304, RFC 7807 stable-drift, `/status` + stable endpoints |
| **Ecosystem** | Production-ready | GitHub Action (lifecycle + stable), pre-commit, adoption kit |

## What “production-ready” means here

| | Alive | Stable |
|---|-------|--------|
| **Good for** | Blocking retired/deprecated IDs before deploy | Catching silent backend drift under the same model name |
| **Ship with** | `modelalive check` in CI | `modelalive stable check` after baseline recorded |
| **Honest limit** | Registry lag; unknown IDs pass by default | 5 prompts + trigram metric; not Stability Monitor–grade |
| **Not a guarantee** | Provider won’t retire unlisted models silently | Subtle or stochastic drift may slip through |

Both layers are **advisory pre-flight gates** — see [ACCURACY.md](ACCURACY.md).

## Two-layer gate

| Layer | Question | Command |
|-------|----------|---------|
| **Alive** | Is the model ID officially retired? | `modelalive check` |
| **Stable** | Same ID, different behavior? | `modelalive stable check` |

Recommended production sequence:

```bash
modelalive check "$MODEL" --strict-unknown
modelalive stable check "$MODEL" -b .modelalive/stable.json
```

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

Track history: [CHANGELOG.md](../CHANGELOG.md) · [STABLE.md](STABLE.md) · [ACCURACY.md](ACCURACY.md)
