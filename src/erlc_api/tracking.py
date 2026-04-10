from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, TYPE_CHECKING

from .context import ERLCContext
from .models import CommandLogEntry, Player, StaffMember, Vehicle, V2ServerBundle

if TYPE_CHECKING:
    from .client import ERLCClient

EventCallback = Callable[..., Any] | Callable[..., Awaitable[Any]]


def _player_key(player: Player) -> str:
    if player.user_id is not None:
        return f"id:{player.user_id}"
    return f"name:{(player.name or '').strip().lower()}"


def _staff_key(staff: StaffMember) -> str:
    if staff.callsign:
        return f"callsign:{staff.callsign.strip().lower()}"
    return f"name:{(staff.name or '').strip().lower()}"


@dataclass
class ServerState:
    players: list[Player] = field(default_factory=list)
    vehicles: list[Vehicle] = field(default_factory=list)
    staff: list[StaffMember] = field(default_factory=list)
    last_command_logs: list[CommandLogEntry] = field(default_factory=list)


class ServerTracker:
    def __init__(self, client: ERLCClient, ctx: ERLCContext, *, interval_s: float = 2.0) -> None:
        if interval_s <= 0:
            raise ValueError("interval_s must be greater than zero.")
        self._client = client
        self._ctx = ctx
        self._interval_s = interval_s
        self._state = ServerState()
        self._callbacks: dict[str, list[EventCallback]] = {}
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._seen_command_keys: set[tuple[int | None, str | None, str | None]] = set()

    @property
    def state(self) -> ServerState:
        return self._state

    @property
    def players(self) -> list[Player]:
        return self._state.players

    @property
    def vehicles(self) -> list[Vehicle]:
        return self._state.vehicles

    @property
    def staff(self) -> list[StaffMember]:
        return self._state.staff

    def on(self, event: str, callback: EventCallback) -> ServerTracker:
        self._callbacks.setdefault(event, []).append(callback)
        return self

    async def _emit(self, event: str, *args: Any) -> None:
        callbacks = self._callbacks.get(event, [])
        for callback in callbacks:
            result = callback(*args)
            if asyncio.iscoroutine(result):
                await result

    async def _poll_once(self) -> V2ServerBundle:
        return await self._client.v2.server_typed(
            self._ctx,
            players=True,
            staff=True,
            vehicles=True,
            command_logs=True,
        )

    async def _run(self) -> None:
        while self._running:
            bundle = await self._poll_once()
            await self._apply_bundle(bundle)
            await asyncio.sleep(self._interval_s)

    async def _apply_bundle(self, bundle: V2ServerBundle) -> None:
        new_players = bundle.players or []
        new_staff = bundle.staff or []
        new_vehicles = bundle.vehicles or []
        new_command_logs = bundle.command_logs or []

        previous_players = {_player_key(player): player for player in self._state.players}
        next_players = {_player_key(player): player for player in new_players}
        for key, player in next_players.items():
            if key not in previous_players:
                await self._emit("player_join", player)
        for key, player in previous_players.items():
            if key not in next_players:
                await self._emit("player_leave", player)

        previous_staff = {_staff_key(member): member for member in self._state.staff}
        next_staff = {_staff_key(member): member for member in new_staff}
        for key, member in next_staff.items():
            if key not in previous_staff:
                await self._emit("staff_join", member)
        for key, member in previous_staff.items():
            if key not in next_staff:
                await self._emit("staff_leave", member)

        for entry in new_command_logs:
            key = (entry.timestamp, entry.player, entry.command)
            if key in self._seen_command_keys:
                continue
            self._seen_command_keys.add(key)
            await self._emit("command_executed", entry)

        self._state = ServerState(
            players=new_players,
            vehicles=new_vehicles,
            staff=new_staff,
            last_command_logs=new_command_logs,
        )
        await self._emit("snapshot", self._state)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def __aenter__(self) -> ServerTracker:
        await self.start()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.stop()


__all__ = [
    "ServerState",
    "ServerTracker",
]
