from __future__ import annotations

import httpx
import pytest

from erlc_api import AsyncERLC, ERLC, RateLimitError, cmd
from erlc_api._constants import BASE_URL
from erlc_api._http import AsyncTransport, ClientSettings, SyncTransport


SERVER_PAYLOAD = {
    "Name": "Avi Server",
    "OwnerId": 123,
    "CoOwnerIds": [456],
    "CurrentPlayers": 2,
    "MaxPlayers": 40,
    "JoinKey": "abc",
    "AccVerifiedReq": "Disabled",
    "TeamBalance": True,
    "Players": [
        {
            "Player": "Avi:100",
            "Permission": "Server Administrator",
            "Callsign": "A-1",
            "Team": "Police",
            "WantedStars": 0,
            "Location": {"LocationX": 10.5, "LocationZ": 12.25, "PostalCode": "001"},
        }
    ],
    "Staff": {"CoOwners": [456], "Admins": {"100": "Avi"}, "Mods": {}, "Helpers": {"200": "Bee"}},
    "Queue": [100, 200],
    "JoinLogs": [{"Join": True, "Timestamp": 1700000000, "Player": "Bee:200"}],
    "KillLogs": [{"Killed": "Bee:200", "Killer": "Avi:100", "Timestamp": 1700000001}],
    "CommandLogs": [{"Player": "Avi:100", "Timestamp": 1700000002, "Command": ":h hi"}],
    "ModCalls": [{"Caller": "Bee:200", "Moderator": "Avi:100", "Timestamp": 1700000003}],
    "EmergencyCalls": [
        {
            "Team": "Police",
            "Caller": 100,
            "Players": [100, 200],
            "Position": [1.0, 2.0, 3.0],
            "StartedAt": 1700000004,
            "CallNumber": 7,
            "Description": "Help",
        }
    ],
    "Vehicles": [{"Name": "Falcon", "Owner": "Avi:100", "Texture": "Blue", "Plate": "ABC123"}],
}


class _AsyncFake:
    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        self.calls.append({"method": method, "path": path, **kwargs})
        if not self.responses:
            raise AssertionError("no response queued")
        return self.responses.pop(0)

    async def aclose(self) -> None:
        return None


class _SyncFake:
    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        self.calls.append({"method": method, "path": path, **kwargs})
        if not self.responses:
            raise AssertionError("no response queued")
        return self.responses.pop(0)

    def close(self) -> None:
        return None


def _json_response(payload: object, status: int = 200, headers: dict[str, str] | None = None) -> httpx.Response:
    merged_headers = {"content-type": "application/json"}
    if headers:
        merged_headers.update(headers)
    return httpx.Response(status, headers=merged_headers, json=payload)


def test_clients_default_to_current_api_domain() -> None:
    assert BASE_URL == "https://api.erlc.gg"
    assert ClientSettings().base_url == BASE_URL
    assert AsyncERLC("key", rate_limited=False).settings.base_url == BASE_URL
    assert ERLC("key", rate_limited=False).settings.base_url == BASE_URL


@pytest.mark.asyncio
async def test_async_flat_server_returns_typed_bundle_and_headers() -> None:
    fake = _AsyncFake([_json_response(SERVER_PAYLOAD)])
    transport = AsyncTransport(ClientSettings(retry_429=False), global_key="global")
    transport._client = fake  # type: ignore[assignment]
    api = AsyncERLC("default-key", global_key="global", transport=transport)

    bundle = await api.server(all=True)

    assert bundle.name == "Avi Server"
    assert bundle.players is not None
    assert bundle.players[0].name == "Avi"
    assert bundle.players[0].user_id == 100
    assert bundle.staff is not None
    assert bundle.staff.admins == {100: "Avi"}
    assert bundle.queue == [100, 200]
    assert bundle.emergency_calls is not None
    assert bundle.emergency_calls[0].call_number == 7
    assert fake.calls[0]["path"] == "/v2/server"
    assert fake.calls[0]["params"] == {
        "Players": "true",
        "Staff": "true",
        "JoinLogs": "true",
        "Queue": "true",
        "KillLogs": "true",
        "CommandLogs": "true",
        "ModCalls": "true",
        "EmergencyCalls": "true",
        "Vehicles": "true",
    }
    assert fake.calls[0]["headers"] == {"Server-Key": "default-key", "Authorization": "global"}


