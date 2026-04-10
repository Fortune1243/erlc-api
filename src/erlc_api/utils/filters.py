from __future__ import annotations

from typing import Protocol, TypeVar

from ..models import CommandLogEntry, ModCallEntry, Player


class _Timestamped(Protocol):
    timestamp: int | None


TS = TypeVar("TS", bound=_Timestamped)


def _contains_ci(haystack: str | None, needle: str | None) -> bool:
    if needle is None:
        return True
    if haystack is None:
        return False
    return needle.lower() in haystack.lower()


def _equals_ci(lhs: str | None, rhs: str | None) -> bool:
    if rhs is None:
        return True
    if lhs is None:
        return False
    return lhs.lower() == rhs.lower()


def _prefix_ci(value: str | None, prefix: str | None) -> bool:
    if prefix is None:
        return True
    if value is None:
        return False
    return value.lower().startswith(prefix.lower())


def filter_players(
    players: list[Player],
    *,
    name_contains: str | None = None,
    team: str | None = None,
    permission: str | None = None,
    callsign: str | None = None,
) -> list[Player]:
    filtered: list[Player] = []
    for player in players:
        if not _contains_ci(player.name, name_contains):
            continue
        if not _equals_ci(player.team, team):
            continue
        if not _equals_ci(player.permission, permission):
            continue
        if not _equals_ci(player.callsign, callsign):
            continue
        filtered.append(player)
    return filtered


def filter_by_timestamp(
    entries: list[TS],
    *,
    min_timestamp: int | None = None,
    max_timestamp: int | None = None,
) -> list[TS]:
    filtered: list[TS] = []
    for entry in entries:
        ts = entry.timestamp
        if ts is None:
            continue
        if min_timestamp is not None and ts < min_timestamp:
            continue
        if max_timestamp is not None and ts > max_timestamp:
            continue
        filtered.append(entry)
    return filtered


def filter_command_logs(
    entries: list[CommandLogEntry],
    *,
    player: str | None = None,
    command_prefix: str | None = None,
    command_contains: str | None = None,
    min_timestamp: int | None = None,
    max_timestamp: int | None = None,
) -> list[CommandLogEntry]:
    filtered: list[CommandLogEntry] = []
    for entry in entries:
        if not _equals_ci(entry.player, player):
            continue
        if not _prefix_ci(entry.command, command_prefix):
            continue
        if not _contains_ci(entry.command, command_contains):
            continue
        ts = entry.timestamp
        if min_timestamp is not None and (ts is None or ts < min_timestamp):
            continue
        if max_timestamp is not None and (ts is None or ts > max_timestamp):
            continue
        filtered.append(entry)
    return filtered


def filter_mod_calls(
    entries: list[ModCallEntry],
    *,
    player: str | None = None,
    reason_contains: str | None = None,
    location_contains: str | None = None,
    min_timestamp: int | None = None,
    max_timestamp: int | None = None,
) -> list[ModCallEntry]:
    filtered: list[ModCallEntry] = []
    for entry in entries:
        if not _equals_ci(entry.player, player):
            continue
        if not _contains_ci(entry.reason, reason_contains):
            continue
        if not _contains_ci(entry.location, location_contains):
            continue
        ts = entry.timestamp
        if min_timestamp is not None and (ts is None or ts < min_timestamp):
            continue
        if max_timestamp is not None and (ts is None or ts > max_timestamp):
            continue
        filtered.append(entry)
    return filtered


__all__ = [
    "filter_by_timestamp",
    "filter_command_logs",
    "filter_mod_calls",
    "filter_players",
]
