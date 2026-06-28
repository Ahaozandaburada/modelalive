"""Property-based and fuzz tests."""

from __future__ import annotations

from datetime import date

import pytest

from modelalive import alive, ensure, resolve
from modelalive.normalize import normalize_model

pytest.importorskip("hypothesis")
from hypothesis import given, settings
from hypothesis import strategies as st


@settings(max_examples=50, deadline=None)
@given(st.text(min_size=1, max_size=64, alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="._:-")))
def test_alive_never_crashes_on_plausible_ids(model_id: str):
    try:
        cleaned = normalize_model(model_id)
    except ValueError:
        return
    result = alive(cleaned, today=date(2026, 6, 28))
    assert result.status in {"active", "deprecated", "retired", "unknown"}
    assert isinstance(result.alive, bool)


@settings(max_examples=30, deadline=None)
@given(st.sampled_from([
    "claude-sonnet-4-20250514",
    "gemini-2.0-flash",
    "gpt-4-0314",
    "mistral-medium-2312",
    "llama3-70b-8192",
]))
def test_ensure_retired_always_returns_active(model_id: str):
    safe = ensure(model_id, today=date(2026, 6, 28))
    target = alive(safe, today=date(2026, 6, 28))
    assert target.status in {"active", "unknown"}


@settings(max_examples=30, deadline=None)
@given(st.sampled_from([
    "claude-sonnet-4-6",
    "gpt-5.5",
    "gemini-3.5-flash",
]))
def test_resolve_idempotent_on_active(model_id: str):
    assert resolve(model_id) == model_id
    assert ensure(model_id) == model_id
