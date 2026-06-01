"""Circuit breaker — closed / open / half-open state machine."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import TypeVar

from ml_core.exceptions import CircuitOpenError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class State(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Protect a downstream call from cascading failures.

    Usage::

        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

        # sync
        result = cb.call(some_function, arg1, arg2)

        # async
        result = await cb.async_call(some_coroutine, arg1, arg2)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 2,
        name: str = "circuit",
    ) -> None:
        self.name = name
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._success_threshold = success_threshold

        self._state = State.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at: float | None = None

    # ------------------------------------------------------------------
    @property
    def state(self) -> State:
        if self._state is State.OPEN:
            if (
                self._opened_at
                and (time.monotonic() - self._opened_at) >= self._recovery_timeout
            ):
                logger.info("[%s] Circuit transitioning OPEN → HALF_OPEN", self.name)
                self._state = State.HALF_OPEN
                self._success_count = 0
        return self._state

    def _on_success(self) -> None:
        if self._state is State.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self._success_threshold:
                logger.info("[%s] Circuit closing (HALF_OPEN → CLOSED)", self.name)
                self._state = State.CLOSED
                self._failure_count = 0
        else:
            self._failure_count = 0

    def _on_failure(self, exc: Exception) -> None:
        self._failure_count += 1
        if (
            self._state is State.HALF_OPEN
            or self._failure_count >= self._failure_threshold
        ):
            logger.warning(
                "[%s] Circuit opening after %d failure(s): %s",
                self.name,
                self._failure_count,
                exc,
            )
            self._state = State.OPEN
            self._opened_at = time.monotonic()

    def _check_open(self) -> None:
        if self.state is State.OPEN:
            raise CircuitOpenError(
                f"Circuit '{self.name}' is OPEN — downstream unavailable",
                detail=f"Retry after {self._recovery_timeout}s",
            )

    # ------------------------------------------------------------------
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        self._check_open()
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure(exc)
            raise

    async def async_call(
        self, coro_func: Callable[..., Awaitable[T]], *args, **kwargs
    ) -> T:
        self._check_open()
        try:
            result = await coro_func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure(exc)
            raise
