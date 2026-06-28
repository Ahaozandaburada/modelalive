"""Model Alive — pre-flight check for LLM model IDs."""

from modelalive.check import alive, check, resolve
from modelalive.exceptions import ModelDeprecatedError, ModelRetiredError
from modelalive.types import AliveResult

__all__ = [
    "alive",
    "check",
    "resolve",
    "AliveResult",
    "ModelRetiredError",
    "ModelDeprecatedError",
]
__version__ = "0.1.0"
