from __future__ import annotations

from modelalive.types import AliveResult


class ModelLifecycleError(Exception):
    """Base error for model lifecycle issues."""

    def __init__(self, result: AliveResult) -> None:
        self.result = result
        super().__init__(result.message or result.model)


class ModelRetiredError(ModelLifecycleError):
    """Raised when a model is retired and API calls will fail."""


class ModelDeprecatedError(ModelLifecycleError):
    """Raised when a model is deprecated but not yet retired."""
