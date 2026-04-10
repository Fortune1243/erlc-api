from __future__ import annotations

import time

import pytest

from erlc_api._ratelimit import RateLimiter


@pytest.mark.asyncio
async def test_ratelimiter_reserves_remaining_tokens_before_reset() -> None:
    limiter = RateLimiter()
    reset_at = time.time() + 0.2

    await limiter.update_from_headers(
        key_id="key-a",
        bucket="bucket-a",
        limit=2,
        remaining=2,
        reset_epoch_s=reset_at,
    )

    assert await limiter.pre_acquire(key_id="key-a", bucket="bucket-a") is None
    assert await limiter.pre_acquire(key_id="key-a", bucket="bucket-a") is None

    start = time.perf_counter()
    await limiter.pre_acquire(key_id="key-a", bucket="bucket-a")
    elapsed = time.perf_counter() - start
    assert elapsed >= 0.15


@pytest.mark.asyncio
async def test_ratelimiter_circuit_breaker_opens_after_threshold() -> None:
    limiter = RateLimiter(circuit_breaker_enabled=True, circuit_failure_threshold=2, circuit_open_s=0.3)

    await limiter.mark_failure(key_id="key-a", bucket="bucket-a")
    await limiter.mark_failure(key_id="key-a", bucket="bucket-a")

    retry_after = await limiter.pre_acquire(key_id="key-a", bucket="bucket-a")
    assert retry_after is not None
    assert retry_after > 0

    await limiter.mark_success(key_id="key-a", bucket="bucket-a")
    reopened = await limiter.pre_acquire(key_id="key-a", bucket="bucket-a")
    assert reopened is None
