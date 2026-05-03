from __future__ import annotations

import asyncio
import time as time_mod
from typing import Any, Callable

from .find import Finder


def _deadline(timeout_s: float) -> float:
    if timeout_s <= 0:
        raise ValueError("timeout_s must be greater than zero.")
    return time_mod.monotonic() + timeout_s


def _validate_interval(interval_s: float) -> None:
    if interval_s <= 0:
        raise ValueError("interval_s must be greater than zero.")


def _player_key(player: Any) -> Any:
    return getattr(player, "user_id", None) or getattr(player, "name", None) or getattr(player, "player", None)


class AsyncWaiter:
    """Async polling helper for common ER:LC conditions."""

    def __init__(self, api: Any, *, server_key: str | None = None, interval_s: float = 2.0) -> None:
        _validate_interval(interval_s)
        self.api = api
        self.server_key = server_key
        self.interval_s = interval_s

    async def _sleep(self, interval_s: float | None) -> None:
        await asyncio.sleep(self.interval_s if interval_s is None else interval_s)

    async def player_join(self, query: str | int, *, timeout_s: float = 60.0, interval_s: float | None = None):
        seen = {_player_key(player) for player in await self.api.players(server_key=self.server_key)}
        end = _deadline(timeout_s)
        while time_mod.monotonic() < end:
            current = await self.api.players(server_key=self.server_key)
            match = Finder(current).player(query)
            if match is not None and _player_key(match) not in seen:
                return match
            await self._sleep(interval_s)
        raise TimeoutError(f"Timed out waiting for player to join: {query}")

    async def player_leave(self, query: str | int, *, timeout_s: float = 60.0, interval_s: float | None = None):
        initial = Finder(await self.api.players(server_key=self.server_key)).player(query)
        end = _deadline(timeout_s)
        while time_mod.monotonic() < end:
            if Finder(await self.api.players(server_key=self.server_key)).player(query) is None:
                return initial
            await self._sleep(interval_s)
        raise TimeoutError(f"Timed out waiting for player to leave: {query}")

    async def staff_appears(self, query: str | int, *, timeout_s: float = 60.0, interval_s: float | None = None):
        end = _deadline(timeout_s)
        while time_mod.monotonic() < end:
            match = Finder(await self.api.staff(server_key=self.server_key)).staff_member(query)
            if match is not None:
                return match
            await self._sleep(interval_s)
        raise TimeoutError(f"Timed out waiting for staff member: {query}")

    async def command_log(
        self,
        *,
        command_prefix: str | None = None,
        contains: str | None = None,
        player: str | int | None = None,
        timeout_s: float = 60.0,
        interval_s: float | None = None,
    ):
        end = _deadline(timeout_s)
        while time_mod.monotonic() < end:
            match = Finder(await self.api.command_logs(server_key=self.server_key)).command_log(
                player=player,
                command_prefix=command_prefix,
                command_contains=contains,
            )
            if match is not None:
                return match
            await self._sleep(interval_s)
        raise TimeoutError("Timed out waiting for command log")

    async def queue_change(self, *, timeout_s: float = 60.0, interval_s: float | None = None) -> list[int]:
        previous = await self.api.queue(server_key=self.server_key)
        end = _deadline(timeout_s)
        while time_mod.monotonic() < end:
            current = await self.api.queue(server_key=self.server_key)
            if current != previous:
                return current
            await self._sleep(interval_s)
        raise TimeoutError("Timed out waiting for queue change")

    async def player_count(
        self,
        predicate: Callable[[int], bool] | None = None,
        *,
        equals: int | None = None,
        at_least: int | None = None,
        at_most: int | None = None,
        timeout_s: float = 60.0,
        interval_s: float | None = None,
    ) -> int:
        end = _deadline(timeout_s)
        while time_mod.monotonic() < end:
            count = len(await self.api.players(server_key=self.server_key))
            ok = predicate(count) if predicate is not None else True
            ok = ok and (equals is None or count == equals)
            ok = ok and (at_least is None or count >= at_least)
            ok = ok and (at_most is None or count <= at_most)
            if ok:
                return count
            await self._sleep(interval_s)
        raise TimeoutError("Timed out waiting for player count condition")


class Waiter:
    """Sync polling helper for common ER:LC conditions."""

    def __init__(self, api: Any, *, server_key: str | None = None, interval_s: float = 2.0) -> None:
        _validate_interval(interval_s)
        self.api = api
        self.server_key = server_key
        self.interval_s = interval_s

    def _sleep(self, interval_s: float | None) -> None:
        time_mod.sleep(self.interval_s if interval_s is None else interval_s)

    def player_join(self, query: str | int, *, timeout_s: float = 60.0, interval_s: float | None = None):
        seen = {_player_key(player) for player in self.api.players(server_key=self.server_key)}
        end = _deadline(timeout_s)
        while time_mod.monotonic() < end:
            current = self.api.players(server_key=self.server_key)
            match = Finder(current).player(query)
            if match is not None and _player_key(match) not in seen:
                return match
            self._sleep(interval_s)
        raise TimeoutError(f"Timed out waiting for player to join: {query}")

    def player_leave(self, query: str | int, *, timeout_s: float = 60.0, interval_s: float | None = None):
        initial = Finder(self.api.players(server_key=self.server_key)).player(query)
        end = _deadline(timeout_s)
        while time_mod.monotonic() < end:
            if Finder(self.api.players(server_key=self.server_key)).player(query) is None:
                return initial
            self._sleep(interval_s)
        raise TimeoutError(f"Timed out waiting for player to leave: {query}")

    def staff_appears(self, query: str | int, *, timeout_s: float = 60.0, interval_s: float | None = None):
        end = _deadline(timeout_s)
        while time_mod.monotonic() < end:
            match = Finder(self.api.staff(server_key=self.server_key)).staff_member(query)
            if match is not None:
                return match
            self._sleep(interval_s)
        raise TimeoutError(f"Timed out waiting for staff member: {query}")

    def command_log(
        self,
        *,
        command_prefix: str | None = None,
        contains: str | None = None,
        player: str | int | None = None,
        timeout_s: float = 60.0,
        interval_s: float | None = None,
    ):
        end = _deadline(timeout_s)
        while time_mod.monotonic() < end:
            match = Finder(self.api.command_logs(server_key=self.server_key)).command_log(
                player=player,
                command_prefix=command_prefix,
                command_contains=contains,
            )
            if match is not None:
                return match
            self._sleep(interval_s)
        raise TimeoutError("Timed out waiting for command log")

    def queue_change(self, *, timeout_s: float = 60.0, interval_s: float | None = None) -> list[int]:
        previous = self.api.queue(server_key=self.server_key)
        end = _deadline(timeout_s)
        while time_mod.monotonic() < end:
            current = self.api.queue(server_key=self.server_key)
            if current != previous:
                return current
            self._sleep(interval_s)
        raise TimeoutError("Timed out waiting for queue change")


__all__ = ["AsyncWaiter", "Waiter"]
