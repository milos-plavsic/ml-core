"""Token-bucket rate limiter — per-key, thread-safe."""

from __future__ import annotations

import threading
import time

from ml_core.exceptions import RateLimitExceeded


class _Bucket:
    __slots__ = ("tokens", "last_refill", "lock")

    def __init__(self, capacity: float) -> None:
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()


class RateLimiter:
    """Token-bucket limiter.  Each ``key`` gets its own bucket.

    Usage::

        limiter = RateLimiter(rate=10, burst=20)   # 10 req/s, burst up to 20
        limiter.acquire("user-123")                # raises RateLimitExceeded if dry
    """

    def __init__(self, rate: float = 10.0, burst: float | None = None) -> None:
        self._rate = rate
        self._burst = burst if burst is not None else rate
        self._buckets: dict[str, _Bucket] = {}
        self._lock = threading.Lock()

    def _get_bucket(self, key: str) -> _Bucket:
        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = _Bucket(self._burst)
            return self._buckets[key]

    def _refill(self, bucket: _Bucket) -> None:
        now = time.monotonic()
        elapsed = now - bucket.last_refill
        bucket.tokens = min(self._burst, bucket.tokens + elapsed * self._rate)
        bucket.last_refill = now

    def acquire(self, key: str = "default", cost: float = 1.0) -> None:
        """Consume tokens for a key, raising if the bucket is exhausted."""
        bucket = self._get_bucket(key)
        with bucket.lock:
            self._refill(bucket)
            if bucket.tokens < cost:
                raise RateLimitExceeded(
                    f"Rate limit exceeded for key={key!r}",
                    detail=f"Available tokens: {bucket.tokens:.2f}/{self._burst}",
                )
            bucket.tokens -= cost

    def available(self, key: str = "default") -> float:
        bucket = self._get_bucket(key)
        with bucket.lock:
            self._refill(bucket)
            return bucket.tokens
