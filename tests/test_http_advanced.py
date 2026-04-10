from __future__ import annotations

import asyncio

import httpx
import pytest

from erlc_api._errors import PermissionDeniedError, RateLimitError
from erlc_api._http import AsyncHTTP, ClientConfig
from erlc_api._ratelimit import RateLimiter


class _SlowHTTPClient:
    def __init__(self, responses: list[httpx.Response], *, sleep_s: float = 0.02) -> None:
        self._responses = responses
        self.calls = 0
        self._sleep_s = sleep_s

    async def request(self, **_kwargs) -> httpx.Response:
        self.calls += 1
        await asyncio.sleep(self._sleep_s)
        if not self._responses:
            raise AssertionError("No fake responses remaining")
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_http_coalesces_identical_get_requests() -> None:
    fake = _SlowHTTPClient(
        [
            httpx.Response(200, headers={"content-type": "application/json"}, json={"value": 1}),
        ]
    )
    http = AsyncHTTP(ClientConfig(max_retries=0, cache_enabled=False, request_coalescing=True), RateLimiter())
    http._client = fake  # type: ignore[assignment]

    async def _call() -> dict[str, int]:
        return await http.request(
            key_id="k1",
            method="GET",
            path="/v1/server",
            headers={"Server-Key": "abc"},
        )

    first, second = await asyncio.gather(_call(), _call())

    assert first == {"value": 1}
    assert second == {"value": 1}
    assert fake.calls == 1


@pytest.mark.asyncio
async def test_http_cache_hit_and_manual_invalidate() -> None:
    fake = _SlowHTTPClient(
        [
            httpx.Response(200, headers={"content-type": "application/json"}, json={"name": "A"}),
            httpx.Response(200, headers={"content-type": "application/json"}, json={"name": "B"}),
        ],
        sleep_s=0.0,
    )
    cfg = ClientConfig(max_retries=0, cache_enabled=True, request_coalescing=False)
    cfg.cache_ttl_by_path["/v1/server"] = 60.0
    http = AsyncHTTP(cfg, RateLimiter())
    http._client = fake  # type: ignore[assignment]

    first = await http.request(key_id="k1", method="GET", path="/v1/server", headers={"Server-Key": "abc"})
    second = await http.request(key_id="k1", method="GET", path="/v1/server", headers={"Server-Key": "abc"})

    assert first == {"name": "A"}
    assert second == {"name": "A"}
    assert fake.calls == 1

    await http.invalidate_cache(key_id="k1", endpoint="/v1/server")
    third = await http.request(key_id="k1", method="GET", path="/v1/server", headers={"Server-Key": "abc"})
    assert third == {"name": "B"}
    assert fake.calls == 2


@pytest.mark.asyncio
async def test_http_retry_429_can_be_disabled() -> None:
    fake = _SlowHTTPClient(
        [
            httpx.Response(429, headers={"content-type": "application/json"}, json={"retry_after": 0.0}),
            httpx.Response(200, headers={"content-type": "application/json"}, json={"ok": True}),
        ],
        sleep_s=0.0,
    )
    cfg = ClientConfig(max_retries=3, retry_429=False)
    http = AsyncHTTP(cfg, RateLimiter())
    http._client = fake  # type: ignore[assignment]

    with pytest.raises(RateLimitError):
        await http.request(
            key_id="k1",
            method="GET",
            path="/v1/server",
            headers={"Server-Key": "abc"},
        )
    assert fake.calls == 1


@pytest.mark.asyncio
async def test_http_maps_permission_denied_error() -> None:
    fake = _SlowHTTPClient(
        [
            httpx.Response(
                403,
                headers={"content-type": "application/json"},
                json={"error": "permission denied"},
            )
        ],
        sleep_s=0.0,
    )
    cfg = ClientConfig(max_retries=0)
    http = AsyncHTTP(cfg, RateLimiter())
    http._client = fake  # type: ignore[assignment]

    with pytest.raises(PermissionDeniedError):
        await http.request(
            key_id="k1",
            method="GET",
            path="/v1/server",
            headers={"Server-Key": "abc"},
        )
