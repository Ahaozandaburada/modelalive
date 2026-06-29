# Stable — behavioral drift (ghost changes)

**Status: Production-ready** — use in CI after recording a baseline. Not a full Stability Monitor replacement.

Model Alive answers two different questions:

| Command | Question |
|---------|----------|
| `modelalive check` | Is this model ID **officially retired**? |
| `modelalive stable check` | Is this endpoint **behaving the same** as before? |

Inspired by [Stability Monitor (arxiv:2603.19022)](https://arxiv.org/abs/2603.19022) — uptime can stay green while weights, quantization, routing, or inference stack change under the same model name.

## Quick start

```bash
# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...
modelalive stable baseline claude-sonnet-4-6 -o .modelalive/stable.json

# OpenAI
export OPENAI_API_KEY=sk-...
modelalive stable baseline gpt-4o -o .modelalive/gpt-4o-stable.json

# Google Gemini
export GOOGLE_API_KEY=...
modelalive stable baseline gemini-3.5-flash -o .modelalive/gemini-stable.json

# Compare later (CI cron, deploy gate, manual)
modelalive stable check claude-sonnet-4-6 -b .modelalive/stable.json
# exit 1 → behavioral drift detected
```

Provider auto-detection uses the registry; override with `--provider anthropic|google|openai`.

## Hosted API

```bash
# List probe prompts
curl https://modelalive.fly.dev/v1/stable/prompts

# Build fingerprint from responses you collected
curl -X POST https://modelalive.fly.dev/v1/stable/fingerprint \
  -H 'Content-Type: application/json' \
  -d '{"model":"gpt-4o","responses":{"json_echo":["{\"ok\": true, \"n\": 42}"],"math_fixed":["391"],"refusal_probe":["no"],"code_snippet":["def f(): pass"],"style_haiku":["a\\nb\\nc"]}}'

# Compare baseline vs current (409 on drift)
curl -X POST https://modelalive.fly.dev/v1/stable/compare \
  -H 'Content-Type: application/json' \
  -d '{"baseline":{...},"current":{...},"threshold":0.25}'
```

Response headers: `X-Stable`, `X-Mean-Distance`.

## Offline / CI without repeated API calls

```bash
modelalive stable baseline gpt-4o --from-json responses.json -o baseline.json
modelalive stable diff baseline.json current.json --threshold 0.25
```

`responses.json` shape:

```json
{
  "json_echo": ["{\"ok\": true, \"n\": 42}"],
  "math_fixed": ["391"]
}
```

## GitHub Action

Lifecycle + behavioral gate:

```yaml
- uses: Ahaozandaburada/modelalive@v1.6.1
  with:
    models: claude-sonnet-4-6
    strict-unknown: "true"
    stable-baseline: .modelalive/stable.json
    stable-threshold: "0.25"
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

Full workflow: [`examples/github-actions/stable-check.yml`](../examples/github-actions/stable-check.yml)

## Configuration

| Env | Purpose |
|-----|---------|
| `ANTHROPIC_API_KEY` | Anthropic probe |
| `OPENAI_API_KEY` | OpenAI-compatible probe |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Gemini probe |
| `MODELALIVE_PROBE_API_KEY` | Override key for any backend |
| `MODELALIVE_PROBE_BASE_URL` | Override base URL |
| `MODELALIVE_PROBE_PROVIDER` | Force `anthropic`, `google`, or `openai` |

## Python API

```python
from modelalive import compare_fingerprints, fingerprint_from_responses, assert_stable, StableShiftError
from modelalive.probe import probe_responses

responses = probe_responses("claude-sonnet-4-6")
baseline = fingerprint_from_responses("claude-sonnet-4-6", responses)
current = fingerprint_from_responses("claude-sonnet-4-6", probe_responses("claude-sonnet-4-6"))
report = compare_fingerprints(baseline, current, threshold=0.25)
assert_stable(baseline, current)
```

## Recommended gate

```bash
modelalive check claude-sonnet-4-6 --strict-unknown
modelalive stable check claude-sonnet-4-6 -b .modelalive/stable.json
```

Lifecycle first, behavior second.

## Limits (honest)

- **Production-ready**, not perfect — 5 fixed prompts, trigram distance; tune `--threshold` for your model
- Live probe costs ~5 API calls per check
- Stochastic models may false-positive; subtle drift may false-negative
- Complements lifecycle checks — run **Alive first**, then Stable
- For legal/compliance-grade monitoring, add eval suites and dedicated stability tooling
