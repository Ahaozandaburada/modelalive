"""Usage metering for hosted API billing tiers."""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

METERED_PREFIXES = ("/v1/alive", "/v1/ensure", "/v1/resolve")


def _is_metered(path: str) -> bool:
    path = path.rstrip("/")
    if path == "/v1/alive/batch":
        return True
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in METERED_PREFIXES)

TIERS: dict[str, dict[str, int]] = {
    "free": {"monthly_checks": 100},
    "pro": {"monthly_checks": 100_000},
    "enterprise": {"monthly_checks": 10_000_000},
}


@dataclass
class UsageTracker:
    """In-memory usage counter — replace with Redis/Postgres for production billing."""

    counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    lock: threading.Lock = field(default_factory=threading.Lock)

    def key_for(self, request: Request) -> str:
        api_key = getattr(request.state, "api_key_id", None)
        if api_key:
            return f"key:{api_key}"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        if request.client:
            return f"ip:{request.client.host}"
        return "ip:unknown"

    def increment(self, request: Request) -> int:
        bucket = self.key_for(request)
        with self.lock:
            self.counts[bucket] += 1
            return self.counts[bucket]

    def get(self, request: Request) -> int:
        return self.counts.get(self.key_for(request), 0)

    def snapshot(self) -> dict[str, int]:
        with self.lock:
            return dict(self.counts)


_tracker = UsageTracker()


def get_tracker() -> UsageTracker:
    return _tracker


def tier_for_request(request: Request) -> str:
    if getattr(request.state, "api_key_id", None):
        return os.environ.get("MODELALIVE_DEFAULT_TIER", "pro")
    return "free"


def monthly_limit(tier: str) -> int:
    return TIERS.get(tier, TIERS["free"])["monthly_checks"]


def enforce_quota() -> bool:
    return os.environ.get("MODELALIVE_ENFORCE_QUOTA", "").strip().lower() in {"1", "true", "yes"}


class UsageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path.rstrip("/")
        if not _is_metered(path):
            return await call_next(request)

        tier = tier_for_request(request)
        limit = monthly_limit(tier)
        current = _tracker.get(request)

        if enforce_quota() and current >= limit:
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=402,
                content={
                    "type": "https://modelalive.dev/errors/quota-exceeded",
                    "title": "Monthly quota exceeded",
                    "detail": f"Tier {tier!r} allows {limit} checks/month. Upgrade at modelalive.dev/pricing",
                    "status": 402,
                },
                headers={"X-Request-ID": request_id} if request_id else {},
                media_type="application/problem+json",
            )

        response = await call_next(request)
        count = _tracker.increment(request)
        response.headers["X-Usage-Count"] = str(count)
        response.headers["X-Usage-Limit"] = str(limit)
        response.headers["X-Usage-Tier"] = tier
        return response
