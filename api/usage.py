"""Usage metering for hosted API billing tiers."""

from __future__ import annotations

import os
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from api.store import get_store

METERED_PREFIXES = ("/v1/alive", "/v1/ensure", "/v1/resolve")
BILLING_PUBLIC = ("/v1/billing/plans", "/v1/billing/webhook", "/v1/billing/checkout", "/v1/billing/success", "/v1/billing/key")


def _is_metered(path: str) -> bool:
    path = path.rstrip("/")
    if path in BILLING_PUBLIC or any(path.startswith(f"{p}/") for p in BILLING_PUBLIC):
        return False
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
    """In-memory IP usage for anonymous free tier."""

    counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    lock: threading.Lock = field(default_factory=threading.Lock)

    def key_for_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        if request.client:
            return f"ip:{request.client.host}"
        return "ip:unknown"

    def increment_ip(self, request: Request) -> int:
        bucket = self.key_for_ip(request)
        with self.lock:
            self.counts[bucket] += 1
            return self.counts[bucket]

    def get_ip(self, request: Request) -> int:
        return self.counts.get(self.key_for_ip(request), 0)


_ip_tracker = UsageTracker()


def get_ip_tracker() -> UsageTracker:
    return _ip_tracker


def reset_ip_tracker() -> None:
    """Clear in-memory IP usage (for tests)."""
    with _ip_tracker.lock:
        _ip_tracker.counts.clear()


def tier_for_request(request: Request) -> str:
    if getattr(request.state, "tier", None):
        return request.state.tier
    if getattr(request.state, "api_key_id", None):
        return os.environ.get("MODELALIVE_DEFAULT_TIER", "pro")
    return "free"


def monthly_limit(tier: str) -> int:
    return TIERS.get(tier, TIERS["free"])["monthly_checks"]


def enforce_quota() -> bool:
    return os.environ.get("MODELALIVE_ENFORCE_QUOTA", "").strip().lower() in {"1", "true", "yes"}


def current_usage(request: Request) -> int:
    raw_key = getattr(request.state, "api_key_raw", None)
    if raw_key:
        usage, _ = get_store().get_usage(raw_key)
        return usage
    return _ip_tracker.get_ip(request)


def increment_usage(request: Request) -> int:
    raw_key = getattr(request.state, "api_key_raw", None)
    if raw_key:
        return get_store().increment_usage(raw_key)
    return _ip_tracker.increment_ip(request)


class UsageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path.rstrip("/")
        if not _is_metered(path):
            return await call_next(request)

        tier = tier_for_request(request)
        limit = monthly_limit(tier)
        current = current_usage(request)

        if enforce_quota() and current >= limit:
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=402,
                content={
                    "type": "https://modelalive.dev/errors/quota-exceeded",
                    "title": "Monthly quota exceeded",
                    "detail": (
                        f"Tier {tier!r} allows {limit} checks/month. "
                        f"Upgrade at {os.environ.get('MODELALIVE_PUBLIC_URL', 'https://modelalive.fly.dev')}/v1/billing/plans"
                    ),
                    "status": 402,
                },
                headers={"X-Request-ID": request_id} if request_id else {},
                media_type="application/problem+json",
            )

        response = await call_next(request)
        count = increment_usage(request)
        response.headers["X-Usage-Count"] = str(count)
        response.headers["X-Usage-Limit"] = str(limit)
        response.headers["X-Usage-Tier"] = tier
        return response
