from __future__ import annotations

from dataclasses import dataclass, field
import inspect
import time
from typing import Any, Callable, Protocol, runtime_checkable


READ_METHODS = frozenset(
    {
        "server",
        "players",
        "staff",
        "queue",
        "join_logs",
        "kill_logs",
        "command_logs",
        "mod_calls",
        "bans",
        "vehicles",
        "emergency_calls",
        "health_check",
        "validate_key",
    }
)


@dataclass(frozen=True)
class CacheEntry:
    key: str
    value: Any
    expires_at: float | None = None
    created_at: float = field(default_factory=time.time)

    def expired(self, now: float | None = None) -> bool:
        return self.expires_at is not None and (time.time() if now is None else now) >= self.expires_at


@dataclass(frozen=True)
class CacheStats:
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    size: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "size": self.size,
        }


@runtime_checkable
class CacheAdapter(Protocol):
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any, *, ttl_s: float | None = None) -> None: ...
    def delete(self, key: str) -> bool: ...
    def clear(self) -> None: ...


@runtime_checkable
class AsyncCacheAdapter(Protocol):
    async def get(self, key: str, default: Any = None) -> Any: ...
    async def set(self, key: str, value: Any, *, ttl_s: float | None = None) -> None: ...
    async def delete(self, key: str) -> bool: ...
    async def clear(self) -> None: ...


class MemoryCache:
    def __init__(self, *, now: Callable[[], float] | None = None) -> None:
        self._entries: dict[str, CacheEntry] = {}
        self._now = now or time.time
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0
        self._evictions = 0

    def _expires_at(self, ttl_s: float | None) -> float | None:
        if ttl_s is None:
            return None
        if ttl_s <= 0:
            raise ValueError("ttl_s must be greater than zero.")
        return self._now() + ttl_s

    def get(self, key: str, default: Any = None) -> Any:
        entry = self._entries.get(key)
        if entry is None:
            self._misses += 1
            return default
        if entry.expired(self._now()):
            self._entries.pop(key, None)
            self._misses += 1
            self._evictions += 1
            return default
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, *, ttl_s: float | None = None) -> None:
        self._entries[key] = CacheEntry(key=key, value=value, expires_at=self._expires_at(ttl_s), created_at=self._now())
        self._sets += 1

    def delete(self, key: str) -> bool:
        existed = key in self._entries
        if existed:
            self._entries.pop(key, None)
            self._deletes += 1
        return existed

    def invalidate(self, prefix: str | None = None) -> int:
        keys = [key for key in self._entries if prefix is None or key.startswith(prefix)]
        for key in keys:
            self.delete(key)
        return len(keys)

    def clear(self) -> None:
        self.invalidate()

    def prune(self) -> int:
        before = len(self._entries)
        for key, entry in list(self._entries.items()):
            if entry.expired(self._now()):
                self._entries.pop(key, None)
                self._evictions += 1
        return before - len(self._entries)

    def cached(self, key: str, factory: Callable[[], Any], *, ttl_s: float | None = None) -> Any:
        sentinel = object()
        cached = self.get(key, sentinel)
        if cached is not sentinel:
            return cached
        value = factory()
        self.set(key, value, ttl_s=ttl_s)
        return value

    def stats(self) -> CacheStats:
        self.prune()
        return CacheStats(
            hits=self._hits,
            misses=self._misses,
            sets=self._sets,
            deletes=self._deletes,
            evictions=self._evictions,
            size=len(self._entries),
        )


class AsyncMemoryCache:
    def __init__(self, *, now: Callable[[], float] | None = None) -> None:
        self._cache = MemoryCache(now=now)

    async def get(self, key: str, default: Any = None) -> Any:
        return self._cache.get(key, default)

    async def set(self, key: str, value: Any, *, ttl_s: float | None = None) -> None:
        self._cache.set(key, value, ttl_s=ttl_s)

    async def delete(self, key: str) -> bool:
        return self._cache.delete(key)

    async def clear(self) -> None:
        self._cache.clear()

    async def invalidate(self, prefix: str | None = None) -> int:
        return self._cache.invalidate(prefix)

    async def prune(self) -> int:
        return self._cache.prune()

    async def cached(self, key: str, factory: Callable[[], Any], *, ttl_s: float | None = None) -> Any:
        sentinel = object()
        cached = await self.get(key, sentinel)
        if cached is not sentinel:
            return cached
        value = factory()
        if inspect.isawaitable(value):
            value = await value
        await self.set(key, value, ttl_s=ttl_s)
        return value

    def stats(self) -> CacheStats:
        return self._cache.stats()


def cache_key(method_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    kwargs_text = ",".join(f"{key}={kwargs[key]!r}" for key in sorted(kwargs))
    args_text = ",".join(repr(arg) for arg in args)
    return f"{method_name}({args_text};{kwargs_text})"


class CachedClient:
    def __init__(
        self,
        api: Any,
        *,
        cache: CacheAdapter | None = None,
        ttl_s: float = 5.0,
        methods: set[str] | None = None,
    ) -> None:
        self.api = api
        self.cache = cache or MemoryCache()
        self.ttl_s = ttl_s
        self.methods = methods or set(READ_METHODS)

    def invalidate(self, prefix: str | None = None) -> int:
        invalidate = getattr(self.cache, "invalidate", None)
        if callable(invalidate):
            return int(invalidate(prefix))
        self.cache.clear()
        return 0

    def __getattr__(self, name: str) -> Any:
        target = getattr(self.api, name)
        if name not in self.methods or not callable(target):
            return target

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            key = cache_key(name, args, kwargs)
            sentinel = object()
            cached = self.cache.get(key, sentinel)
            if cached is not sentinel:
                return cached
            value = target(*args, **kwargs)
            self.cache.set(key, value, ttl_s=self.ttl_s)
            return value

        return wrapped


class AsyncCachedClient:
    def __init__(
        self,
        api: Any,
        *,
        cache: AsyncCacheAdapter | None = None,
        ttl_s: float = 5.0,
        methods: set[str] | None = None,
    ) -> None:
        self.api = api
        self.cache = cache or AsyncMemoryCache()
        self.ttl_s = ttl_s
        self.methods = methods or set(READ_METHODS)

    async def invalidate(self, prefix: str | None = None) -> int:
        invalidate = getattr(self.cache, "invalidate", None)
        if callable(invalidate):
            return int(await invalidate(prefix))
        await self.cache.clear()
        return 0

    def __getattr__(self, name: str) -> Any:
        target = getattr(self.api, name)
        if name not in self.methods or not callable(target):
            return target

        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            key = cache_key(name, args, kwargs)
            sentinel = object()
            cached = await self.cache.get(key, sentinel)
            if cached is not sentinel:
                return cached
            value = target(*args, **kwargs)
            if inspect.isawaitable(value):
                value = await value
            await self.cache.set(key, value, ttl_s=self.ttl_s)
            return value

        return wrapped


__all__ = [
    "AsyncCacheAdapter",
    "AsyncCachedClient",
    "AsyncMemoryCache",
    "CacheAdapter",
    "CacheEntry",
    "CacheStats",
    "CachedClient",
    "MemoryCache",
    "READ_METHODS",
    "cache_key",
]
