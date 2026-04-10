from __future__ import annotations

from erlc_api.models import Player, QueueEntry, StaffMember, V2ServerBundle, Vehicle
from erlc_api.web import compute_dashboard_metrics, players_to_dto, v2_bundle_to_dto


def _player(name: str, team: str) -> Player:
    return Player(
        name=name,
        user_id=None,
        permission="Mod",
        team=team,
        callsign=None,
        location=None,
        raw={},
        extra={"x": 1},
    )


def test_players_to_dto_has_stable_keys() -> None:
    players = [_player("Avi", "Police")]

    result = players_to_dto(players)

    assert result == [
        {
            "name": "Avi",
            "user_id": None,
            "permission": "Mod",
            "team": "Police",
            "callsign": None,
            "location": None,
            "extra": {"x": 1},
        }
    ]


def test_v2_bundle_to_dto_and_metrics() -> None:
    bundle = V2ServerBundle(
        players=[_player("Avi", "Police"), _player("Bee", "Civilian")],
        staff=[StaffMember(name="Mod1", callsign=None, permission="Admin", raw={}, extra={})],
        join_logs=None,
        queue=[QueueEntry(player="Avi", position=1, timestamp=1, raw={}, extra={})],
        kill_logs=None,
        command_logs=None,
        mod_calls=None,
        vehicles=[
            Vehicle(owner="Avi", model="SUV", color="Black", plate="ABC123", team="Police", raw={}, extra={})
        ],
        server_name="Test",
        current_players=2,
        max_players=40,
        raw={},
        extra={"unknown": True},
    )

    dto = v2_bundle_to_dto(bundle)
    metrics = compute_dashboard_metrics(bundle)

    assert dto["server_name"] == "Test"
    assert dto["players"] is not None and len(dto["players"]) == 2
    assert dto["extra"] == {"unknown": True}
    assert metrics.player_count == 2
    assert metrics.queue_count == 1
    assert metrics.staff_count == 1
    assert metrics.vehicle_count == 1
    assert metrics.players_by_team == {"Police": 1, "Civilian": 1}
