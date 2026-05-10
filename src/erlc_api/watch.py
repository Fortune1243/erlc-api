from __future__ import annotations

import asyncio
import time as time_mod
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Iterator

from . import _utility as u
from .diff import BundleDiff, Differ


@dataclass(frozen=True)
class WatchEvent:
    type: str
    item: Any = None
    diff: BundleDiff | None = None
    snapshot: Any = None


def _player_key(item: Any) -> Any:
    return u.get_value(item, "user_id") or u.get_value(item, "name") or u.get_value(item, "player")


def _wanted_events(previous: Any, current: Any, diff: BundleDiff) -> list[WatchEvent]:
    previous_players = {_player_key(player): player for player in u.players(previous) if _player_key(player) is not None}
    events: list[WatchEvent] = []
    for player in u.players(current):
        old = previous_players.get(_player_key(player))
        if old is None:
            continue
        before = u.get_value(old, "wanted_stars") or 0
        after = u.get_value(player, "wanted_stars") or 0
        if before == after:
            continue
        if before <= 0 < after:
            event_type = "wanted_new"
        elif before > 0 >= after:
            event_type = "wanted_cleared"
        elif after > before:
            event_type = "wanted_escalated"
        else:
            event_type = "wanted_decreased"
        events.append(WatchEvent(event_type, item=player, diff=diff, snapshot=current))
        events.append(WatchEvent("wanted_change", item=player, diff=diff, snapshot=current))
    return events


def _events_from_diff(diff: BundleDiff, previous: Any, snapshot: Any) -> list[WatchEvent]:
    events = [WatchEvent("snapshot", diff=diff, snapshot=snapshot)]
    for item in diff.players.added:
        events.append(WatchEvent("player_join", item=item, diff=diff, snapshot=snapshot))
    for item in diff.players.removed:
        events.append(WatchEvent("player_leave", item=item, diff=diff, snapshot=snapshot))
    for item in diff.staff.added:
        events.append(WatchEvent("staff_join", item=item, diff=diff, snapshot=snapshot))
    for item in diff.staff.removed:
        events.append(WatchEvent("staff_leave", item=item, diff=diff, snapshot=snapshot))
    for item in diff.queue.added + diff.queue.removed:
        events.append(WatchEvent("queue_change", item=item, diff=diff, snapshot=snapshot))
    for item in diff.command_logs.added:
        events.append(WatchEvent("command_executed", item=item, diff=diff, snapshot=snapshot))
    for item in diff.mod_calls.added:
        events.append(WatchEvent("mod_call", item=item, diff=diff, snapshot=snapshot))
    for item in diff.emergency_calls.added:
        events.append(WatchEvent("emergency_call", item=item, diff=diff, snapshot=snapshot))
    for item in diff.vehicles.added + diff.vehicles.removed:
        events.append(WatchEvent("vehicle_change", item=item, diff=diff, snapshot=snapshot))
    events.extend(_wanted_events(previous, snapshot, diff))
    return events


class AsyncWatcher:
    """Async snapshot watcher with optional callbacks."""

    def __init__(self, api: Any, *, server_key: str | None = None, interval_s: float = 2.0) -> None:
        self.api = api
        self.server_key = server_key
        self.interval_s = interval_s
        self._callbacks: dict[str, list[Callable[[WatchEvent], Any]]] = {}

    def on(self, event_type: str, callback: Callable[[WatchEvent], Any]) -> AsyncWatcher:
        self._callbacks.setdefault(event_type, []).append(callback)
        return self

    async def _emit(self, event: WatchEvent) -> None:
        for callback in self._callbacks.get(event.type, []) + self._callbacks.get("*", []):
            result = callback(event)
            if asyncio.iscoroutine(result):
                await result

    async def events(self, *, limit: int | None = None) -> AsyncIterator[WatchEvent]:
        previous = await self.api.server(server_key=self.server_key, all=True)
        emitted = 0
        while limit is None or emitted < limit:
            await asyncio.sleep(self.interval_s)
            current = await self.api.server(server_key=self.server_key, all=True)
            diff = Differ(previous, current).bundle()
            for event in _events_from_diff(diff, previous, current):
                await self._emit(event)
                emitted += 1
                yield event
                if limit is not None and emitted >= limit:
                    break
            previous = current


class Watcher:
    """Sync snapshot watcher with optional callbacks."""

    def __init__(self, api: Any, *, server_key: str | None = None, interval_s: float = 2.0) -> None:
        self.api = api
        self.server_key = server_key
        self.interval_s = interval_s
        self._callbacks: dict[str, list[Callable[[WatchEvent], Any]]] = {}

    def on(self, event_type: str, callback: Callable[[WatchEvent], Any]) -> Watcher:
        self._callbacks.setdefault(event_type, []).append(callback)
        return self

    def _emit(self, event: WatchEvent) -> None:
        for callback in self._callbacks.get(event.type, []) + self._callbacks.get("*", []):
            callback(event)

    def events(self, *, limit: int | None = None) -> Iterator[WatchEvent]:
        previous = self.api.server(server_key=self.server_key, all=True)
        emitted = 0
        while limit is None or emitted < limit:
            time_mod.sleep(self.interval_s)
            current = self.api.server(server_key=self.server_key, all=True)
            diff = Differ(previous, current).bundle()
            for event in _events_from_diff(diff, previous, current):
                self._emit(event)
                emitted += 1
                yield event
                if limit is not None and emitted >= limit:
                    break
            previous = current


__all__ = ["AsyncWatcher", "Watcher", "WatchEvent"]
