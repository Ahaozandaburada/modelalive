from datetime import date

import pytest

from modelalive import alive, check, resolve
from modelalive.exceptions import ModelRetiredError


def test_retired_model_not_alive():
    result = alive("claude-sonnet-4-20250514")
    assert result.alive is False
    assert result.status == "retired"
    assert result.replacement == "claude-sonnet-4-6"


def test_check_raises_on_retired():
    with pytest.raises(ModelRetiredError) as exc:
        check("claude-sonnet-4-20250514")
    assert exc.value.result.replacement == "claude-sonnet-4-6"


def test_active_model_alive():
    result = alive("claude-sonnet-4-6")
    assert result.alive is True
    assert result.status == "active"


def test_unknown_model_assumed_alive():
    result = alive("some-future-model-xyz")
    assert result.alive is True
    assert result.status == "unknown"


def test_resolve_returns_replacement():
    assert resolve("claude-sonnet-4-20250514") == "claude-sonnet-4-6"
    assert resolve("claude-sonnet-4-6") == "claude-sonnet-4-6"


def test_deprecated_mythos_still_alive():
    result = alive("claude-mythos-preview", today=date(2026, 6, 28))
    assert result.alive is True
    assert result.status == "deprecated"
    assert result.days_until_retirement == 2
