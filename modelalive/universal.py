"""Universal model ID resolution across all inference surfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from modelalive.normalize import normalize_model
from modelalive.registry import get_model_entry, load_registry, resolve_alias


@dataclass
class UniversalResolve:
    queried_model: str
    normalized: str
    resolved: str
    chain: list[str] = field(default_factory=list)
    in_registry: bool = False
    surface: str | None = None


def _slash_variants(model: str) -> list[str]:
    """Generate candidate IDs from provider/model and host-specific paths."""
    out: list[str] = []
    if "/" not in model:
        return out
    parts = model.split("/")
    out.append(parts[-1])
    if len(parts) >= 2:
        out.append(f"{parts[-2]}/{parts[-1]}")
    if len(parts) >= 3:
        out.append("/".join(parts[-2:]))
    # OpenRouter lowercase slugs
    out.append(model.lower())
    out.append(parts[-1].lower())
    # meta-llama/llama-3.3-70b-instruct → meta-llama/Llama-3.3-70B-Instruct style
    if parts[-1]:
        titled = parts[-1].replace("llama-", "Llama-").replace("instruct", "Instruct")
        out.append(titled)
    deduped: list[str] = []
    seen: set[str] = set()
    for item in out:
        if item and item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def _lookup_alias(model: str, *, registry_path: str | Path | None) -> tuple[str, list[str]] | None:
    registry = load_registry(registry_path)
    aliases: dict[str, str] = registry.get("aliases", {})
    if model in aliases:
        canonical, chain = resolve_alias(model, registry_path=registry_path)
        return canonical, chain
    lower_map = {k.lower(): k for k in aliases}
    key = lower_map.get(model.lower())
    if key:
        canonical, chain = resolve_alias(key, registry_path=registry_path)
        return canonical, chain
    return None


def universal_resolve(
    model: str,
    *,
    registry_path: str | Path | None = None,
) -> UniversalResolve:
    """Resolve any model string through normalization, aliases, and host heuristics."""
    normalized = normalize_model(model)
    chain = [model.strip(), normalized]

    # Prefer alias chain over passthrough aggregator routes
    alias_hit = _lookup_alias(normalized, registry_path=registry_path)
    if alias_hit:
        canonical, alias_chain = alias_hit
        if get_model_entry(canonical, registry_path=registry_path):
            merged = chain + alias_chain[1:]
            entry = get_model_entry(canonical, registry_path=registry_path) or {}
            return UniversalResolve(
                queried_model=model,
                normalized=normalized,
                resolved=canonical,
                chain=merged,
                in_registry=True,
                surface=entry.get("provider"),
            )

    # Direct registry hit (skip OpenRouter passthrough when alias exists)
    entry = get_model_entry(normalized, registry_path=registry_path)
    if entry is not None:
        if entry.get("provider") == "openrouter":
            alias_hit = _lookup_alias(normalized, registry_path=registry_path)
            if alias_hit:
                canonical, alias_chain = alias_hit
                target_entry = get_model_entry(canonical, registry_path=registry_path)
                if target_entry and target_entry.get("provider") != "openrouter":
                    merged = chain + alias_chain[1:]
                    return UniversalResolve(
                        queried_model=model,
                        normalized=normalized,
                        resolved=canonical,
                        chain=merged,
                        in_registry=True,
                        surface=target_entry.get("provider"),
                    )
        return UniversalResolve(
            queried_model=model,
            normalized=normalized,
            resolved=normalized,
            chain=chain,
            in_registry=True,
            surface=entry.get("provider"),
        )

    # Slash / host path heuristics (OpenRouter, Together, HF, Bedrock-style paths)
    for variant in _slash_variants(normalized):
        try:
            candidate = normalize_model(variant)
        except ValueError:
            continue
        if get_model_entry(candidate, registry_path=registry_path):
            entry = get_model_entry(candidate, registry_path=registry_path) or {}
            return UniversalResolve(
                queried_model=model,
                normalized=normalized,
                resolved=candidate,
                chain=chain + [candidate],
                in_registry=True,
                surface=entry.get("provider"),
            )
        alias_hit = _lookup_alias(candidate, registry_path=registry_path)
        if alias_hit:
            canonical, alias_chain = alias_hit
            if get_model_entry(canonical, registry_path=registry_path):
                entry = get_model_entry(canonical, registry_path=registry_path) or {}
                return UniversalResolve(
                    queried_model=model,
                    normalized=normalized,
                    resolved=canonical,
                    chain=chain + alias_chain,
                    in_registry=True,
                    surface=entry.get("provider"),
                )

    return UniversalResolve(
        queried_model=model,
        normalized=normalized,
        resolved=normalized,
        chain=chain,
        in_registry=False,
        surface=None,
    )
