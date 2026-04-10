from __future__ import annotations

import pytest

from erlc_api import ERLCClient
from erlc_api.models import CommandLogEntry, Player, StaffMember, V2ServerBundle, Vehicle
from erlc_api.tracking import ServerTracker


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


def _staff(name: str) -> StaffMember:
    return StaffMember(name=name, callsign=None, permission="Admin", raw={}, extra={})


def _bundle(players: list[Player], staff: list[StaffMember], command_logs: list[CommandLogEntry]) -> V2ServerBundle:
    return V2ServerBundle(
        players=players,
        staff=staff,
        helpers=None,
        join_logs=None,
        queue=None,
        kill_logs=None,
        command_logs=command_logs,
        mod_calls=None,
        vehicles=[Vehicle(owner=None, model="Falcon", color=None, plate=None, team=None, raw={}, extra={})],
        emergency_calls=None,
        server_name=None,
        current_players=None,
        max_players=None,
        raw={},
        extra={},
    )


@pytest.mark.asyncio
async def test_server_tracker_emits_join_leave_and_command_events() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")
    tracker = ServerTracker(api, ctx, interval_s=0.01)

    events: list[tuple[str, str]] = []
    tracker.on("player_join", lambda player: events.append(("join", player.name or "")))
    tracker.on("player_leave", lambda player: events.append(("leave", player.name or "")))
    tracker.on("command_executed", lambda entry: events.append(("command", entry.command or "")))

    await tracker._apply_bundle(_bundle([_player("Avi", 1)], [_staff("Mod")], []))
    await tracker._apply_bundle(
        _bundle(
            [_player("Bee", 2)],
            [_staff("Mod")],
            [CommandLogEntry(player="Bee", command=":help", timestamp=1, raw={}, extra={})],
        )
    )

    assert ("join", "Avi") in events
    assert ("leave", "Avi") in events
    assert ("join", "Bee") in events
    assert ("command", ":help") in events
