# Hosted API (modelalive.dev)

Public HTTP API for model lifecycle checks — deployable via Docker or Fly.io.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/health` | Registry health + stale warning |
| GET | `/v1/alive?model=` | Is this model alive? |
| GET | `/v1/ensure?model=` | Safe model ID (replacement chain) |
| POST | `/v1/ensure` | Same, JSON body |
| GET | `/v1/resolve?model=` | Replacement chain + breaking changes |
| GET | `/v1/models/{id}` | Full model entry |
| GET | `/v1/expiring?days=30` | Models retiring soon |
| GET | `/v1/providers` | Supported providers |
| GET | `/openapi.json` | OpenAPI 3.1 spec |

## Self-host

```bash
pip install "modelalive[api]"
uvicorn api.main:app --host 0.0.0.0 --port 8080
```

Docker:

```bash
docker build -t modelalive-api .
docker run -p 8080:8080 modelalive-api
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODELALIVE_RATE_LIMIT` | off | Max requests/minute per IP |
| `MODELALIVE_REQUIRE_API_KEY` | off | Require API key when set to `1` |
| `MODELALIVE_API_KEYS` | — | Comma-separated valid keys (hosted tier) |
| `MODELALIVE_REGISTRY_PATH` | bundled | Override registry JSON path |
| `MODELALIVE_ENFORCE_QUOTA` | off | Return 402 when monthly tier limit exceeded |
| `MODELALIVE_DEFAULT_TIER` | `pro` | Tier for authenticated API keys |

## Response headers

Every response includes:

- `X-Request-ID` — trace ID (pass your own via request header)
- `X-Model-Status` — on `/v1/alive`
- `X-Replacement` — when model is retired/deprecated
- `ETag` — registry version hash (cache with `If-None-Match`)

## Rate limiting

Set `MODELALIVE_RATE_LIMIT=100` for 100 requests/minute per client IP.
Health checks are excluded.

## API keys (monetization prep)

For hosted tiers, set:

```bash
export MODELALIVE_REQUIRE_API_KEY=1
export MODELALIVE_API_KEYS="ma_live_abc123,ma_live_def456"
```

Clients send:

```bash
curl -H "X-API-Key: ma_live_abc123" \
  "https://api.modelalive.dev/v1/alive?model=gpt-4o"
```

Free tier (future): 100 checks/month without key on `/v1/health` + limited `/v1/alive`.
Paid tier: API key + higher limits via Stripe (Phase 8).

## Deploy to Fly.io

```bash
fly auth login
fly launch --copy-config
fly secrets set MODELALIVE_RATE_LIMIT=120
fly deploy
```

GitHub Action `.github/workflows/deploy.yml` deploys on `v*` tags when `FLY_API_TOKEN` is set.

## Client example

```python
import httpx

BASE = "https://api.modelalive.dev"
headers = {"X-API-Key": "ma_live_..."}  # optional until hosted tier live

r = httpx.get(f"{BASE}/v1/ensure", params={"model": "claude-sonnet-4-20250514"}, headers=headers)
print(r.json()["safe_model"])  # claude-sonnet-4-6
```

Python SDK works offline — HTTP API is for CI, gateways, and non-Python stacks.
