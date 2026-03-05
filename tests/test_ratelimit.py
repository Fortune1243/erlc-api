from __future__ import annotations

import time

import pytest

from erlc_api._ratelimit import RateLimiter


@pytest.mark.asyncio
async def test_ratelimiter_is_scoped_per_server_key() -> None:
    limiter = RateLimiter()
    reset_at = time.time() + 0.2

    await limiter.update_from_headers(
        key_id="key-a",
        bucket="same-bucket",
        limit=10,
        remaining=0,
        reset_epoch_s=reset_at,
    )

    start_other = time.perf_counter()
    await limiter.pre_acquire(key_id="key-b", bucket="same-bucket")
    other_elapsed = time.perf_counter() - start_other
    assert other_elapsed < 0.1

    start_blocked = time.perf_counter()
    await limiter.pre_acquire(key_id="key-a", bucket="same-bucket")
    blocked_elapsed = time.perf_counter() - start_blocked
    assert blocked_elapsed >= 0.15
