"""Model Alive — pre-flight check for LLM model IDs."""

from modelalive.check import alive, check, check_many, ensure, resolve
from modelalive.exceptions import (
    ModelDeprecatedError,
    ModelRetiredError,
    ModelUnknownError,
)
from modelalive.types import AliveResult
from modelalive.validate import assert_registry_valid, validate_registry

__all__ = [
    "alive",
    "check",
    "check_many",
    "ensure",
    "resolve",
    "AliveResult",
    "ModelRetiredError",
    "ModelDeprecatedError",
    "ModelUnknownError",
    "validate_registry",
    "assert_registry_valid",
]
__version__ = "0.3.0"
