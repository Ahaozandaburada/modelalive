from __future__ import annotations

from modelalive.types import AliveResult


class ModelLifecycleError(Exception):
    """Base error for model lifecycle issues."""

    def __init__(self, result: AliveResult) -> None:
        self.result = result
        super().__init__(self._format_message(result))

    @staticmethod
    def _format_message(result: AliveResult) -> str:
        if result.message:
            return result.message
        return f"Model lifecycle error for {result.queried_model or result.model}"


class ModelRetiredError(ModelLifecycleError):
    """Raised when a model is retired and API calls will fail."""


class ModelDeprecatedError(ModelLifecycleError):
    """Raised when a model is deprecated but not yet retired."""


class ModelUnknownError(ModelLifecycleError):
    """Raised when a model is not in the registry and strict mode is enabled."""


class ModelExpiringSoonError(ModelLifecycleError):
    """Raised when a model retires within the configured warn_days window."""
