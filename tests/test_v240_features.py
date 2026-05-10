from __future__ import annotations

import pytest

from erlc_api import (
    CommandPolicy,
    CommandResult,
    PermissionLevel,
    Player,
    PlayerLocation,
    ServerBundle,
    StaffMember,
    Vehicle,
)
from erlc_api.analytics import Analyzer
from erlc_api.commands import get_command_metadata
from erlc_api.emergency import EmergencyCallTools
from erlc_api.filter import Filter
from erlc_api.find import Finder
from erlc_api.models import EmergencyCall, decode_command_result, decode_server_bundle
from erlc_api.ratelimit import RateLimiter
from erlc_api.security import AuthFailureTracker, key_fingerprint
from erlc_api.vehicles import PlayerVehicleBundle, VehicleTools, parse_vehicle_name
from erlc_api.watch import AsyncWatcher


def test_permission_level_properties_keep_raw_permission_string() -> None:
    player = Player(name="Avi", permission="Server Administrator")
    staff = StaffMember(name="Bee", role="Mod")

    assert player.permission == "Server Administrator"
    assert player.permission_level is PermissionLevel.ADMIN
    assert staff.permission_level is PermissionLevel.MOD
    assert PermissionLevel.ADMIN > PermissionLevel.MOD


def test_command_result_command_id_and_metadata() -> None:
    result = decode_command_result({"message": "Success", "commandId": "abc-123", "Extra": True})
    metadata = get_command_metadata(":pm Avi hello")

    assert result.command_id == "abc-123"
    assert result.extra == {"Extra": True}
    assert metadata is not None
    assert metadata.display_name == "Private Message"
    assert metadata.supports_target is True
    assert "Kick Player" in (CommandPolicy(allowed={"h"}).check("kick Avi").reason or "")
    assert Analyzer(ServerBundle(command_logs=[])).command_categories() == {}


def test_vehicle_parser_tools_and_player_vehicle_bundle() -> None:
    vehicle = Vehicle(
        name="2020 Falcon Advance 350",
        owner="Avi:1",
        texture="Ghost",
        plate="abc123",
        color_name="Blue",
        color_hex="#0000ff",
    )
    secondary = Vehicle(name="4-Wheeler", owner="Bee:2", texture="Custom", plate="ABC123")
    players = [Player(name="Avi", user_id=1, team="Police"), Player(name="Bee", user_id=2, team="Civilian")]
    tools = VehicleTools([vehicle, secondary])

    parsed = parse_vehicle_name("2020 Falcon Advance 350")

    assert parsed.is_known is True
    assert parsed.model == "Falcon Advance 350"
    assert parsed.year == 2020
    assert vehicle.model_name == "Falcon Advance 350"
    assert vehicle.owner_name == "Avi"
    assert vehicle.owner_id == 1
    assert vehicle.normalized_plate == "ABC123"
    assert vehicle.is_custom_texture is False
    assert secondary.is_secondary is True
    assert tools.by_owner("Avi") == [vehicle]
    assert tools.by_team("Police", players=players) == [vehicle]
    assert tools.by_color("blue") == [vehicle]
    assert tools.by_model("Falcon Advance 350") == [vehicle]
    assert tools.find_plate("abc") == [vehicle, secondary]
    assert tools.duplicate_plates()["ABC123"] == [vehicle, secondary]
    assert tools.abandoned([players[0]]) == [secondary]
    assert tools.summary().total == 2

    joined = PlayerVehicleBundle(players, [vehicle, secondary])
    assert joined.player("Avi").vehicles == [vehicle]  # type: ignore[union-attr]
    assert joined.vehicle("abc").owner_player == players[0]  # type: ignore[union-attr]


def test_server_bundle_player_vehicles_property() -> None:
    bundle = ServerBundle(
        players=[Player(name="Avi", user_id=1)],
        vehicles=[Vehicle(name="2020 Falcon Advance 350", owner="Avi:1")],
    )

    assert bundle.player_vehicles is not None
    assert bundle.player_vehicles.vehicles_for("Avi")
    assert ServerBundle(players=[Player(name="Avi")]).player_vehicles is None


