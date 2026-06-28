from __future__ import annotations

import os
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
from modelalive.providers import list_provider_keys, provider_label
from modelalive.validate import validate_registry

from api.middleware import RateLimitMiddleware, RequestIDMiddleware
from api.auth import APIKeyMiddleware
from api.usage import UsageMiddleware, current_usage, monthly_limit, tier_for_request
from api.billing import (
    create_checkout_session,
    create_portal_session,
    handle_webhook,
    list_plans,
    retrieve_key_for_session,
    stripe_enabled,
)
from api.store import get_store
from api.cache import attach_etag, etag_matches, not_modified
from api.status_page import html_response, json_response, status_payload

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

_rate_raw = os.environ.get("MODELALIVE_RATE_LIMIT", "").strip()
if _rate_raw and _rate_raw != "0":
    try:
        _rate_limit = int(_rate_raw)
        if _rate_limit > 0:
            app.add_middleware(RateLimitMiddleware, limit=_rate_limit)
    except ValueError:
        pass
app.add_middleware(RequestIDMiddleware)
app.add_middleware(UsageMiddleware)
app.add_middleware(APIKeyMiddleware)


class CheckoutRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    plan: str = Field(default="pro", pattern="^pro$")


class BatchRequest(BaseModel):
    models: list[str] = Field(..., min_length=1, max_length=100)


class EnsureRequest(BaseModel):
    model: str = Field(..., min_length=1, max_length=256)
    warn_deprecated: bool | None = None
    strict_unknown: bool | None = None


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


@app.get("/status", include_in_schema=False)
def service_status_html():
    return html_response(status_payload())


@app.get("/v1/status")
def service_status_json():
    return json_response(status_payload())


@app.get("/v1/health")
def health(request: Request):
    if etag_matches(request):
        return not_modified()
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
    response = JSONResponse(content=payload)
    attach_etag(response)
    return response


@app.get("/v1/providers")
def get_providers():
    keys = list_provider_keys()
    return {
        "count": len(keys),
        "providers": [{"key": k, "name": provider_label(k)} for k in keys],
    }


@app.get("/v1/sources")
def get_sources(request: Request):
    if etag_matches(request):
        return not_modified()
    registry = load_registry()
    response = JSONResponse(
        content={
            "registry_version": registry.get("version"),
            "sources": registry.get("sources", {}),
        }
    )
    attach_etag(response)
    return response


@app.get("/v1/alive")
def get_alive(request: Request, model: Annotated[str, Query(min_length=1, max_length=256)]):
    if etag_matches(request):
        return not_modified()
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
def get_resolve(request: Request, model: Annotated[str, Query(min_length=1, max_length=256)]):
    if etag_matches(request):
        return not_modified()
    detail = resolve_detail(model)
    response = JSONResponse(
        content={
            "queried_model": detail["queried_model"],
            "resolved": detail["resolved"],
            "chain": detail["chain"],
            "breaking_changes": detail["breaking_changes"],
        }
    )
    attach_etag(response)
    return response


def _ensure_error_response(exc) -> JSONResponse:
    from modelalive.exceptions import (
        ModelDeprecatedError,
        ModelExpiringSoonError,
        ModelRetiredError,
        ModelUnknownError,
    )

    if isinstance(exc, ModelUnknownError):
        detail = exc.result.message or f"'{exc.result.queried_model}' is not in the registry"
        return _problem(404, "Model not found", detail, type_suffix="not-found")
    if isinstance(exc, (ModelDeprecatedError, ModelExpiringSoonError)):
        return _alive_response(exc.result, status_code=409)
    return _alive_response(exc.result, status_code=410)


