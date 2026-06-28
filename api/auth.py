"""Optional API key authentication for hosted deployment."""

from __future__ import annotations

import os
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from api.store import get_store

PUBLIC_PREFIXES = (
    "/v1/health",
    "/openapi.json",
    "/docs",
    "/redoc",
    "/v1/billing/plans",
    "/v1/billing/webhook",
    "/v1/billing/checkout",
    "/v1/billing/success",
    "/v1/billing/key",
)


def _is_public(path: str) -> bool:
    path = path.rstrip("/")
    return any(path == p or path.startswith(f"{p}/") for p in PUBLIC_PREFIXES)


def load_legacy_api_keys() -> set[str]:
    raw = os.environ.get("MODELALIVE_API_KEYS", "").strip()
    if not raw:
        return set()
    return {k.strip() for k in raw.split(",") if k.strip()}


def require_api_key_enabled() -> bool:
    return os.environ.get("MODELALIVE_REQUIRE_API_KEY", "").strip().lower() in {"1", "true", "yes"}


def resolve_api_key(provided: str) -> tuple[bool, str | None, str | None]:
    """Return (valid, key_prefix, tier)."""
    if provided in load_legacy_api_keys():
        return True, provided[:16], os.environ.get("MODELALIVE_DEFAULT_TIER", "pro")

    record = get_store().lookup_key(provided)
    if record:
        return True, record["key_prefix"], record["tier"]
    return False, None, None


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if _is_public(request.url.path):
            return await call_next(request)

        provided = request.headers.get("X-API-Key") or request.headers.get(
            "Authorization", ""
        ).removeprefix("Bearer ").strip()

        if require_api_key_enabled():
            if not provided:
                return _unauthorized(request, "API key required on hosted tier")
            valid, prefix, tier = resolve_api_key(provided)
            if not valid:
                return _unauthorized(request, "Invalid API key")
            request.state.api_key_id = prefix
            request.state.api_key_raw = provided
            request.state.tier = tier
        elif provided:
            valid, prefix, tier = resolve_api_key(provided)
            if valid:
                request.state.api_key_id = prefix
                request.state.api_key_raw = provided
                request.state.tier = tier

        response = await call_next(request)
        if getattr(request.state, "api_key_id", None):
            response.headers["X-Authenticated"] = "true"
            if getattr(request.state, "tier", None):
                response.headers["X-Usage-Tier"] = request.state.tier
        return response


def _unauthorized(request: Request, detail: str) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=401,
        content={
            "type": "https://modelalive.dev/errors/unauthorized",
            "title": "Invalid or missing API key",
            "detail": detail,
            "status": 401,
        },
        headers={"X-Request-ID": request_id} if request_id else {},
        media_type="application/problem+json",
    )
