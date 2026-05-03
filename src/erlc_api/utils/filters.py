from __future__ import annotations

from typing import Protocol, TypeVar

from ..models import CommandLogEntry, ModCallEntry, Player, Vehicle


class _Timestamped(Protocol):
    timestamp: int | None


TS = TypeVar("TS", bound=_Timestamped)


def _contains_ci(haystack: str | None, needle: str | None) -> bool:
    if needle is None:
        return True
    return haystack is not None and needle.lower() in haystack.lower()


def _equals_ci(lhs: str | None, rhs: str | None) -> bool:
    if rhs is None:
        return True
    return lhs is not None and lhs.lower() == rhs.lower()


def _prefix_ci(value: str | None, prefix: str | None) -> bool:
    if prefix is None:
        return True
    return value is not None and value.lower().startswith(prefix.lower())


def filter_players(
    players: list[Player],
    *,
    name_contains: str | None = None,
    team: str | None = None,
    permission: str | None = None,
    callsign: str | None = None,
    user_id: int | None = None,
) -> list[Player]:
    out: list[Player] = []
    for player in players:
        if user_id is not None and player.user_id != user_id:
            continue
        if not _contains_ci(player.name, name_contains):
            continue
        if not _equals_ci(player.team, team):
            continue
        if not _equals_ci(player.permission, permission):
            continue
        if not _equals_ci(player.callsign, callsign):
            continue
        out.append(player)
    return out


def find_player(players: list[Player], query: str | int) -> Player | None:
    if isinstance(query, int):
        for player in players:
            if player.user_id == query:
                return player
        return None
    lowered = query.strip().lower()
    for player in players:
        if (player.name or "").lower() == lowered or (player.player or "").lower() == lowered:
            return player
    for player in players:
        if player.name and lowered in player.name.lower():
            return player
    return None


def filter_vehicles(
    vehicles: list[Vehicle],
    *,
    name_contains: str | None = None,
    owner: str | None = None,
    color: str | None = None,
) -> list[Vehicle]:
    out: list[Vehicle] = []
    for vehicle in vehicles:
        if not _contains_ci(vehicle.name, name_contains):
            continue
        if not _equals_ci(vehicle.owner, owner):
            continue
        if color is not None and not (
            _contains_ci(vehicle.color_name, color) or _contains_ci(vehicle.color_hex, color)
        ):
            continue
        out.append(vehicle)
    return out


def filter_by_timestamp(
    entries: list[TS],
    *,
    min_timestamp: int | None = None,
    max_timestamp: int | None = None,
) -> list[TS]:
    out: list[TS] = []
    for entry in entries:
        ts = entry.timestamp
        if ts is None:
            continue
        if min_timestamp is not None and ts < min_timestamp:
            continue
        if max_timestamp is not None and ts > max_timestamp:
            continue
        out.append(entry)
    return out


def filter_command_logs(
    entries: list[CommandLogEntry],
    *,
    player: str | None = None,
    command_prefix: str | None = None,
    command_contains: str | None = None,
    min_timestamp: int | None = None,
    max_timestamp: int | None = None,
) -> list[CommandLogEntry]:
    out: list[CommandLogEntry] = []
    for entry in entries:
        if not _equals_ci(entry.player, player) and not _equals_ci(entry.name, player):
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
        out.append(entry)
    return out


def filter_mod_calls(
    entries: list[ModCallEntry],
    *,
    caller: str | None = None,
    moderator: str | None = None,
    min_timestamp: int | None = None,
    max_timestamp: int | None = None,
    player: str | None = None,
) -> list[ModCallEntry]:
    wanted_caller = caller or player
    out: list[ModCallEntry] = []
    for entry in entries:
        if not _equals_ci(entry.caller, wanted_caller) and not _equals_ci(entry.caller_name, wanted_caller):
            continue
        if not _equals_ci(entry.moderator, moderator) and not _equals_ci(entry.moderator_name, moderator):
            continue
        ts = entry.timestamp
        if min_timestamp is not None and (ts is None or ts < min_timestamp):
            continue
        if max_timestamp is not None and (ts is None or ts > max_timestamp):
            continue
        out.append(entry)
    return out


__all__ = [
    "filter_by_timestamp",
    "filter_command_logs",
    "filter_mod_calls",
    "filter_players",
    "filter_vehicles",
    "find_player",
]
