"""HTTP middleware: request tracing and optional rate limiting."""

from __future__ import annotations

import os
import time
import uuid
from collections import defaultdict, deque
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory sliding-window rate limiter per client IP."""

    def __init__(self, app, *, limit: int, window_seconds: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    @classmethod
    def from_env(cls, app):
        raw = os.environ.get("MODELALIVE_RATE_LIMIT", "").strip()
        if not raw or raw == "0":
            return None
        try:
            limit = int(raw)
        except ValueError:
            return None
        if limit <= 0:
            return None
        return cls(app, limit=limit)

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in {"/v1/health", "/openapi.json"}:
            return await call_next(request)

        now = time.monotonic()
        key = self._client_key(request)
        bucket = self._hits[key]
        while bucket and now - bucket[0] > self.window:
            bucket.popleft()

        if len(bucket) >= self.limit:
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=429,
                content={
                    "type": "https://modelalive.dev/errors/rate-limit",
                    "title": "Rate limit exceeded",
                    "detail": f"Limit is {self.limit} requests per {self.window}s",
                    "status": 429,
                },
                headers={"X-Request-ID": request_id} if request_id else {},
                media_type="application/problem+json",
            )

        bucket.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.limit - len(bucket)))
        return response
