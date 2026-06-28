"""Optional API key authentication for hosted deployment."""

from __future__ import annotations

import os
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

PUBLIC_PATHS = {"/v1/health", "/openapi.json", "/docs", "/redoc"}


def load_api_keys() -> set[str]:
    raw = os.environ.get("MODELALIVE_API_KEYS", "").strip()
    if not raw:
        return set()
    return {k.strip() for k in raw.split(",") if k.strip()}


def require_api_key_enabled() -> bool:
    return os.environ.get("MODELALIVE_REQUIRE_API_KEY", "").strip().lower() in {"1", "true", "yes"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, keys: set[str]):
        super().__init__(app)
        self.keys = keys

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        provided = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not provided or provided not in self.keys:
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=401,
                content={
                    "type": "https://modelalive.dev/errors/unauthorized",
                    "title": "Invalid or missing API key",
                    "detail": "Provide X-API-Key or Authorization: Bearer <key>",
                    "status": 401,
                },
                headers={"X-Request-ID": request_id} if request_id else {},
                media_type="application/problem+json",
            )

        request.state.api_key_id = provided[:8]
        response = await call_next(request)
        response.headers["X-Authenticated"] = "true"
        return response
