from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator

from ..client import AsyncERLC
from ..models import CommandLogEntry, ModCallEntry, Player
from ..utils.polling import poll_players


@dataclass(frozen=True)
class PlayerJoinEvent:
    player: Player
    fetched_at_epoch: float

    @property
    def fetched_at(self) -> datetime:
        return datetime.fromtimestamp(self.fetched_at_epoch, tz=timezone.utc)


@dataclass(frozen=True)
class PlayerLeaveEvent:
    player: Player
    fetched_at_epoch: float

    @property
    def fetched_at(self) -> datetime:
        return datetime.fromtimestamp(self.fetched_at_epoch, tz=timezone.utc)


@dataclass(frozen=True)
class ModCallEvent:
    entry: ModCallEntry
    fetched_at_epoch: float

    @property
    def fetched_at(self) -> datetime:
        return datetime.fromtimestamp(self.fetched_at_epoch, tz=timezone.utc)


@dataclass(frozen=True)
class CommandLogEvent:
    entry: CommandLogEntry
    fetched_at_epoch: float

    @property
    def fetched_at(self) -> datetime:
        return datetime.fromtimestamp(self.fetched_at_epoch, tz=timezone.utc)


def _validate_interval(interval_s: float) -> None:
    if interval_s <= 0:
        raise ValueError("interval_s must be greater than zero.")


def _mod_call_key(entry: ModCallEntry) -> str:
    return "|".join([str(entry.timestamp), entry.caller or "", entry.moderator or ""])


def _command_log_key(entry: CommandLogEntry) -> str:
    return "|".join([str(entry.timestamp), entry.player or "", entry.command or ""])


async def iter_player_events(
    client: AsyncERLC,
    *,
    server_key: str | None = None,
    interval_s: float = 5.0,
    include_initial: bool = False,
) -> AsyncIterator[PlayerJoinEvent | PlayerLeaveEvent]:
    async for snapshot in poll_players(client, server_key=server_key, interval_s=interval_s):
        if snapshot.previous is None:
            if include_initial:
                for player in snapshot.current:
                    yield PlayerJoinEvent(player=player, fetched_at_epoch=snapshot.fetched_at_epoch)
            continue
        if snapshot.diff is None:
            continue
        for player in snapshot.diff.joined:
            yield PlayerJoinEvent(player=player, fetched_at_epoch=snapshot.fetched_at_epoch)
        for player in snapshot.diff.left:
            yield PlayerLeaveEvent(player=player, fetched_at_epoch=snapshot.fetched_at_epoch)


async def iter_mod_call_events(
    client: AsyncERLC,
    *,
    server_key: str | None = None,
    interval_s: float = 5.0,
    include_initial: bool = False,
) -> AsyncIterator[ModCallEvent]:
    _validate_interval(interval_s)
    previous_keys: set[str] | None = None
    while True:
        current = await client.mod_calls(server_key=server_key)
        if previous_keys is None:
            if include_initial:
                for entry in current:
                    yield ModCallEvent(entry=entry, fetched_at_epoch=datetime.now(tz=timezone.utc).timestamp())
            previous_keys = {_mod_call_key(entry) for entry in current}
            await asyncio.sleep(interval_s)
            continue
        current_keys = {_mod_call_key(entry) for entry in current}
        for entry in current:
            key = _mod_call_key(entry)
            if key not in previous_keys:
                yield ModCallEvent(entry=entry, fetched_at_epoch=datetime.now(tz=timezone.utc).timestamp())
        previous_keys = current_keys
        await asyncio.sleep(interval_s)


async def iter_command_log_events(
    client: AsyncERLC,
    *,
    server_key: str | None = None,
    interval_s: float = 5.0,
    include_initial: bool = False,
) -> AsyncIterator[CommandLogEvent]:
    _validate_interval(interval_s)
    previous_keys: set[str] | None = None
    while True:
        current = await client.command_logs(server_key=server_key)
        if previous_keys is None:
            if include_initial:
                for entry in current:
                    yield CommandLogEvent(entry=entry, fetched_at_epoch=datetime.now(tz=timezone.utc).timestamp())
            previous_keys = {_command_log_key(entry) for entry in current}
            await asyncio.sleep(interval_s)
            continue
        current_keys = {_command_log_key(entry) for entry in current}
        for entry in current:
            key = _command_log_key(entry)
            if key not in previous_keys:
                yield CommandLogEvent(entry=entry, fetched_at_epoch=datetime.now(tz=timezone.utc).timestamp())
        previous_keys = current_keys
        await asyncio.sleep(interval_s)


__all__ = [
    "CommandLogEvent",
    "ModCallEvent",
    "PlayerJoinEvent",
    "PlayerLeaveEvent",
    "iter_command_log_events",
    "iter_mod_call_events",
    "iter_player_events",
]
