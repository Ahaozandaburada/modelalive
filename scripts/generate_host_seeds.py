#!/usr/bin/env python3
"""Generate Bedrock and Azure host-specific registry entries from canonical models."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "registry" / "models.json"
BEDROCK_SEED = ROOT / "registry" / "seeds" / "bedrock.json"
AZURE_SEED = ROOT / "registry" / "seeds" / "azure.json"

BEDROCK_MIGRATE = "https://docs.aws.amazon.com/bedrock/latest/userguide/model-lifecycle.html"
AZURE_MIGRATE = "https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/model-retirements"

# Bedrock inference profile ID -> canonical model ID
BEDROCK_PRIMARY: dict[str, str] = {
    "anthropic.claude-sonnet-4-6-v1:0": "claude-sonnet-4-6",
    "anthropic.claude-sonnet-4-20250514-v1:0": "claude-sonnet-4-20250514",
    "anthropic.claude-opus-4-8-v1:0": "claude-opus-4-8",
    "anthropic.claude-opus-4-20250514-v1:0": "claude-opus-4-20250514",
    "anthropic.claude-haiku-4-5-20251001-v1:0": "claude-haiku-4-5-20251001",
    "anthropic.claude-3-5-sonnet-20241022-v2:0": "claude-3-5-sonnet-20241022",
    "anthropic.claude-3-5-haiku-20241022-v1:0": "claude-3-5-haiku-20241022",
    "anthropic.claude-3-opus-20240229-v1:0": "claude-3-opus-20240229",
    "anthropic.claude-3-sonnet-20240229-v1:0": "claude-3-sonnet-20240229",
    "anthropic.claude-3-haiku-20240307-v1:0": "claude-3-haiku-20240307",
    "meta.llama3-70b-instruct-v1:0": "meta-llama/Llama-3.3-70B-Instruct",
    "meta.llama3-8b-instruct-v1:0": "meta-llama/Llama-3.1-8B-Instruct",
    "amazon.titan-text-premier-v1:0": "amazon.titan-text-premier-v1",
    "amazon.nova-pro-v1:0": "amazon.nova-pro-v1",
    "amazon.nova-lite-v1:0": "amazon.nova-lite-v1",
    "cohere.command-r-v1:0": "command-r",
    "cohere.command-r-plus-v1:0": "command-r-plus",
    "mistral.mistral-large-2402-v1:0": "mistral-large-2411",
    "mistral.mixtral-8x7b-instruct-v0:1": "mixtral-8x7b-instruct",
}

# Regional / cross-region aliases -> primary Bedrock ID
BEDROCK_REGIONAL: dict[str, str] = {
    "us.anthropic.claude-sonnet-4-6-v1:0": "anthropic.claude-sonnet-4-6-v1:0",
    "eu.anthropic.claude-sonnet-4-6-v1:0": "anthropic.claude-sonnet-4-6-v1:0",
    "us.anthropic.claude-opus-4-8-v1:0": "anthropic.claude-opus-4-8-v1:0",
    "eu.anthropic.claude-opus-4-8-v1:0": "anthropic.claude-opus-4-8-v1:0",
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0": "anthropic.claude-3-5-sonnet-20241022-v2:0",
}

# Azure deployment alias -> canonical model ID
AZURE_PRIMARY: dict[str, str] = {
    "azure/gpt-5.5": "gpt-5.5",
    "azure/gpt-5.5-pro": "gpt-5.5-pro",
    "azure/gpt-5.4-mini": "gpt-5.4-mini",
    "azure/gpt-4o": "gpt-4o",
    "azure/gpt-4o-mini": "gpt-4o-mini",
    "azure/o3": "o3",
    "azure/o3-mini": "o3-mini",
    "azure/o4-mini": "o4-mini",
    "azure/text-embedding-3-large": "text-embedding-3-large",
    "azure/text-embedding-3-small": "text-embedding-3-small",
    "azure/claude-sonnet-4-6": "claude-sonnet-4-6",
    "azure/claude-opus-4-8": "claude-opus-4-8",
    "azure/claude-haiku-4-5": "claude-haiku-4-5-20251001",
}


def _host_replacement(
    repl: str | None,
    *,
    primary_map: dict[str, str],
) -> str | None:
    if not repl:
        return None
    for host_id, canonical in primary_map.items():
        if canonical == repl:
            return host_id
    return repl


def _host_entry(
    canonical_id: str,
    entry: dict,
    *,
    provider: str,
    source_key: str,
    migrate_url: str,
    primary_map: dict[str, str],
) -> dict:
    repl = _host_replacement(entry.get("replacement"), primary_map=primary_map)
    return {
        "provider": provider,
        "status": entry.get("status", "active"),
        "deprecated_at": entry.get("deprecated_at"),
        "retired_at": entry.get("retired_at"),
        "replacement": repl,
        "breaking_changes": list(entry.get("breaking_changes") or []),
        "migrate_url": migrate_url,
        "source": source_key,
        "notes": f"Host entry for {canonical_id}",
    }


def _fallback_entry(provider: str, source_key: str, migrate_url: str) -> dict:
    return {
        "provider": provider,
        "status": "active",
        "replacement": None,
        "breaking_changes": [],
        "migrate_url": migrate_url,
        "source": source_key,
        "notes": "Host entry — canonical model pending full crosswalk",
    }


def generate(*, today: date | None = None) -> tuple[dict, dict]:
    _ = today or date.today()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    models = registry.get("models", {})
    checked = date.today().isoformat()

    bedrock_models: dict[str, dict] = {}
    bedrock_aliases: dict[str, str] = dict(BEDROCK_REGIONAL)

    for host_id, canonical in BEDROCK_PRIMARY.items():
        entry = models.get(canonical)
        if entry:
            bedrock_models[host_id] = _host_entry(
                canonical,
                entry,
                provider="bedrock",
                source_key="bedrock",
                migrate_url=BEDROCK_MIGRATE,
                primary_map=BEDROCK_PRIMARY,
            )
        else:
            bedrock_models[host_id] = _fallback_entry("bedrock", "bedrock", BEDROCK_MIGRATE)

    # Strip :0 for lookup alias (some SDKs omit suffix)
    for host_id in list(bedrock_models):
        bare = host_id.removesuffix(":0")
        if bare != host_id and bare not in bedrock_models:
            bedrock_aliases[bare] = host_id

    azure_models: dict[str, dict] = {}
    azure_aliases: dict[str, str] = {}

    for host_id, canonical in AZURE_PRIMARY.items():
        entry = models.get(canonical)
        if entry:
            azure_models[host_id] = _host_entry(
                canonical,
                entry,
                provider="azure",
                source_key="azure",
                migrate_url=AZURE_MIGRATE,
                primary_map=AZURE_PRIMARY,
            )
        else:
            azure_models[host_id] = _fallback_entry("azure", "azure", AZURE_MIGRATE)

    bedrock_seed = {
        "sources": {
            "bedrock": {
                "url": BEDROCK_MIGRATE,
                "checked_at": checked,
            }
        },
        "aliases": bedrock_aliases,
        "models": bedrock_models,
    }
    azure_seed = {
        "sources": {
            "azure": {
                "url": AZURE_MIGRATE,
                "checked_at": checked,
            }
        },
        "aliases": azure_aliases,
        "models": azure_models,
    }
    return bedrock_seed, azure_seed


def main() -> int:
    bedrock_seed, azure_seed = generate()
    BEDROCK_SEED.write_text(json.dumps(bedrock_seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    AZURE_SEED.write_text(json.dumps(azure_seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Host seeds: bedrock={len(bedrock_seed['models'])} models, "
        f"azure={len(azure_seed['models'])} models"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
