# src/erlc_api/v1.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from .context import ERLCContext
from .models import (
    BanEntry,
    CommandLogEntry,
    CommandResponse,
    JoinLogEntry,
    KillLogEntry,
    ModCallEntry,
    Player,
    QueueEntry,
    ServerInfo,
    StaffMember,
    Vehicle,
    decode_bans,
    decode_command_logs,
    decode_command_response,
    decode_join_logs,
    decode_kill_logs,
    decode_mod_calls,
    decode_players,
    decode_queue,
    decode_server_info,
    decode_staff,
    decode_vehicles,
)

RequestFn = Callable[..., Awaitable[Any]]

@dataclass
class V1:
    _request: RequestFn

    async def command(self, ctx: ERLCContext, command: str) -> Any:
        stripped = command.lstrip()
        lowered = stripped.lower()
        if lowered == ":log" or (lowered.startswith(":log") and len(lowered) > 4 and lowered[4].isspace()):
            raise ValueError("The :log command is not supported by this wrapper.")

        return await self._request(
            ctx,
            "POST",
            "/v1/server/command",
            path_template="/v1/server/command",
            json={"command": command},
            idempotent=False,
        )

    async def command_typed(self, ctx: ERLCContext, command: str) -> CommandResponse:
        payload = await self.command(ctx, command)
        return decode_command_response(payload, endpoint="/v1/server/command")

    async def server(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server",
            path_template="/v1/server",
        )

    async def server_typed(self, ctx: ERLCContext) -> ServerInfo:
        payload = await self.server(ctx)
        return decode_server_info(payload, endpoint="/v1/server")

    async def players(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/players",
            path_template="/v1/server/players",
        )

    async def players_typed(self, ctx: ERLCContext) -> list[Player]:
        payload = await self.players(ctx)
        return decode_players(payload, endpoint="/v1/server/players")

    async def join_logs(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/joinlogs",
            path_template="/v1/server/joinlogs",
        )

    async def join_logs_typed(self, ctx: ERLCContext) -> list[JoinLogEntry]:
        payload = await self.join_logs(ctx)
        return decode_join_logs(payload, endpoint="/v1/server/joinlogs")

    async def queue(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/queue",
            path_template="/v1/server/queue",
        )

    async def queue_typed(self, ctx: ERLCContext) -> list[QueueEntry]:
        payload = await self.queue(ctx)
        return decode_queue(payload, endpoint="/v1/server/queue")

    async def kill_logs(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/killlogs",
            path_template="/v1/server/killlogs",
        )

    async def kill_logs_typed(self, ctx: ERLCContext) -> list[KillLogEntry]:
        payload = await self.kill_logs(ctx)
        return decode_kill_logs(payload, endpoint="/v1/server/killlogs")

    async def command_logs(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/commandlogs",
            path_template="/v1/server/commandlogs",
        )

    async def command_logs_typed(self, ctx: ERLCContext) -> list[CommandLogEntry]:
        payload = await self.command_logs(ctx)
        return decode_command_logs(payload, endpoint="/v1/server/commandlogs")

    async def mod_calls(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/modcalls",
            path_template="/v1/server/modcalls",
        )

    async def mod_calls_typed(self, ctx: ERLCContext) -> list[ModCallEntry]:
        payload = await self.mod_calls(ctx)
        return decode_mod_calls(payload, endpoint="/v1/server/modcalls")

    async def bans(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/bans",
            path_template="/v1/server/bans",
        )

    async def bans_typed(self, ctx: ERLCContext) -> list[BanEntry]:
        payload = await self.bans(ctx)
        return decode_bans(payload, endpoint="/v1/server/bans")

    async def vehicles(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/vehicles",
            path_template="/v1/server/vehicles",
        )

    async def vehicles_typed(self, ctx: ERLCContext) -> list[Vehicle]:
        payload = await self.vehicles(ctx)
        return decode_vehicles(payload, endpoint="/v1/server/vehicles")

    async def staff(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/staff",
            path_template="/v1/server/staff",
        )

    async def staff_typed(self, ctx: ERLCContext) -> list[StaffMember]:
        payload = await self.staff(ctx)
        return decode_staff(payload, endpoint="/v1/server/staff")
