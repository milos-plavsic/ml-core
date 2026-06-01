"""Unit tests for ml_core.cache."""

import time
from pathlib import Path

from ml_core.cache import DiskCache, TTLCache, cache_with_ttl


class TestTTLCache:
    def test_set_and_get(self):
        c = TTLCache()
        c.set("k", "v")
        assert c.get("k") == "v"

    def test_miss_returns_none(self):
        c = TTLCache()
        assert c.get("missing") is None

    def test_expiry(self):
        c = TTLCache(default_ttl=0.01)
        c.set("k", 99)
        time.sleep(0.02)
        assert c.get("k") is None

    def test_max_size_evicts_oldest(self):
        c = TTLCache(max_size=3)
        c.set("a", 1)
        c.set("b", 2)
        c.set("c", 3)
        c.set("d", 4)  # evicts "a"
        assert c.get("a") is None
        assert c.get("d") == 4

    def test_clear(self):
        c = TTLCache()
        c.set("x", 1)
        c.clear()
        assert c.size() == 0

    def test_stores_arbitrary_objects(self):
        c = TTLCache()
        c.set("obj", {"nested": [1, 2, 3]})
        assert c.get("obj") == {"nested": [1, 2, 3]}


class TestDiskCache:
    def test_set_and_get(self, tmp_path: Path):
        c = DiskCache(tmp_path / "cache")
        c.set("k", {"data": [1, 2, 3]})
        assert c.get("k") == {"data": [1, 2, 3]}

    def test_miss_returns_none(self, tmp_path: Path):
        c = DiskCache(tmp_path / "cache")
        assert c.get("missing") is None

    def test_expiry(self, tmp_path: Path):
        c = DiskCache(tmp_path / "cache", default_ttl=0.01)
        c.set("k", "value")
        time.sleep(0.02)
        assert c.get("k") is None

    def test_stores_non_json_objects(self, tmp_path: Path):
        """DiskCache uses pickle, so arbitrary objects are safe."""
        import numpy as np

        arr = np.array([1.0, 2.0, 3.0])
        c = DiskCache(tmp_path / "cache")
        c.set("arr", arr)
        result = c.get("arr")
        assert list(result) == list(arr)

    def test_clear(self, tmp_path: Path):
        c = DiskCache(tmp_path / "cache")
        c.set("a", 1)
        c.set("b", 2)
        c.clear()
        assert c.get("a") is None


class TestCacheWithTTLDecorator:
    def test_caches_result(self):
        calls = []

        @cache_with_ttl(ttl_seconds=60)
        def expensive(x):
            calls.append(x)
            return x * 2

        assert expensive(5) == 10
        assert expensive(5) == 10
        assert len(calls) == 1

    def test_different_args_not_cached(self):
        calls = []

        @cache_with_ttl(ttl_seconds=60)
        def fn(x):
            calls.append(x)
            return x

        fn(1)
        fn(2)
        assert len(calls) == 2
