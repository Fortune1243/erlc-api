from __future__ import annotations

import pytest
import httpx

from erlc_api._errors import APIError, AuthError, NetworkError, RateLimitError
from erlc_api._http import AsyncHTTP, ClientConfig
from erlc_api._ratelimit import RateLimiter


class _FakeHTTPClient:
    def __init__(self, responses: list[httpx.Response | Exception]) -> None:
        self._responses = responses
        self.calls = 0

    async def request(self, *_args, **_kwargs) -> httpx.Response:
        self.calls += 1
        if not self._responses:
            raise AssertionError("No fake responses remaining")
        result = self._responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def test_http_default_user_agent_matches_package_version() -> None:
    assert ClientConfig().user_agent == "erlc-api-python/1.0.1"


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("failure", "expected_error"),
    [
        (httpx.ConnectError("boom"), NetworkError),
        (
            httpx.Response(
                500,
                headers={"content-type": "application/json"},
                json={"error": "server"},
            ),
            APIError,
        ),
    ],
)
async def test_http_does_not_retry_non_idempotent_failures(
    failure: httpx.Response | Exception,
    expected_error: type[Exception],
) -> None:
    fake_client = _FakeHTTPClient([failure])
    http = AsyncHTTP(ClientConfig(max_retries=4), RateLimiter())
    http._client = fake_client  # type: ignore[assignment]

    with pytest.raises(expected_error):
        await http.request(
            key_id="key1",
            method="POST",
            path="/v1/server/command",
            headers={"Server-Key": "abcd1234"},
            json={"command": ":help"},
            idempotent=False,
        )

    assert fake_client.calls == 1
