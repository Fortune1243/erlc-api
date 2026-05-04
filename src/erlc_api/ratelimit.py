from __future__ import annotations

import asyncio
from dataclasses import dataclass
import time
from typing import Any, Awaitable, Callable, Mapping

from ._errors import RateLimitError


def _now_default() -> float:
    return time.time()


def _route_key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


def _header(headers: Mapping[str, Any], name: str) -> str | None:
    wanted = name.lower()
    for key, value in headers.items():
        if str(key).lower() != wanted:
            continue
        if value is None:
            return None
        text = str(value).strip()
        return text or None
    return None


def _float_header(headers: Mapping[str, Any], name: str) -> float | None:
    value = _header(headers, name)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _int_header(headers: Mapping[str, Any], name: str) -> int | None:
    value = _header(headers, name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


@dataclass(frozen=True)
class RateLimitState:
    bucket: str
    limit: int | None = None
    remaining: int | None = None
    reset_epoch_s: float | None = None
    retry_after_s: float | None = None
    key_scope: str | None = None

    def wait_seconds(self, now: float | None = None) -> float:
        current = _now_default() if now is None else now
        waits: list[float] = []
        if self.retry_after_s is not None:
            waits.append(max(0.0, self.retry_after_s))
        if self.remaining is not None and self.remaining <= 0 and self.reset_epoch_s is not None:
            waits.append(max(0.0, self.reset_epoch_s - current))
        if self.retry_after_s is not None and self.reset_epoch_s is not None:
            waits.append(max(0.0, self.reset_epoch_s - current))
        return max(waits, default=0.0)

    def to_dict(self) -> dict[str, str | int | float | None]:
        return {
            "bucket": self.bucket,
            "limit": self.limit,
            "remaining": self.remaining,
            "reset_epoch_s": self.reset_epoch_s,
            "retry_after_s": self.retry_after_s,
            "key_scope": self.key_scope,
        }


@dataclass(frozen=True)
class RateLimitSnapshot:
    states: tuple[RateLimitState, ...]
    generated_at: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "states": [state.to_dict() for state in self.states],
        }


class _BaseLimiter:
    def __init__(self, *, now: Callable[[], float] | None = None) -> None:
        self._now = now or _now_default
        self._states: dict[tuple[str, str], RateLimitState] = {}
        self._route_buckets: dict[tuple[str, str], str] = {}

    def _state_key(self, key_scope: str, bucket: str) -> tuple[str, str]:
        return (key_scope, bucket)

    def _candidates(self, method: str, path: str, *, key_scope: str, bucket: str | None = None) -> list[RateLimitState]:
        route = _route_key(method, path)
        buckets: list[str] = []
        if bucket:
            buckets.append(bucket)
        observed = self._route_buckets.get((key_scope, route))
        if observed:
            buckets.append(observed)
        buckets.append(route)
        if (key_scope, "global") in self._states:
            buckets.append("global")

        out: list[RateLimitState] = []
        seen: set[str] = set()
        for item in buckets:
            if item in seen:
                continue
            seen.add(item)
            state = self._states.get(self._state_key(key_scope, item))
            if state is not None:
                out.append(state)
        return out

    def _wait_seconds(self, method: str, path: str, *, key_scope: str, bucket: str | None = None) -> float:
        now = self._now()
        return max((state.wait_seconds(now) for state in self._candidates(method, path, key_scope=key_scope, bucket=bucket)), default=0.0)

    def _store(self, method: str, path: str, *, key_scope: str, state: RateLimitState) -> RateLimitState:
        route = _route_key(method, path)
        self._states[self._state_key(key_scope, state.bucket)] = state
        self._route_buckets[(key_scope, route)] = state.bucket
        return state

    def _state_from_headers(self, method: str, path: str, headers: Mapping[str, Any], *, key_scope: str) -> RateLimitState | None:
        bucket = _header(headers, "X-RateLimit-Bucket")
        limit = _int_header(headers, "X-RateLimit-Limit")
        remaining = _int_header(headers, "X-RateLimit-Remaining")
        reset = _float_header(headers, "X-RateLimit-Reset")
        retry_after = _float_header(headers, "Retry-After")
        if bucket is None and limit is None and remaining is None and reset is None and retry_after is None:
            return None

        return RateLimitState(
            bucket=bucket or _route_key(method, path),
            limit=limit,
            remaining=remaining,
            reset_epoch_s=reset,
            retry_after_s=retry_after,
            key_scope=key_scope,
        )

    def after_response(self, method: str, path: str, headers: Mapping[str, Any], *, key_scope: str = "server") -> RateLimitState | None:
        state = self._state_from_headers(method, path, headers, key_scope=key_scope)
        if state is None:
            return None
        return self._store(method, path, key_scope=key_scope, state=state)

    def after_error(
        self,
        error: Any,
        *,
        method: str | None = None,
        path: str | None = None,
        key_scope: str = "server",
    ) -> RateLimitState | None:
        if not isinstance(error, RateLimitError):
            return None
        method = method or error.method or "GET"
        path = path or error.path or "/"
        retry_after = error.retry_after_s
        reset = error.reset_epoch_s
        if reset is None and retry_after is not None:
            reset = self._now() + retry_after
        if retry_after is None and reset is None:
            return None
        state = RateLimitState(
            bucket=error.bucket or _route_key(method, path),
            remaining=0,
            reset_epoch_s=reset,
            retry_after_s=retry_after,
            key_scope=key_scope,
        )
        return self._store(method, path, key_scope=key_scope, state=state)

    def snapshot(self) -> RateLimitSnapshot:
        states = tuple(sorted(self._states.values(), key=lambda state: ((state.key_scope or ""), state.bucket)))
        return RateLimitSnapshot(states=states, generated_at=self._now())

    def reset(self) -> None:
        self._states.clear()
        self._route_buckets.clear()


class AsyncRateLimiter(_BaseLimiter):
    def __init__(
        self,
        *,
        now: Callable[[], float] | None = None,
        sleep: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        super().__init__(now=now)
        self._sleep = sleep or asyncio.sleep

    async def before_request(self, method: str, path: str, *, key_scope: str = "server", bucket: str | None = None) -> float:
        wait_s = self._wait_seconds(method, path, key_scope=key_scope, bucket=bucket)
        if wait_s > 0:
            await self._sleep(wait_s)
        return wait_s


class RateLimiter(_BaseLimiter):
    def __init__(
        self,
        *,
        now: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        super().__init__(now=now)
        self._sleep = sleep or time.sleep

    def before_request(self, method: str, path: str, *, key_scope: str = "server", bucket: str | None = None) -> float:
        wait_s = self._wait_seconds(method, path, key_scope=key_scope, bucket=bucket)
        if wait_s > 0:
            self._sleep(wait_s)
        return wait_s


__all__ = [
    "AsyncRateLimiter",
    "RateLimitSnapshot",
    "RateLimitState",
    "RateLimiter",
]
