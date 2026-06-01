"""Unit tests for ml_core.ratelimit."""

import pytest

from ml_core.exceptions import RateLimitExceeded
from ml_core.ratelimit import RateLimiter


def test_acquire_within_limit():
    lim = RateLimiter(rate=10, burst=10)
    for _ in range(10):
        lim.acquire("user")


def test_acquire_exceeds_burst():
    lim = RateLimiter(rate=1, burst=3)
    lim.acquire("u")
    lim.acquire("u")
    lim.acquire("u")
    with pytest.raises(RateLimitExceeded):
        lim.acquire("u")


def test_different_keys_independent():
    lim = RateLimiter(rate=1, burst=1)
    lim.acquire("a")
    lim.acquire("b")  # separate bucket — should not raise
    with pytest.raises(RateLimitExceeded):
        lim.acquire("a")


def test_tokens_refill_over_time():
    import time

    lim = RateLimiter(rate=100, burst=1)
    lim.acquire("k")
    with pytest.raises(RateLimitExceeded):
        lim.acquire("k")
    time.sleep(0.02)  # 100 tokens/s * 0.02s = 2 tokens refilled
    lim.acquire("k")  # should succeed now


def test_available_reports_remaining():
    lim = RateLimiter(rate=10, burst=10)
    lim.acquire("k", cost=3)
    assert abs(lim.available("k") - 7.0) < 0.5
