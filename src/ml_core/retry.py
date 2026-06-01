"""Retry logic with exponential backoff and jitter — sync and async."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

from ml_core.exceptions import RetryExhausted

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    func: Callable[[], T],
    *,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """Retry a callable with exponential backoff + jitter."""
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        try:
            return func()
        except exceptions as exc:
            last_exc = exc
            if attempt == max_retries - 1:
                logger.error(
                    "All %d retries exhausted for %s: %s",
                    max_retries,
                    getattr(func, "__name__", func),
                    exc,
                )
                raise RetryExhausted(str(exc)) from exc

            delay = min(initial_delay * (backoff_factor**attempt), max_delay)
            if jitter:
                delay += random.uniform(0, delay * 0.1)
            logger.warning(
                "Attempt %d/%d failed for %s: %s — retrying in %.2fs",
                attempt + 1,
                max_retries,
                getattr(func, "__name__", func),
                exc,
                delay,
            )
            time.sleep(delay)

    raise RetryExhausted(str(last_exc)) from last_exc


async def async_retry(
    coro_func: Callable[..., Awaitable[T]],
    *args,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs,
) -> T:
    """Await a coroutine function with exponential backoff + jitter.

    Unlike the previous ``async_retry_with_backoff`` (which returned a wrapper
    function and had to be called separately), this function is itself a
    coroutine — just ``await`` it directly::

        result = await async_retry(fetch_data, url, max_retries=5)
    """
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        try:
            return await coro_func(*args, **kwargs)
        except exceptions as exc:
            last_exc = exc
            if attempt == max_retries - 1:
                logger.error("All %d retries exhausted: %s", max_retries, exc)
                raise RetryExhausted(str(exc)) from exc

            delay = min(initial_delay * (backoff_factor**attempt), max_delay)
            if jitter:
                delay += random.uniform(0, delay * 0.1)
            logger.warning(
                "Async attempt %d/%d failed: %s — retrying in %.2fs",
                attempt + 1,
                max_retries,
                exc,
                delay,
            )
            await asyncio.sleep(delay)

    raise RetryExhausted(str(last_exc)) from last_exc
