from __future__ import annotations

import asyncio
import time as time_mod
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Iterator

from .diff import BundleDiff, Differ


@dataclass(frozen=True)
class WatchEvent:
    type: str
    item: Any = None
    diff: BundleDiff | None = None
    snapshot: Any = None


def _events_from_diff(diff: BundleDiff, snapshot: Any) -> list[WatchEvent]:
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
            previous = current
            for event in _events_from_diff(diff, current):
                await self._emit(event)
                emitted += 1
                yield event
                if limit is not None and emitted >= limit:
                    break


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
            previous = current
            for event in _events_from_diff(diff, current):
                self._emit(event)
                emitted += 1
                yield event
                if limit is not None and emitted >= limit:
                    break


__all__ = ["AsyncWatcher", "Watcher", "WatchEvent"]