@app.get("/v1/ensure")
def get_ensure(
    model: Annotated[str, Query(min_length=1, max_length=256)],
    warn_deprecated: Annotated[bool | None, Query()] = None,
    strict_unknown: Annotated[bool | None, Query()] = None,
):
    from modelalive.exceptions import (
        ModelDeprecatedError,
        ModelExpiringSoonError,
        ModelRetiredError,
        ModelUnknownError,
    )

    try:
        safe_model = ensure(
            model,
            warn_deprecated=warn_deprecated,
            strict_unknown=strict_unknown,
        )
    except (
        ModelRetiredError,
        ModelDeprecatedError,
        ModelUnknownError,
        ModelExpiringSoonError,
    ) as exc:
        return _ensure_error_response(exc)
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
    from modelalive.exceptions import (
        ModelDeprecatedError,
        ModelExpiringSoonError,
        ModelRetiredError,
        ModelUnknownError,
    )

    try:
        safe_model = ensure(
            body.model,
            warn_deprecated=body.warn_deprecated,
            strict_unknown=body.strict_unknown,
        )
    except (
        ModelRetiredError,
        ModelDeprecatedError,
        ModelUnknownError,
        ModelExpiringSoonError,
    ) as exc:
        return _ensure_error_response(exc)
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
    request: Request,
    status: Annotated[str | None, Query(description="active, deprecated, retired")] = None,
    provider: Annotated[str | None, Query(description="anthropic, openai, google, groq, mistral, bedrock")] = None,
):
    from modelalive.registry import list_models

    if etag_matches(request):
        return not_modified()
    etag = registry_hash()
    filtered = list_models(status=status, provider=provider)
    response = JSONResponse(
        content={
            "registry_version": load_registry().get("version"),
            "registry_etag": etag,
            "count": len(filtered),
            "models": filtered,
        }
    )
    attach_etag(response)
    return response


@app.get("/v1/expiring")
def get_expiring(
    request: Request,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    provider: Annotated[str | None, Query()] = None,
):
    from modelalive.expiring import list_expiring

    if etag_matches(request):
        return not_modified()
    results = list_expiring(within_days=days, provider=provider)
    response = JSONResponse(
        content={
            "within_days": days,
            "count": len(results),
            "models": [result.to_dict() for result in results],
        }
    )
    attach_etag(response)
    return response


@app.get("/v1/billing/plans")
def billing_plans():
    payload = list_plans()
    payload["stripe_enabled"] = stripe_enabled()
    payload["upgrade_url"] = f"{os.environ.get('MODELALIVE_PUBLIC_URL', 'https://modelalive.fly.dev')}/v1/billing/checkout"
    return payload


@app.post("/v1/billing/checkout")
def billing_checkout(body: CheckoutRequest):
    try:
        return create_checkout_session(email=body.email, plan=body.plan)
    except (RuntimeError, ValueError) as exc:
        return _problem(503 if isinstance(exc, RuntimeError) else 400, "Checkout unavailable", str(exc))


@app.post("/v1/billing/webhook")
async def billing_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature")
    try:
        return handle_webhook(payload, sig)
    except Exception as exc:
        return _problem(400, "Webhook error", str(exc))


@app.get("/v1/billing/key")
def billing_retrieve_key(session_id: Annotated[str, Query(min_length=8)]):
    result = retrieve_key_for_session(session_id)
    if result is None:
        return _problem(404, "Session not found", "Unknown checkout session", type_suffix="not-found")
    return result


@app.get("/v1/billing/success")
def billing_success(session_id: Annotated[str, Query(min_length=8)]):
    result = retrieve_key_for_session(session_id)
    if result is None:
        return _problem(404, "Session not found", "Unknown checkout session", type_suffix="not-found")
    if result.get("api_key"):
        return {
            "message": "Save your API key now — it will not be shown again.",
            **result,
        }
    return result


@app.post("/v1/billing/portal")
def billing_portal(request: Request):
    raw_key = getattr(request.state, "api_key_raw", None)
    if not raw_key:
        return _problem(401, "API key required", "Provide X-API-Key to manage subscription")
    customer_id = get_store().get_stripe_customer_id(raw_key)
    if not customer_id:
        return _problem(404, "No subscription", "This key is not linked to Stripe")
    try:
        return create_portal_session(stripe_customer_id=customer_id)
    except RuntimeError as exc:
        return _problem(503, "Portal unavailable", str(exc))


@app.get("/v1/usage")
def get_usage(request: Request):
    """Current billing-period usage for this client (IP or API key)."""
    tier = tier_for_request(request)
    count = current_usage(request)
    return {
        "tier": tier,
        "checks_used": count,
        "checks_limit": monthly_limit(tier),
        "checks_remaining": max(0, monthly_limit(tier) - count),
        "upgrade_url": f"{os.environ.get('MODELALIVE_PUBLIC_URL', 'https://modelalive.fly.dev')}/v1/billing/plans",
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
