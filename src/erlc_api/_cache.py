from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
import math
import pickle
import time
from typing import Any, Protocol


@dataclass(frozen=True)
class CacheStats:
    hits: int = 0
    misses: int = 0
    sets: int = 0
    invalidations: int = 0

    @property
    def total_reads(self) -> int:
        return self.hits + self.misses

    @property
    def hit_ratio(self) -> float:
        if self.total_reads == 0:
            return 0.0
        return self.hits / self.total_reads


class CacheBackend(Protocol):
    async def get(self, key: str) -> Any | None: ...

    async def set(self, key: str, value: Any, ttl_s: float) -> None: ...

    async def invalidate_key(self, key: str) -> None: ...

    async def invalidate_prefix(self, prefix: str) -> None: ...

    async def clear(self) -> None: ...

    def stats(self) -> CacheStats: ...


@dataclass
class _Entry:
    value: Any
    expires_at: float


class InMemoryCacheBackend:
    def __init__(self) -> None:
        self._store: dict[str, _Entry] = {}
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._invalidations = 0

    @staticmethod
    def _is_expired(entry: _Entry, now: float) -> bool:
        return entry.expires_at <= now

    async def get(self, key: str) -> Any | None:
        now = time.time()
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            if self._is_expired(entry, now):
                self._store.pop(key, None)
                self._misses += 1
                return None
            self._hits += 1
            return entry.value

    async def set(self, key: str, value: Any, ttl_s: float) -> None:
        if ttl_s <= 0:
            return
        async with self._lock:
            self._store[key] = _Entry(value=value, expires_at=time.time() + ttl_s)
            self._sets += 1

    async def invalidate_key(self, key: str) -> None:
        async with self._lock:
            if key in self._store:
                self._store.pop(key, None)
                self._invalidations += 1

    async def invalidate_prefix(self, prefix: str) -> None:
        async with self._lock:
            keys = [key for key in self._store if key.startswith(prefix)]
            for key in keys:
                self._store.pop(key, None)
            if keys:
                self._invalidations += len(keys)

    async def clear(self) -> None:
        async with self._lock:
            removed = len(self._store)
            self._store.clear()
            if removed:
                self._invalidations += removed

    def stats(self) -> CacheStats:
        return CacheStats(
            hits=self._hits,
            misses=self._misses,
            sets=self._sets,
            invalidations=self._invalidations,
        )


class RedisCacheBackend:
    """
    Optional Redis cache backend for multi-instance deployments.

    Redis dependency is imported lazily. Install via:
    pip install erlc-api[redis]
    """

    def __init__(self, redis_url: str, *, key_prefix: str = "erlc-api:cache:") -> None:
        try:
            import redis.asyncio as redis  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - import path validation
            raise RuntimeError("Redis cache backend requires `redis` package. Install with erlc-api[redis].") from exc
        self._redis = redis.from_url(redis_url, decode_responses=False)
        self._key_prefix = key_prefix
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._invalidations = 0

    def _key(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    @staticmethod
    def _encode(value: Any) -> bytes:
        return base64.b85encode(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))

    @staticmethod
    def _decode(raw: bytes) -> Any:
        return pickle.loads(base64.b85decode(raw))

    async def get(self, key: str) -> Any | None:
        raw = await self._redis.get(self._key(key))
        if raw is None:
            self._misses += 1
            return None
        self._hits += 1
        return self._decode(raw)

    async def set(self, key: str, value: Any, ttl_s: float) -> None:
        if ttl_s <= 0:
            return
        await self._redis.set(self._key(key), self._encode(value), ex=max(1, math.ceil(ttl_s)))
        self._sets += 1

    async def invalidate_key(self, key: str) -> None:
        deleted = await self._redis.delete(self._key(key))
        if deleted:
            self._invalidations += int(deleted)

    async def invalidate_prefix(self, prefix: str) -> None:
        pattern = self._key(f"{prefix}*")
        deleted = 0
        async for key in self._redis.scan_iter(match=pattern):
            deleted += int(await self._redis.delete(key))
        if deleted:
            self._invalidations += deleted

    async def clear(self) -> None:
        await self.invalidate_prefix("")

    def stats(self) -> CacheStats:
        return CacheStats(
            hits=self._hits,
            misses=self._misses,
            sets=self._sets,
            invalidations=self._invalidations,
        )


__all__ = [
    "CacheBackend",
    "CacheStats",
    "InMemoryCacheBackend",
    "RedisCacheBackend",
]
