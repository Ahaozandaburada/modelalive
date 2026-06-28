from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from modelalive import __version__
from modelalive.check import alive, check_many, ensure, resolve_detail
from modelalive.registry import (
    get_model_entry,
    load_registry,
    oldest_source_age_days,
    registry_hash,
    registry_version,
)
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


class EnsureRequest(BaseModel):
    model: str = Field(..., min_length=1, max_length=256)
    warn_deprecated: bool = False
    strict_unknown: bool = False


def _problem(status: int, title: str, detail: str, *, type_suffix: str = "error") -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "type": f"https://modelalive.dev/errors/{type_suffix}",
            "title": title,
            "detail": detail,
            "status": status,
        },
        media_type="application/problem+json",
    )


def _alive_response(result, *, status_code: int | None = None) -> JSONResponse:
    code = status_code if status_code is not None else (410 if result.status == "retired" else 200)
    response = JSONResponse(content=result.to_dict(), status_code=code)
    response.headers["X-Model-Status"] = result.status
    response.headers["X-Model-Alive"] = "true" if result.alive else "false"
    if result.replacement:
        response.headers["X-Replacement"] = result.replacement
    response.headers["X-Registry-Version"] = result.registry_version or "unknown"
    response.headers["ETag"] = f'"{registry_hash()}"'
    return response


@app.get("/openapi.json", include_in_schema=False)
def openapi_json():
    return app.openapi()


@app.get("/v1/health")
def health() -> dict[str, object]:
    registry = load_registry()
    age = oldest_source_age_days()
    payload: dict[str, object] = {
        "status": "ok",
        "version": __version__,
        "registry_version": registry_version() or "unknown",
        "registry_etag": registry_hash(),
        "model_count": len(registry.get("models", {})),
        "alias_count": len(registry.get("aliases", {})),
    }
    if age is not None:
        payload["oldest_source_age_days"] = age
        if age > 7:
            payload["status"] = "degraded"
            payload["warning"] = f"Registry sources stale — oldest check is {age} days old"
    return payload


@app.get("/v1/sources")
def get_sources(response: Response):
    registry = load_registry()
    response.headers["ETag"] = f'"{registry_hash()}"'
    return {
        "registry_version": registry.get("version"),
        "sources": registry.get("sources", {}),
    }


@app.get("/v1/alive")
def get_alive(model: Annotated[str, Query(min_length=1, max_length=256)]):
    result = alive(model)
    return _alive_response(result)


@app.post("/v1/alive/batch")
def post_alive_batch(body: BatchRequest):
    results = check_many(body.models)
    payload = {
        "count": len(results),
        "retired_count": sum(1 for result in results if result.status == "retired"),
        "results": [result.to_dict() for result in results],
    }
    status_code = 410 if payload["retired_count"] else 200
    response = JSONResponse(content=payload, status_code=status_code)
    response.headers["ETag"] = f'"{registry_hash()}"'
    return response


@app.get("/v1/resolve")
def get_resolve(model: Annotated[str, Query(min_length=1, max_length=256)]):
    detail = resolve_detail(model)
    return {
        "queried_model": detail["queried_model"],
        "resolved": detail["resolved"],
        "chain": detail["chain"],
        "breaking_changes": detail["breaking_changes"],
    }


@app.get("/v1/ensure")
def get_ensure(
    model: Annotated[str, Query(min_length=1, max_length=256)],
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
        return _alive_response(exc.result, status_code=410)
    detail = resolve_detail(safe_model)
    response = JSONResponse(
        content={
            "queried_model": model,
            "safe_model": safe_model,
            "breaking_changes": detail["breaking_changes"],
        }
    )
    response.headers["X-Safe-Model"] = safe_model
    response.headers["ETag"] = f'"{registry_hash()}"'
    return response


@app.post("/v1/ensure")
def post_ensure(body: EnsureRequest):
    from modelalive.exceptions import ModelDeprecatedError, ModelRetiredError, ModelUnknownError

    try:
        safe_model = ensure(
            body.model,
            warn_deprecated=body.warn_deprecated,
            strict_unknown=body.strict_unknown,
        )
    except (ModelRetiredError, ModelDeprecatedError, ModelUnknownError) as exc:
        return _alive_response(exc.result, status_code=410)
    detail = resolve_detail(safe_model)
    response = JSONResponse(
        content={
            "queried_model": body.model,
            "safe_model": safe_model,
            "breaking_changes": detail["breaking_changes"],
        }
    )
    response.headers["X-Safe-Model"] = safe_model
    return response


@app.get("/v1/models/{model_id:path}")
def get_model(model_id: str, request: Request):
    from modelalive.lifecycle import effective_status

    result = alive(model_id)
    entry = get_model_entry(result.canonical_model or model_id)
    if entry is None and result.status == "unknown":
        return _problem(404, "Model not found", f"'{model_id}' is not in the registry", type_suffix="not-found")
    return {
        "model_id": result.canonical_model or model_id,
        "queried_model": result.queried_model,
        "status": result.status,
        "alive": result.alive,
        "provider": result.provider,
        "replacement": result.replacement,
        "breaking_changes": result.breaking_changes,
        "entry": entry,
        "effective_status": effective_status(entry, today=None) if entry else result.status,
    }


@app.get("/v1/registry")
def list_registry(
    response: Response,
    status: Annotated[str | None, Query(description="active, deprecated, retired")] = None,
    provider: Annotated[str | None, Query(description="anthropic, openai, google, groq, mistral, bedrock")] = None,
):
    from modelalive.registry import list_models

    etag = registry_hash()
    response.headers["ETag"] = f'"{etag}"'
    filtered = list_models(status=status, provider=provider)
    return {
        "registry_version": load_registry().get("version"),
        "registry_etag": etag,
        "count": len(filtered),
        "models": filtered,
    }


@app.get("/v1/expiring")
def get_expiring(
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    provider: Annotated[str | None, Query()] = None,
):
    from modelalive.expiring import list_expiring

    results = list_expiring(within_days=days, provider=provider)
    return {
        "within_days": days,
        "count": len(results),
        "models": [result.to_dict() for result in results],
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
