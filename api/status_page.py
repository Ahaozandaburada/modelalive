"""Public status page (HTML + JSON)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.responses import HTMLResponse, JSONResponse

from modelalive import __version__
from modelalive.registry import load_registry, oldest_source_age_days, registry_hash, registry_version
from modelalive.validate import validate_registry


def status_payload() -> dict[str, object]:
    registry = load_registry()
    age = oldest_source_age_days()
    issues = validate_registry()
    errors = [i for i in issues if i.level == "error"]
    state = "operational"
    if errors:
        state = "degraded"
    elif age is not None and age > 7:
        state = "degraded"
    return {
        "status": state,
        "service": "Model Alive API",
        "version": __version__,
        "registry_version": registry_version() or "unknown",
        "registry_etag": registry_hash(),
        "model_count": len(registry.get("models", {})),
        "alias_count": len(registry.get("aliases", {})),
        "provider_count": len(registry.get("sources", {})),
        "oldest_source_age_days": age,
        "validation_errors": len(errors),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoints": {
            "health": "/v1/health",
            "alive": "/v1/alive?model=",
            "docs": "/docs",
        },
    }


def status_html(payload: dict[str, object]) -> str:
    state = str(payload.get("status", "unknown"))
    color = "#22c55e" if state == "operational" else "#f59e0b"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Model Alive — Status</title>
  <style>
    :root {{ font-family: ui-sans-serif, system-ui, sans-serif; background: #0b0f14; color: #e5e7eb; }}
    body {{ max-width: 720px; margin: 2rem auto; padding: 0 1rem; }}
    .badge {{ display: inline-block; padding: .35rem .75rem; border-radius: 999px; background: {color}22; color: {color}; font-weight: 600; }}
    h1 {{ font-size: 1.75rem; margin-bottom: .25rem; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1.5rem; }}
    .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 1rem; }}
    .label {{ color: #9ca3af; font-size: .85rem; }}
    .value {{ font-size: 1.25rem; font-weight: 600; margin-top: .25rem; }}
    a {{ color: #60a5fa; }}
    footer {{ margin-top: 2rem; color: #6b7280; font-size: .85rem; }}
  </style>
</head>
<body>
  <p class="badge">{state.upper()}</p>
  <h1>Model Alive</h1>
  <p>Universal LLM model lifecycle pre-flight API</p>
  <div class="grid">
    <div class="card"><div class="label">Version</div><div class="value">{payload.get("version")}</div></div>
    <div class="card"><div class="label">Models tracked</div><div class="value">{payload.get("model_count")}</div></div>
    <div class="card"><div class="label">Providers</div><div class="value">{payload.get("provider_count")}</div></div>
    <div class="card"><div class="label">Registry age (days)</div><div class="value">{payload.get("oldest_source_age_days", "—")}</div></div>
  </div>
  <p style="margin-top:1.5rem">
    <a href="/v1/health">JSON health</a> ·
    <a href="/docs">API docs</a> ·
    <a href="https://github.com/Ahaozandaburada/modelalive">GitHub</a>
  </p>
  <footer>Updated {payload.get("timestamp")} · registry {payload.get("registry_version")}</footer>
</body>
</html>"""


def json_response(payload: dict[str, object]) -> JSONResponse:
    return JSONResponse(content=payload)


def html_response(payload: dict[str, object]) -> HTMLResponse:
    return HTMLResponse(content=status_html(payload))
