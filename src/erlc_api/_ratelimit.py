# src/erlc_api/_ratelimit.py
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

BucketKey = Tuple[str, str]  # (key_id, bucket)


@dataclass
class BucketState:
    remaining: Optional[int] = None
    reset_epoch_s: Optional[float] = None
    limit: Optional[int] = None
    updated_at_epoch_s: float = 0.0


@dataclass
class CircuitState:
    failure_count: int = 0
    open_until_epoch_s: float | None = None
    half_open_probe_in_flight: bool = False


class RateLimiter:
    """
    Cooperative bucket limiter keyed by (server key id, bucket).

    Notes:
    - A per-bucket lock serializes updates and pre-acquire checks for the same key/bucket.
    - Sleep is always done outside locks to avoid lock contention and deadlocks.
    - In-flight requests may still race, but header updates converge deterministically.
    """

    def __init__(
        self,
        *,
        circuit_breaker_enabled: bool = True,
        circuit_failure_threshold: int = 5,
        circuit_open_s: float = 15.0,
    ) -> None:
        self._locks_guard = asyncio.Lock()
        self._bucket_locks: Dict[BucketKey, asyncio.Lock] = {}
        self._state: Dict[BucketKey, BucketState] = {}
        self._circuit_state: Dict[BucketKey, CircuitState] = {}
        self._circuit_breaker_enabled = circuit_breaker_enabled
        self._circuit_failure_threshold = max(1, int(circuit_failure_threshold))
        self._circuit_open_s = max(0.1, float(circuit_open_s))

    async def _bucket_lock(self, bucket_key: BucketKey) -> asyncio.Lock:
        lock = self._bucket_locks.get(bucket_key)
        if lock is not None:
            return lock
        async with self._locks_guard:
            existing = self._bucket_locks.get(bucket_key)
            if existing is not None:
                return existing
            created = asyncio.Lock()
            self._bucket_locks[bucket_key] = created
            return created

    @staticmethod
    def _refresh_window(st: BucketState, *, now: float) -> BucketState:
        if st.reset_epoch_s is not None and now >= st.reset_epoch_s and st.limit is not None:
            st.remaining = st.limit
            st.reset_epoch_s = None
        return st

    async def pre_acquire(self, *, key_id: str, bucket: str) -> float | None:
        bk = (key_id, bucket)
        lock = await self._bucket_lock(bk)
        while True:
            sleep_s = 0.0
            async with lock:
                now = time.time()
                if self._circuit_breaker_enabled:
                    circuit = self._circuit_state.get(bk, CircuitState())
                    if circuit.open_until_epoch_s is not None and now < circuit.open_until_epoch_s:
                        return max(0.0, circuit.open_until_epoch_s - now)
                    if circuit.open_until_epoch_s is not None and now >= circuit.open_until_epoch_s:
                        if circuit.half_open_probe_in_flight:
                            return 0.5
                        circuit.half_open_probe_in_flight = True
                        self._circuit_state[bk] = circuit

                st = self._state.get(bk)
                if st is None or st.remaining is None:
                    return None

                st = self._refresh_window(st, now=now)
                if st.remaining > 0:
                    st.remaining -= 1
                    st.updated_at_epoch_s = now
                    self._state[bk] = st
                    return None

                if st.reset_epoch_s is not None:
                    sleep_s = max(0.0, st.reset_epoch_s - now)
                else:
                    sleep_s = 0.05
                if sleep_s <= 0.0:
                    continue
            await asyncio.sleep(sleep_s)

    async def update_from_headers(
        self,
        *,
        key_id: str,
        bucket: Optional[str],
        limit: Optional[int],
        remaining: Optional[int],
        reset_epoch_s: Optional[float],
    ) -> None:
        if not bucket:
            return
        bk = (key_id, bucket)
        lock = await self._bucket_lock(bk)
        async with lock:
            st = self._state.get(bk, BucketState())
            if limit is not None:
                st.limit = limit
            if remaining is not None:
                st.remaining = remaining
            if reset_epoch_s is not None:
                st.reset_epoch_s = reset_epoch_s
            st.updated_at_epoch_s = time.time()
            self._state[bk] = st

    async def mark_failure(self, *, key_id: str, bucket: Optional[str]) -> None:
        if not self._circuit_breaker_enabled or not bucket:
            return
        bk = (key_id, bucket)
        lock = await self._bucket_lock(bk)
        async with lock:
            now = time.time()
            state = self._circuit_state.get(bk, CircuitState())
            if state.open_until_epoch_s is not None and now < state.open_until_epoch_s:
                return
            state.failure_count += 1
            state.half_open_probe_in_flight = False
            if state.failure_count >= self._circuit_failure_threshold:
                state.open_until_epoch_s = now + self._circuit_open_s
                state.failure_count = 0
            self._circuit_state[bk] = state

    async def mark_success(self, *, key_id: str, bucket: Optional[str]) -> None:
        if not self._circuit_breaker_enabled or not bucket:
            return
        bk = (key_id, bucket)
        lock = await self._bucket_lock(bk)
        async with lock:
            state = self._circuit_state.get(bk, CircuitState())
            state.failure_count = 0
            state.open_until_epoch_s = None
            state.half_open_probe_in_flight = False
            self._circuit_state[bk] = state
