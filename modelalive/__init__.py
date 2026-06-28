"""Model Alive — pre-flight check for LLM model IDs."""

from modelalive.check import alive, check, check_many, resolve
from modelalive.exceptions import ModelDeprecatedError, ModelRetiredError
from modelalive.types import AliveResult
from modelalive.validate import assert_registry_valid, validate_registry

__all__ = [
    "alive",
    "check",
    "check_many",
    "resolve",
    "AliveResult",
    "ModelRetiredError",
    "ModelDeprecatedError",
    "validate_registry",
    "assert_registry_valid",
]
__version__ = "0.2.1"
