from __future__ import annotations

from erlc_api.models import Player, QueueEntry, StaffMember, V2ServerBundle
from erlc_api.utils.diff import diff_players, diff_queue, diff_server_default, diff_staff


def _player(name: str, user_id: int) -> Player:
    return Player(
        name=name,
        user_id=user_id,
        permission=None,
        team=None,
        callsign=None,
        location=None,
        raw={},
        extra={},
    )


def _queue(player: str, position: int) -> QueueEntry:
    return QueueEntry(player=player, position=position, timestamp=None, raw={}, extra={})


def _staff(name: str) -> StaffMember:
    return StaffMember(name=name, callsign=None, permission="Admin", raw={}, extra={})


def test_diff_players_detects_join_and_leave() -> None:
    previous = [_player("Avi", 1), _player("Bee", 2)]
    current = [_player("Bee", 2), _player("Cy", 3)]

    result = diff_players(previous, current)

    assert [item.name for item in result.joined] == ["Cy"]
    assert [item.name for item in result.left] == ["Avi"]
    assert [item.name for item in result.stayed] == ["Bee"]


def test_diff_staff_detects_added_removed_unchanged() -> None:
    previous = [_staff("A"), _staff("B")]
    current = [_staff("B"), _staff("C")]

    result = diff_staff(previous, current)

    assert [item.name for item in result.added] == ["C"]
    assert [item.name for item in result.removed] == ["A"]
    assert [item.name for item in result.unchanged] == ["B"]


def test_diff_queue_detects_movement() -> None:
    previous = [_queue("Avi", 2), _queue("Bee", 1)]
    current = [_queue("Avi", 1), _queue("Bee", 2)]

    result = diff_queue(previous, current)

    assert result.joined == []
    assert result.left == []
    assert len(result.moved) == 2


def test_diff_server_default_uses_available_sections() -> None:
    previous = V2ServerBundle(
        players=[_player("Avi", 1)],
        staff=[_staff("Mod")],
        join_logs=None,
        queue=[_queue("Avi", 1)],
        kill_logs=None,
        command_logs=None,
        mod_calls=None,
        vehicles=None,
        server_name=None,
        current_players=None,
        max_players=None,
        raw={},
        extra={},
    )
    current = V2ServerBundle(
        players=[_player("Avi", 1), _player("Bee", 2)],
        staff=[_staff("Mod")],
        join_logs=None,
        queue=[_queue("Avi", 1)],
        kill_logs=None,
        command_logs=None,
        mod_calls=None,
        vehicles=None,
        server_name=None,
        current_players=None,
        max_players=None,
        raw={},
        extra={},
    )

    result = diff_server_default(previous, current)

    assert result.players is not None
    assert [item.name for item in result.players.joined] == ["Bee"]
    assert result.queue is not None
    assert result.staff is not None