def test_wanted_filter_finder_and_sorter() -> None:
    players = [
        Player(name="Avi", wanted_stars=0, permission="Normal"),
        Player(name="Bee", wanted_stars=3, permission="Server Moderator"),
        Player(name="Cat", wanted_stars=1, permission="Server Administrator"),
    ]

    assert [player.name for player in Filter(players).wanted(stars=2).all()] == ["Bee"]
    assert [player.name for player in Filter(players).permission_at_least(PermissionLevel.MOD).all()] == ["Bee", "Cat"]
    assert [player.name for player in Finder(players).wanted()] == ["Bee", "Cat"]


def test_emergency_call_tools() -> None:
    calls = [
        EmergencyCall(team="Police", players=[], position=[0, 0, 0], started_at=10, call_number=1),
        EmergencyCall(team="Fire", players=[1], position=[10, 0, 0], started_at=11, call_number=2),
    ]
    player = Player(name="Avi", location=None)
    near_player = Player(name="Bee", location=PlayerLocation(location_x=1.0, location_z=0.0))
    tools = EmergencyCallTools(calls)

    assert tools.unresponded() == [calls[0]]
    assert tools.by_team("fire") == [calls[1]]
    assert tools.nearest_to([1, 0]) == calls[0]
    assert tools.nearest_to(player) is None
    assert tools.nearest_players_to_call(calls[0], [near_player], limit=1) == [near_player]
    assert tools.summary().by_team == {"Police": 1, "Fire": 1}


@pytest.mark.asyncio
async def test_watcher_emits_wanted_change_events() -> None:
    class API:
        def __init__(self) -> None:
            self.calls = 0

        async def server(self, *, server_key=None, all=False):  # noqa: ARG002, A002
            self.calls += 1
            return ServerBundle(players=[Player(name="Avi", user_id=1, wanted_stars=0 if self.calls == 1 else 2)])

    event_types = []
    async for event in AsyncWatcher(API(), interval_s=0).events(limit=3):
        event_types.append(event.type)

    assert "wanted_new" in event_types
    assert "wanted_change" in event_types


def test_rate_limiter_known_bucket_queues_and_no_hidden_client_cache() -> None:
    now = 100.0
    sleeps: list[float] = []

    def clock() -> float:
        return now

    def sleep(delay: float) -> None:
        nonlocal now
        sleeps.append(delay)
        now += delay

    limiter = RateLimiter(now=clock, sleep=sleep)
    limiter.after_response("GET", "/v2/server", {"X-RateLimit-Bucket": "server", "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "105"})

    assert limiter.before_request("GET", "/v2/server") == 5.0
    assert limiter.before_request("GET", "/v2/server") == 0.0
    assert sleeps == [5.0]


def test_auth_failure_tracker_uses_key_fingerprints_without_storing_secrets() -> None:
    tracker = AuthFailureTracker(now=lambda: 123.0)
    first = tracker.mark("server-secret-key")
    second = tracker.mark("server-secret-key")

    assert second.repeated is True
    assert second.count == 2
    assert first.fingerprint == key_fingerprint("server-secret-key")
    assert "server-secret-key" not in second.fingerprint
    assert tracker.get(second.fingerprint) == second


def test_decode_server_bundle_vehicle_and_command_fields() -> None:
    bundle = decode_server_bundle(
        {
            "Name": "Server",
            "Players": [{"Player": "Avi:1", "Permission": "Server Moderator", "WantedStars": 2}],
            "Vehicles": [{"Name": "2020 Falcon Advance 350", "Owner": "Avi:1", "Plate": "abc"}],
        }
    )

    assert bundle.players[0].permission_level is PermissionLevel.MOD  # type: ignore[index]
    assert bundle.vehicles[0].year == 2020  # type: ignore[index]
    assert isinstance(CommandResult(command_id="local").command_id, str)
