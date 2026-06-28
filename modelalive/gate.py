from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import date
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

from modelalive.check import ensure

F = TypeVar("F", bound=Callable[..., Any])


@contextmanager
def gate(
    model: str,
    *,
    warn_deprecated: bool | None = None,
    strict_unknown: bool | None = None,
    warn_days: int | None = None,
    registry_path: str | Path | None = None,
    today: date | None = None,
) -> Iterator[str]:
    """Context manager: yield a safe model ID for the block body."""
    safe_model = ensure(
        model,
        warn_deprecated=warn_deprecated,
        strict_unknown=strict_unknown,
        warn_days=warn_days,
        registry_path=registry_path,
        today=today,
    )
    yield safe_model


def require_alive(
    model: str | None = None,
    *,
    param: str = "model",
    warn_deprecated: bool | None = None,
    strict_unknown: bool | None = None,
    warn_days: int | None = None,
    registry_path: str | Path | None = None,
) -> Callable[[F], F]:
    """Decorator: replace `param` kwarg/arg with ensure()-validated model ID."""

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            model_id = model
            if model_id is None:
                if param in kwargs:
                    model_id = kwargs[param]
                else:
                    raise TypeError(f"require_alive: missing model argument {param!r}")

            safe = ensure(
                model_id,
                warn_deprecated=warn_deprecated,
                strict_unknown=strict_unknown,
                warn_days=warn_days,
                registry_path=registry_path,
            )
            kwargs = {**kwargs, param: safe}
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
