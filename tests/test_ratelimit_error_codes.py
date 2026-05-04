from __future__ import annotations

import httpx
import pytest

from erlc_api import AsyncERLC, ERLC, PermissionDeniedError, RateLimitError, RobloxCommunicationError
from erlc_api._http import AsyncTransport, ClientSettings, SyncTransport
from erlc_api.error_codes import exception_for_error_code, explain_error_code, list_error_codes
from erlc_api.ratelimit import AsyncRateLimiter, RateLimiter


class _AsyncFake:
    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = responses
        self.calls = 0

    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        self.calls += 1
        if not self.responses:
            raise AssertionError("no response queued")
        return self.responses.pop(0)

    async def aclose(self) -> None:
        return None


class _SyncFake:
    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = responses
        self.calls = 0

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        self.calls += 1
        if not self.responses:
            raise AssertionError("no response queued")
        return self.responses.pop(0)

    def close(self) -> None:
        return None


def _json_response(payload: object, status: int = 200, headers: dict[str, str] | None = None) -> httpx.Response:
    merged = {"content-type": "application/json"}
    if headers:
        merged.update(headers)
    return httpx.Response(status, headers=merged, json=payload)


@pytest.mark.asyncio
async def test_async_client_rate_limiter_updates_and_waits_from_headers() -> None:
    now = 100.0
    sleeps: list[float] = []

    def clock() -> float:
        return now

    async def sleep(delay: float) -> None:
        nonlocal now
        sleeps.append(delay)
        now += delay

    limiter = AsyncRateLimiter(now=clock, sleep=sleep)
    fake = _AsyncFake(
        [
            _json_response({"Players": []}, headers={"X-RateLimit-Bucket": "global", "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "105"}),
            _json_response({"Players": []}, headers={"X-RateLimit-Bucket": "global", "X-RateLimit-Remaining": "1", "X-RateLimit-Reset": "110"}),
        ]
    )
    transport = AsyncTransport(ClientSettings(retry_429=False), rate_limiter=limiter)
    transport._client = fake  # type: ignore[assignment]
    api = AsyncERLC("key", rate_limited=True, transport=transport)

    await api.players()
    await api.players()

    assert sleeps == [5.0]
    assert api.rate_limits is not None
    assert api.rate_limits.states[0].bucket == "global"
    assert api.rate_limits.states[0].key_scope == "server"


@pytest.mark.asyncio
async def test_rate_limiter_429_updates_state_and_raises_when_retry_disabled() -> None:
    now = 100.0

    def clock() -> float:
        return now

    limiter = AsyncRateLimiter(now=clock)
    fake = _AsyncFake(
        [
            _json_response(
                {"message": "Slow down", "error_code": 4001},
                status=429,
                headers={"Retry-After": "3", "X-RateLimit-Bucket": "command-key"},
            )
        ]
    )
    transport = AsyncTransport(ClientSettings(retry_429=False), rate_limiter=limiter)
    transport._client = fake  # type: ignore[assignment]
    api = AsyncERLC("key", rate_limited=True, transport=transport)

    with pytest.raises(RateLimitError):
        await api.players()

    snapshot = api.rate_limits
    assert snapshot is not None
    assert snapshot.states[0].bucket == "command-key"
    assert snapshot.states[0].retry_after_s == 3.0
    assert snapshot.states[0].reset_epoch_s == 103.0


def test_sync_rate_limiter_scopes_global_and_server_keys_separately() -> None:
    now = 50.0
    sleeps: list[float] = []

    def clock() -> float:
        return now

    def sleep(delay: float) -> None:
        nonlocal now
        sleeps.append(delay)
        now += delay

    limiter = RateLimiter(now=clock, sleep=sleep)
    limiter.after_response("GET", "/v2/server", {"X-RateLimit-Bucket": "global", "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "55"}, key_scope="global")
    limiter.after_response("GET", "/v2/server", {"X-RateLimit-Bucket": "server", "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "60"}, key_scope="server")

    assert limiter.before_request("GET", "/v2/server", key_scope="global") == 5.0
    assert limiter.before_request("GET", "/v2/server", key_scope="server") == 5.0
    assert sleeps == [5.0, 5.0]
    assert {state.key_scope for state in limiter.snapshot().states} == {"global", "server"}


def test_rate_limited_false_preserves_no_limiter_behavior() -> None:
    fake = _SyncFake([_json_response({"Players": []}, headers={"X-RateLimit-Bucket": "global", "X-RateLimit-Remaining": "0"})])
    transport = SyncTransport(ClientSettings(retry_429=False))
    transport._client = fake  # type: ignore[assignment]
    api = ERLC("key", rate_limited=False, transport=transport)

    assert api.rate_limits is None
    assert api.players() == []
    assert api.rate_limits is None


def test_rate_limiter_is_default_on() -> None:
    transport = SyncTransport(ClientSettings(retry_429=False))
    api = ERLC("key", transport=transport)

    assert api.rate_limited is True
    assert api.rate_limits is not None


def test_rate_limiter_missing_headers_do_not_block() -> None:
    sleeps: list[float] = []
    limiter = RateLimiter(now=lambda: 1.0, sleep=sleeps.append)

    assert limiter.after_response("GET", "/v2/server", {}, key_scope="server") is None
    assert limiter.before_request("GET", "/v2/server", key_scope="server") == 0.0
    assert limiter.snapshot().states == ()


def test_rate_limiter_retry_after_wait_expires() -> None:
    now = 100.0
    sleeps: list[float] = []

    def clock() -> float:
        return now

    limiter = RateLimiter(now=clock, sleep=sleeps.append)
    err = RateLimitError("Slow down", method="GET", path="/v2/server", retry_after=3, bucket="server")
    limiter.after_error(err, method="GET", path="/v2/server")

    assert limiter.before_request("GET", "/v2/server") == 3.0
    now = 104.0
    assert limiter.before_request("GET", "/v2/server") == 0.0

    limiter.reset()
    now = 200.0
    limiter.after_response("GET", "/v2/server", {"Retry-After": "3", "X-RateLimit-Bucket": "server"})

    assert limiter.before_request("GET", "/v2/server") == 3.0
    now = 204.0
    assert limiter.before_request("GET", "/v2/server") == 0.0
    assert sleeps == [3.0, 3.0]


def test_error_code_helpers_explain_and_map_known_codes() -> None:
    info = explain_error_code(4001)
    assert info is not None
    assert info.retryable is True
    assert info.exception is RateLimitError
    assert explain_error_code({"error_code": "9998"}).exception is PermissionDeniedError  # type: ignore[union-attr]
    assert exception_for_error_code(1001) is RobloxCommunicationError
    assert exception_for_error_code(None, status=429) is RateLimitError
    assert exception_for_error_code(None, status=400).__name__ == "BadRequestError"
    assert explain_error_code(123456) is None
    assert {item.code for item in list_error_codes("auth")} >= {2000, 2001, 2002, 2003, 2004, 9998}
