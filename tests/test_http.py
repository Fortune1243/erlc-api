from __future__ import annotations

import importlib.metadata as importlib_metadata
from datetime import datetime, timezone
from email.utils import format_datetime

import pytest
import httpx

from erlc_api._errors import APIError, AuthError, NetworkError, RateLimitError
from erlc_api._http import AsyncHTTP, ClientConfig, _default_user_agent, _parse_retry_after
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


def test_http_default_user_agent_uses_package_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("erlc_api._http.importlib_metadata.version", lambda _name: "9.9.9")

    assert ClientConfig().user_agent == "erlc-api-python/9.9.9"


def test_http_default_user_agent_falls_back_when_metadata_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_not_found(_name: str) -> str:
        raise importlib_metadata.PackageNotFoundError

    monkeypatch.setattr("erlc_api._http.importlib_metadata.version", raise_not_found)

    assert _default_user_agent() == "erlc-api-python/0+unknown"


def test_parse_retry_after_accepts_numeric_header() -> None:
    resp = httpx.Response(429, headers={"Retry-After": "1.75"})

    assert _parse_retry_after(resp, {}) == 1.75


def test_parse_retry_after_accepts_http_date_header(monkeypatch: pytest.MonkeyPatch) -> None:
    now = 1_700_000_000.0
    retry_at = datetime.fromtimestamp(now + 30.0, tz=timezone.utc)
    resp = httpx.Response(429, headers={"Retry-After": format_datetime(retry_at)})

    monkeypatch.setattr("erlc_api._http.time.time", lambda: now)

    assert _parse_retry_after(resp, {}) == 30.0


def test_parse_retry_after_returns_none_for_malformed_header() -> None:
    resp = httpx.Response(429, headers={"Retry-After": "tomorrow-ish"})

    assert _parse_retry_after(resp, {}) is None


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
    http = AsyncHTTP(ClientConfig(max_retries=0), RateLimiter())
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


@pytest.mark.asyncio
async def test_http_max_retries_zero_still_makes_one_attempt() -> None:
    fake_client = _FakeHTTPClient(
        [
            httpx.Response(
                500,
                headers={"content-type": "application/json"},
                json={"error": "server"},
            )
        ]
    )
    http = AsyncHTTP(ClientConfig(max_retries=0), RateLimiter())
    http._client = fake_client  # type: ignore[assignment]

    with pytest.raises(APIError):
        await http.request(
            key_id="key1",
            method="GET",
            path="/v1/server",
            headers={"Server-Key": "abcd1234"},
        )

    assert fake_client.calls == 1
