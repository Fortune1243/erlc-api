from __future__ import annotations

import pytest
import httpx

from erlc_api._errors import AuthError, RateLimitError
from erlc_api._http import AsyncHTTP, ClientConfig
from erlc_api._ratelimit import RateLimiter


class _FakeHTTPClient:
    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = responses

    async def request(self, *_args, **_kwargs) -> httpx.Response:
        if not self._responses:
            raise AssertionError("No fake responses remaining")
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_http_raises_auth_error_on_401() -> None:
    http = AsyncHTTP(ClientConfig(max_retries=1), RateLimiter())
    http._client = _FakeHTTPClient(  # type: ignore[assignment]
        [
            httpx.Response(
                401,
                headers={"content-type": "application/json"},
                json={"error": "unauthorized"},
            )
        ]
    )

    with pytest.raises(AuthError):
        await http.request(
            key_id="key1",
            method="GET",
            path="/v1/server",
            headers={"Server-Key": "abcd1234"},
        )


@pytest.mark.asyncio
async def test_http_raises_rate_limit_error_with_retry_after() -> None:
    http = AsyncHTTP(ClientConfig(max_retries=1), RateLimiter())
    http._client = _FakeHTTPClient(  # type: ignore[assignment]
        [
            httpx.Response(
                429,
                headers={
                    "content-type": "application/json",
                    "X-RateLimit-Bucket": "bucket-a",
                },
                json={"retry_after": 1.75},
            )
        ]
    )

    with pytest.raises(RateLimitError) as exc_info:
        await http.request(
            key_id="key1",
            method="GET",
            path="/v1/server",
            headers={"Server-Key": "abcd1234"},
        )
    assert exc_info.value.retry_after == 1.75
