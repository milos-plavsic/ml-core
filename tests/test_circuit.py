"""Unit tests for ml_core.circuit."""

import pytest

from ml_core.circuit import CircuitBreaker, State
from ml_core.exceptions import CircuitOpenError


def test_starts_closed():
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.state is State.CLOSED


def test_opens_after_threshold():
    cb = CircuitBreaker(failure_threshold=3)
    for _ in range(3):
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("boom")))
    assert cb.state is State.OPEN


def test_open_raises_circuit_error():
    cb = CircuitBreaker(failure_threshold=1)
    with pytest.raises(ValueError):
        cb.call(lambda: (_ for _ in ()).throw(ValueError("x")))
    with pytest.raises(CircuitOpenError):
        cb.call(lambda: None)


def test_success_resets_failure_count():
    cb = CircuitBreaker(failure_threshold=3)
    with pytest.raises(ValueError):
        cb.call(lambda: (_ for _ in ()).throw(ValueError("x")))
    cb.call(lambda: "ok")
    assert cb.state is State.CLOSED
    assert cb._failure_count == 0


def test_transitions_to_half_open_after_timeout(monkeypatch):
    import time

    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
    with pytest.raises(ValueError):
        cb.call(lambda: (_ for _ in ()).throw(ValueError("x")))
    assert cb.state is State.OPEN
    time.sleep(0.02)
    assert cb.state is State.HALF_OPEN


@pytest.mark.asyncio
async def test_async_call_success():
    cb = CircuitBreaker()

    async def coro():
        return 42

    result = await cb.async_call(coro)
    assert result == 42


@pytest.mark.asyncio
async def test_async_call_opens_on_failure():
    cb = CircuitBreaker(failure_threshold=1)

    async def coro():
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError):
        await cb.async_call(coro)
    assert cb.state is State.OPEN
