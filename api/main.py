from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from modelalive.check import alive, resolve
from modelalive.registry import load_registry, registry_version

app = FastAPI(
    title="Model Alive",
    description="Pre-flight API: is this LLM model ID still alive?",
    version="0.1.0",
)


@app.get("/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "registry_version": registry_version() or "unknown"}


@app.get("/v1/alive")
def get_alive(model: str = Query(..., min_length=1, description="Model ID to check")):
    result = alive(model)
    payload = result.to_dict()
    status_code = 410 if result.status == "retired" else 200
    return JSONResponse(content=payload, status_code=status_code)


@app.get("/v1/resolve")
def get_resolve(model: str = Query(..., min_length=1)):
    return {"model": model, "resolved": resolve(model)}


@app.get("/v1/registry")
def list_registry(
    status: str | None = Query(None, description="Filter: active, deprecated, retired"),
):
    registry = load_registry()
    models = registry.get("models", {})
    if status:
        filtered = {k: v for k, v in models.items() if v.get("status") == status}
    else:
        filtered = models
    return {
        "registry_version": registry.get("version"),
        "count": len(filtered),
        "models": filtered,
    }
