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


class RateLimiter:
    """
    Cooperative bucket limiter keyed by (server key id, bucket).

    Notes:
    - A per-bucket lock serializes updates and pre-acquire checks for the same key/bucket.
    - Sleep is always done outside locks to avoid lock contention and deadlocks.
    - In-flight requests may still race, but header updates converge deterministically.
    """

    def __init__(self) -> None:
        self._locks_guard = asyncio.Lock()
        self._bucket_locks: Dict[BucketKey, asyncio.Lock] = {}
        self._state: Dict[BucketKey, BucketState] = {}

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

    async def pre_acquire(self, *, key_id: str, bucket: str) -> None:
        bk = (key_id, bucket)
        lock = await self._bucket_lock(bk)
        while True:
            sleep_s = 0.0
            async with lock:
                st = self._state.get(bk)
                if st and st.remaining == 0 and st.reset_epoch_s is not None:
                    sleep_s = max(0.0, st.reset_epoch_s - time.time())
                if sleep_s <= 0.0:
                    return
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
            self._state[bk] = st
