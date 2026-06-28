from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from modelalive import __version__
from modelalive.check import alive, check_many, ensure, resolve
from modelalive.registry import load_registry, registry_version
from modelalive.validate import validate_registry

app = FastAPI(
    title="Model Alive",
    description="Pre-flight API: is this LLM model ID still alive?",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class BatchRequest(BaseModel):
    models: list[str] = Field(..., min_length=1, max_length=100)


@app.get("/v1/health")
def health() -> dict[str, str | int]:
    registry = load_registry()
    return {
        "status": "ok",
        "version": __version__,
        "registry_version": registry_version() or "unknown",
        "model_count": len(registry.get("models", {})),
    }


@app.get("/v1/sources")
def get_sources():
    registry = load_registry()
    return {
        "registry_version": registry.get("version"),
        "sources": registry.get("sources", {}),
    }


@app.get("/v1/alive")
def get_alive(model: Annotated[str, Query(min_length=1, max_length=128)]):
    result = alive(model)
    status_code = 410 if result.status == "retired" else 200
    return JSONResponse(content=result.to_dict(), status_code=status_code)


@app.post("/v1/alive/batch")
def post_alive_batch(body: BatchRequest):
    results = check_many(body.models)
    payload = {
        "count": len(results),
        "retired_count": sum(1 for result in results if result.status == "retired"),
        "results": [result.to_dict() for result in results],
    }
    status_code = 410 if payload["retired_count"] else 200
    return JSONResponse(content=payload, status_code=status_code)


@app.get("/v1/resolve")
def get_resolve(model: Annotated[str, Query(min_length=1, max_length=128)]):
    result = alive(model)
    resolved = resolve(model)
    target = alive(resolved)
    return {
        "queried_model": result.queried_model or model,
        "canonical_model": result.canonical_model or model,
        "resolved": resolved,
        "replacement": result.replacement,
        "breaking_changes": target.breaking_changes,
    }


@app.get("/v1/ensure")
def get_ensure(
    model: Annotated[str, Query(min_length=1, max_length=128)],
    warn_deprecated: bool = False,
    strict_unknown: bool = False,
):
    from modelalive.exceptions import ModelDeprecatedError, ModelRetiredError, ModelUnknownError

    try:
        safe_model = ensure(
            model,
            warn_deprecated=warn_deprecated,
            strict_unknown=strict_unknown,
        )
    except (ModelRetiredError, ModelDeprecatedError, ModelUnknownError) as exc:
        return JSONResponse(content=exc.result.to_dict(), status_code=410)
    result = alive(safe_model)
    return {
        "queried_model": model,
        "safe_model": safe_model,
        "breaking_changes": result.breaking_changes,
    }


@app.get("/v1/registry")
def list_registry(
    status: Annotated[str | None, Query(description="active, deprecated, retired")] = None,
    provider: Annotated[str | None, Query(description="anthropic, openai, google")] = None,
):
    from modelalive.registry import list_models

    filtered = list_models(status=status, provider=provider)
    return {
        "registry_version": load_registry().get("version"),
        "count": len(filtered),
        "models": filtered,
    }


@app.get("/v1/validate")
def get_validate():
    issues = validate_registry()
    errors = [issue for issue in issues if issue.level == "error"]
    return {
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(issues) - len(errors),
        "issues": [{"level": i.level, "path": i.path, "message": i.message} for i in issues],
    }
