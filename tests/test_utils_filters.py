from __future__ import annotations

from erlc_api.models import CommandLogEntry, ModCallEntry, Player
from erlc_api.utils.filters import filter_by_timestamp, filter_command_logs, filter_mod_calls, filter_players


def _player(name: str, team: str) -> Player:
    return Player(
        name=name,
        user_id=None,
        permission="Moderator",
        team=team,
        callsign=None,
        location=None,
        raw={},
        extra={},
    )


def test_filter_players_by_name_and_team() -> None:
    players = [_player("Avi", "Police"), _player("Bee", "Civilian"), _player("Avery", "Police")]

    result = filter_players(players, name_contains="av", team="police")

    assert [item.name for item in result] == ["Avi", "Avery"]


def test_filter_command_logs_by_prefix_and_timestamp() -> None:
    entries = [
        CommandLogEntry(player="Avi", command=":help", timestamp=100, raw={}, extra={}),
        CommandLogEntry(player="Avi", command=":log abc", timestamp=120, raw={}, extra={}),
        CommandLogEntry(player="Bee", command=":help", timestamp=140, raw={}, extra={}),
    ]

    result = filter_command_logs(
        entries,
        player="avi",
        command_prefix=":log",
        min_timestamp=110,
        max_timestamp=130,
    )

    assert [entry.command for entry in result] == [":log abc"]


def test_filter_mod_calls_by_reason() -> None:
    entries = [
        ModCallEntry(player="Avi", reason="RDM", location="Gas", timestamp=100, raw={}, extra={}),
        ModCallEntry(player="Bee", reason="FailRP", location="Bank", timestamp=120, raw={}, extra={}),
    ]

    result = filter_mod_calls(entries, reason_contains="fail")

    assert [entry.player for entry in result] == ["Bee"]


def test_filter_by_timestamp_inclusive_bounds() -> None:
    entries = [
        CommandLogEntry(player="Avi", command=":help", timestamp=100, raw={}, extra={}),
        CommandLogEntry(player="Bee", command=":help", timestamp=120, raw={}, extra={}),
        CommandLogEntry(player="Cy", command=":help", timestamp=140, raw={}, extra={}),
    ]

    result = filter_by_timestamp(entries, min_timestamp=120, max_timestamp=140)

    assert [entry.player for entry in result] == ["Bee", "Cy"]
