"""Unit tests for ml_core.retry."""

import pytest

from ml_core.exceptions import RetryExhausted
from ml_core.retry import async_retry, retry_with_backoff


def test_retry_succeeds_first_attempt():
    calls = []

    def fn():
        calls.append(1)
        return 42

    assert retry_with_backoff(fn, max_retries=3, initial_delay=0) == 42
    assert len(calls) == 1


def test_retry_succeeds_after_failures():
    calls = []

    def fn():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("transient")
        return "ok"

    result = retry_with_backoff(fn, max_retries=5, initial_delay=0)
    assert result == "ok"
    assert len(calls) == 3


def test_retry_exhausted_raises():
    def fn():
        raise RuntimeError("always fails")

    with pytest.raises(RetryExhausted):
        retry_with_backoff(fn, max_retries=3, initial_delay=0)


def test_retry_respects_exception_filter():
    def fn():
        raise KeyError("not retried")

    with pytest.raises(KeyError):
        retry_with_backoff(fn, max_retries=3, initial_delay=0, exceptions=(ValueError,))


@pytest.mark.asyncio
async def test_async_retry_succeeds():
    calls = []

    async def coro():
        calls.append(1)
        return "done"

    result = await async_retry(coro, max_retries=3, initial_delay=0)
    assert result == "done"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_async_retry_after_failures():
    calls = []

    async def coro():
        calls.append(1)
        if len(calls) < 2:
            raise ConnectionError("retry me")
        return "ok"

    result = await async_retry(coro, max_retries=5, initial_delay=0)
    assert result == "ok"


@pytest.mark.asyncio
async def test_async_retry_exhausted():
    async def coro():
        raise TimeoutError("always")

    with pytest.raises(RetryExhausted):
        await async_retry(coro, max_retries=3, initial_delay=0)
