"""Retry helpers for transient operational failures."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class RetryPolicy:
    attempts: int = 2
    base_delay_seconds: float = 0.05


def with_retry(action: Callable[[], T], on_retry: Callable[[int, Exception], None], policy: RetryPolicy | None = None) -> T:
    """Execute an action with bounded retries and simple linear backoff."""

    effective_policy = policy or RetryPolicy()
    last_error: Exception | None = None

    for attempt in range(1, effective_policy.attempts + 1):
        try:
            return action()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= effective_policy.attempts:
                break
            on_retry(attempt, exc)
            time.sleep(effective_policy.base_delay_seconds * attempt)

    assert last_error is not None
    raise last_error
