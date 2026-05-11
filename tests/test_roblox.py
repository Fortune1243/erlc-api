from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from erlc_api.roblox import (
    AsyncRobloxClient,
    RobloxAPIError,
    RobloxClient,
    RobloxNetworkError,
    RobloxRateLimitError,
    RobloxUser,
)


def _json_response(status: int, payload: Any, **headers: str) -> httpx.Response:
    return httpx.Response(status, json=payload, headers=headers)


def _body(request: httpx.Request) -> dict[str, Any]:
    return json.loads(request.content.decode("utf-8"))


def test_sync_profile_lookup_parses_fields_and_uses_cache() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        assert request.method == "GET"
        return _json_response(
            200,
            {
                "id": 1,
                "name": "Roblox",
                "displayName": "Roblox",
                "hasVerifiedBadge": True,
                "description": "Official account",
                "created": "2006-02-27T21:06:40.3Z",
                "isBanned": False,
                "externalAppDisplayName": None,
                "mystery": "kept",
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    roblox = RobloxClient(client=client)

    user = roblox.user(1)
    assert isinstance(user, RobloxUser)
    assert user.user_id == 1
    assert user.name == "Roblox"
    assert user.description == "Official account"
    assert user.created_at == "2006-02-27T21:06:40.3Z"
    assert user.extra == {"mystery": "kept"}
    assert user.to_dict()["display_name"] == "Roblox"
    assert roblox.username(1) == "Roblox"
    assert calls == ["/v1/users/1"]
    assert roblox.cache_stats().hits == 1

    raw = roblox.profile(1, raw=True)
    assert isinstance(raw, dict)
    assert raw["id"] == 1
    assert roblox.cache_stats().hits == 2


def test_sync_batch_users_raw_misses_and_no_negative_cache() -> None:
    bodies: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/users"
        body = _body(request)
        bodies.append(body)
        data = [
            {"id": user_id, "name": f"User{user_id}", "displayName": f"Display {user_id}"}
            for user_id in body["userIds"]
            if user_id in {1, 2}
        ]
        return _json_response(200, {"data": data})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    roblox = RobloxClient(client=client)

    users = roblox.users([1, 0, -1, 2, 999])
    assert list(users) == [1, 2]
    assert isinstance(users[1], RobloxUser)
    assert users[2].name == "User2"
    assert bodies == [{"userIds": [1, 2, 999], "excludeBannedUsers": False}]

    raw = roblox.users([1, 999], raw=True)
    assert raw[1]["id"] == 1
    assert list(raw) == [1]
    assert bodies[-1] == {"userIds": [999], "excludeBannedUsers": False}

    roblox.users([999])
    assert bodies[-1] == {"userIds": [999], "excludeBannedUsers": False}
    assert len(bodies) == 3


def test_sync_username_lookup_payload_raw_and_cache_controls() -> None:
    bodies: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/usernames/users"
        body = _body(request)
        bodies.append(body)
        data = [
            {
                "requestedUsername": name,
                "id": 1,
                "name": "Roblox",
                "displayName": "Roblox",
                "hasVerifiedBadge": True,
            }
            for name in body["usernames"]
            if name.casefold() == "roblox"
        ]
        return _json_response(200, {"data": data})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    roblox = RobloxClient(client=client)

    user = roblox.user_by_username("Roblox")
    assert isinstance(user, RobloxUser)
    assert user.requested_username == "Roblox"
    assert bodies == [{"usernames": ["Roblox"], "excludeBannedUsers": False}]

    cached = roblox.user_by_username("ROBLOX")
    assert isinstance(cached, RobloxUser)
    assert cached.user_id == 1
    assert len(bodies) == 1

    raw = roblox.users_by_username(["Roblox", "Missing"], exclude_banned_users=True, raw=True)
    assert raw["Roblox"]["requestedUsername"] == "Roblox"
    assert "Missing" not in raw
    assert bodies[-1] == {"usernames": ["Roblox", "Missing"], "excludeBannedUsers": True}

    assert roblox.cache_stats().size > 0
    roblox.clear_cache()
    assert roblox.cache_stats().size == 0


@pytest.mark.asyncio
async def test_async_client_profile_batch_and_missing() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            if request.url.path == "/v1/users/404":
                return _json_response(404, {"errors": [{"message": "Not found"}]})
            return _json_response(200, {"id": 156, "name": "builderman", "displayName": "builderman"})
        return _json_response(200, {"data": [{"id": 156, "name": "builderman", "displayName": "builderman"}]})

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    roblox = AsyncRobloxClient(client=http_client)
    try:
        profile = await roblox.profile(156)
        assert isinstance(profile, RobloxUser)
        assert profile.name == "builderman"
        assert await roblox.username(156) == "builderman"
        assert await roblox.profile(404) is None
        assert await roblox.profile(0) is None
        users = await roblox.users([156, 0])
        assert list(users) == [156]
    finally:
        await http_client.aclose()


def test_sync_errors_are_module_local() -> None:
    def rate_limited(_: httpx.Request) -> httpx.Response:
        return _json_response(429, {"message": "Too many requests"}, **{"Retry-After": "7"})

    with pytest.raises(RobloxRateLimitError) as rate_exc:
        RobloxClient(client=httpx.Client(transport=httpx.MockTransport(rate_limited))).users([1])
    assert rate_exc.value.retry_after_s == 7
    assert rate_exc.value.status == 429

    def failed(_: httpx.Request) -> httpx.Response:
        return _json_response(500, {"message": "Roblox is unavailable"})

    with pytest.raises(RobloxAPIError, match="Roblox is unavailable"):
        RobloxClient(client=httpx.Client(transport=httpx.MockTransport(failed))).users([1])

    def network_error(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    with pytest.raises(RobloxNetworkError, match="boom"):
        RobloxClient(client=httpx.Client(transport=httpx.MockTransport(network_error))).users([1])
