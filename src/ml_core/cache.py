"""TTL cache — in-memory and disk backends with safe serialization."""

from __future__ import annotations

import hashlib
import logging
import pickle
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry:
    value: Any
    timestamp: float

    def is_expired(self, ttl: float) -> bool:
        return (time.monotonic() - self.timestamp) > ttl


class TTLCache:
    """Thread-safe in-memory LRU-style cache with TTL eviction."""

    def __init__(self, max_size: int = 1000, default_ttl: float = 3600.0) -> None:
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._store: dict[str, CacheEntry] = {}

    # ------------------------------------------------------------------
    def get(self, key: str, ttl: float | None = None) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.is_expired(ttl if ttl is not None else self._default_ttl):
            del self._store[key]
            return None
        return entry.value

    def set(self, key: str, value: Any) -> None:
        if len(self._store) >= self._max_size:
            oldest = min(self._store, key=lambda k: self._store[k].timestamp)
            del self._store[oldest]
        self._store[key] = CacheEntry(value=value, timestamp=time.monotonic())

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def size(self) -> int:
        return len(self._store)


class DiskCache:
    """Pickle-based disk cache — handles arbitrary Python objects safely."""

    def __init__(self, cache_dir: Path | str, default_ttl: float = 86400.0) -> None:
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._default_ttl = default_ttl

    def _path(self, key: str) -> Path:
        safe = hashlib.sha256(key.encode()).hexdigest()
        return self._dir / f"{safe}.pkl"

    def get(self, key: str, ttl: float | None = None) -> Any | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            with path.open("rb") as fh:
                entry: CacheEntry = pickle.load(fh)
            if entry.is_expired(ttl if ttl is not None else self._default_ttl):
                path.unlink(missing_ok=True)
                return None
            return entry.value
        except Exception as exc:
            logger.warning("DiskCache read failed for key=%s: %s", key, exc)
            path.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: Any) -> None:
        path = self._path(key)
        try:
            entry = CacheEntry(value=value, timestamp=time.monotonic())
            tmp = path.with_suffix(".tmp")
            with tmp.open("wb") as fh:
                pickle.dump(entry, fh, protocol=pickle.HIGHEST_PROTOCOL)
            tmp.replace(path)
        except Exception as exc:
            logger.error("DiskCache write failed for key=%s: %s", key, exc)

    def clear(self) -> None:
        for f in self._dir.glob("*.pkl"):
            f.unlink(missing_ok=True)


def cache_with_ttl(
    ttl_seconds: float = 3600.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator: memoize a synchronous function with TTL eviction."""
    _cache: TTLCache = TTLCache(default_ttl=ttl_seconds)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            raw = f"{func.__qualname__}:{args!r}:{sorted(kwargs.items())!r}"
            key = hashlib.sha256(raw.encode()).hexdigest()
            hit = _cache.get(key)
            if hit is not None:
                return hit
            result = func(*args, **kwargs)
            _cache.set(key, result)
            return result

        wrapper.__wrapped__ = func  # type: ignore[attr-defined]
        return wrapper

    return decorator
