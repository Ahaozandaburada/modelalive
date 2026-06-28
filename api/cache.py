"""Registry-backed HTTP caching (ETag + If-None-Match)."""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response

from modelalive.registry import registry_hash


def etag_value() -> str:
    return f'"{registry_hash()}"'


def if_none_match(request: Request) -> str | None:
    raw = request.headers.get("if-none-match", "").strip()
    return raw or None


def etag_matches(request: Request, etag: str | None = None) -> bool:
    header = if_none_match(request)
    if not header:
        return False
    current = etag or etag_value()
    candidates = {tag.strip() for tag in header.split(",")}
    normalized = {tag.removeprefix("W/") for tag in candidates}
    return current in candidates or current in normalized


def not_modified(etag: str | None = None) -> Response:
    tag = etag or etag_value()
    return Response(status_code=304, headers={"ETag": tag})


def attach_etag(response: Response, etag: str | None = None) -> Response:
    response.headers["ETag"] = etag or etag_value()
    return response
