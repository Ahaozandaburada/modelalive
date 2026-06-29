# Quickstart — FastAPI + Model Alive

60-second demo: **every chat request runs `modelalive.ensure()` first**.

## Run (mock mode — no API key)

```bash
cd examples/quickstart-fastapi
pip install -r requirements.txt
uvicorn main:app --reload --port 8090
```

```bash
# Retired ID → auto-replaced in response
curl -s -X POST http://127.0.0.1:8090/chat \
  -H 'Content-Type: application/json' \
  -d '{"model":"claude-sonnet-4-20250514","message":"hi"}' | python3 -m json.tool
```

Expected: `safe_model` → `claude-sonnet-4-6`, `lifecycle_status` → `retired`.

## Run (live OpenAI)

```bash
export OPENAI_API_KEY=sk-...
uvicorn main:app --port 8090
```

## Strict production

```bash
export MODELALIVE_STRICT=1
# Unknown model IDs now return HTTP 422
```

OpenAPI docs: http://127.0.0.1:8090/docs
