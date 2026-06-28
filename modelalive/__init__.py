"""Model Alive — pre-flight check for LLM model IDs."""

from modelalive.check import alive, check, check_many, ensure, resolve, resolve_detail
from modelalive.exceptions import (
    ModelDeprecatedError,
    ModelExpiringSoonError,
    ModelRetiredError,
    ModelUnknownError,
)
from modelalive.expiring import list_expiring
from modelalive.gate import gate, require_alive
from modelalive.scan import scan_path
from modelalive.types import AliveResult
from modelalive.providers import list_provider_keys, provider_label
from modelalive.validate import assert_registry_valid, validate_registry

__all__ = [
    "alive",
    "check",
    "check_many",
    "ensure",
    "resolve",
    "resolve_detail",
    "gate",
    "require_alive",
    "list_expiring",
    "scan_path",
    "AliveResult",
    "ModelRetiredError",
    "ModelDeprecatedError",
    "ModelUnknownError",
    "ModelExpiringSoonError",
    "validate_registry",
    "assert_registry_valid",
    "list_provider_keys",
    "provider_label",
]
__version__ = "0.8.0"
