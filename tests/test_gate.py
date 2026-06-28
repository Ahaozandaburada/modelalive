"""Tests for gate context manager and decorator."""

from __future__ import annotations

import modelalive
from modelalive.gate import gate, require_alive


def test_gate_yields_safe_model():
    with gate("claude-sonnet-4-20250514") as safe:
        assert safe == "claude-sonnet-4-6"


def test_gate_active_unchanged():
    with gate("claude-sonnet-4-6") as safe:
        assert safe == "claude-sonnet-4-6"


@require_alive(param="model")
def _echo(model: str) -> str:
    return model


def test_require_alive_decorator():
    assert _echo(model="claude-sonnet-4-20250514") == "claude-sonnet-4-6"


@require_alive("gpt-4o")
def _fixed_model(model: str) -> str:
    return model


def test_require_alive_fixed_model():
    assert _fixed_model(model="ignored") == "gpt-4o"