@pytest.mark.asyncio
async def test_async_flat_methods_support_raw_and_server_key_override() -> None:
    fake = _AsyncFake([_json_response(SERVER_PAYLOAD)])
    transport = AsyncTransport(ClientSettings(retry_429=False))
    transport._client = fake  # type: ignore[assignment]
    api = AsyncERLC("default-key", transport=transport)

    players = await api.players(server_key="override", raw=True)

    assert players == SERVER_PAYLOAD["Players"]
    assert fake.calls[0]["headers"] == {"Server-Key": "override"}
    assert fake.calls[0]["params"] == {"Players": "true"}


@pytest.mark.asyncio
async def test_raw_mode_shapes_are_explicit() -> None:
    command_payload = {"message": "Success", "extra": {"id": "abc"}}
    fake = _AsyncFake([_json_response(SERVER_PAYLOAD), _json_response(SERVER_PAYLOAD), _json_response(command_payload)])
    transport = AsyncTransport(ClientSettings(retry_429=False))
    transport._client = fake  # type: ignore[assignment]
    api = AsyncERLC("default-key", transport=transport)

    server_payload = await api.server(players=True, raw=True)
    players_payload = await api.players(raw=True)
    command_result = await api.command("h hi", raw=True)

    assert server_payload == SERVER_PAYLOAD
    assert players_payload == SERVER_PAYLOAD["Players"]
    assert command_result == command_payload


@pytest.mark.asyncio
async def test_async_command_uses_v2_and_flexible_builder() -> None:
    fake = _AsyncFake([_json_response({"message": "Success"})])
    transport = AsyncTransport(ClientSettings(retry_429=False))
    transport._client = fake  # type: ignore[assignment]
    api = AsyncERLC("key", transport=transport)

    result = await api.command(cmd.pm("Avi", "hello"))

    assert result.success is True
    assert result.message == "Success"
    assert fake.calls[0]["path"] == "/v2/server/command"
    assert fake.calls[0]["json"] == {"command": ":pm Avi hello"}


def test_sync_client_mirrors_flat_api() -> None:
    fake = _SyncFake([_json_response(SERVER_PAYLOAD), _json_response({"message": "Success"})])
    transport = SyncTransport(ClientSettings(retry_429=False))
    transport._client = fake  # type: ignore[assignment]
    api = ERLC("key", transport=transport)

    assert api.players()[0].name == "Avi"
    assert api.command("h hi").success is True
    assert fake.calls[1]["json"] == {"command": ":h hi"}


@pytest.mark.asyncio
async def test_rate_limit_error_exposes_retry_metadata_without_ops_stack() -> None:
    fake = _AsyncFake(
        [
            _json_response(
                {"message": "Slow down", "error_code": 4001},
                status=429,
                headers={"Retry-After": "2.5", "X-RateLimit-Bucket": "server"},
            )
        ]
    )
    transport = AsyncTransport(ClientSettings(retry_429=False))
    transport._client = fake  # type: ignore[assignment]
    api = AsyncERLC("key", transport=transport)

    with pytest.raises(RateLimitError) as excinfo:
        await api.players()

    assert excinfo.value.retry_after == 2.5
    assert excinfo.value.bucket == "server"
    assert excinfo.value.error_code == 4001


@pytest.mark.asyncio
async def test_bans_use_v1_because_v2_does_not_cover_them() -> None:
    fake = _AsyncFake([_json_response({"100": "Avi"})])
    transport = AsyncTransport(ClientSettings(retry_429=False))
    transport._client = fake  # type: ignore[assignment]
    api = AsyncERLC("key", transport=transport)

    bans = await api.bans()

    assert bans.bans == {"100": "Avi"}
    assert bans.entries[0].player_id == "100"
    assert fake.calls[0]["path"] == "/v1/server/bans"

