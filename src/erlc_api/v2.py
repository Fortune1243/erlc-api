# src/erlc_api/v2.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from .context import ERLCContext
from .models import V2ServerBundle, decode_v2_server_bundle

RequestFn = Callable[..., Awaitable[Any]]

@dataclass
class V2:
    _request: RequestFn

    async def server(
        self,
        ctx: ERLCContext,
        *,
        players: bool = False,
        staff: bool = False,
        join_logs: bool = False,
        queue: bool = False,
        kill_logs: bool = False,
        command_logs: bool = False,
        mod_calls: bool = False,
        vehicles: bool = False,
    ) -> Any:
        params = {
            "Players": str(players).lower(),
            "Staff": str(staff).lower(),
            "JoinLogs": str(join_logs).lower(),
            "Queue": str(queue).lower(),
            "KillLogs": str(kill_logs).lower(),
            "CommandLogs": str(command_logs).lower(),
            "ModCalls": str(mod_calls).lower(),
            "Vehicles": str(vehicles).lower(),
        }
        return await self._request(
            ctx,
            "GET",
            "/v2/server",
            path_template="/v2/server",
            params=params,
        )

    async def server_typed(
        self,
        ctx: ERLCContext,
        *,
        players: bool = False,
        staff: bool = False,
        join_logs: bool = False,
        queue: bool = False,
        kill_logs: bool = False,
        command_logs: bool = False,
        mod_calls: bool = False,
        vehicles: bool = False,
    ) -> V2ServerBundle:
        payload = await self.server(
            ctx,
            players=players,
            staff=staff,
            join_logs=join_logs,
            queue=queue,
            kill_logs=kill_logs,
            command_logs=command_logs,
            mod_calls=mod_calls,
            vehicles=vehicles,
        )
        return decode_v2_server_bundle(payload, endpoint="/v2/server")

    async def server_all(self, ctx: ERLCContext) -> Any:
        return await self.server(
            ctx,
            players=True,
            staff=True,
            join_logs=True,
            queue=True,
            kill_logs=True,
            command_logs=True,
            mod_calls=True,
            vehicles=True,
        )

    async def server_all_typed(self, ctx: ERLCContext) -> V2ServerBundle:
        payload = await self.server_all(ctx)
        return decode_v2_server_bundle(payload, endpoint="/v2/server")

    async def server_default(self, ctx: ERLCContext) -> Any:
        return await self.server(ctx, players=True, queue=True, staff=True)

    async def server_default_typed(self, ctx: ERLCContext) -> V2ServerBundle:
        payload = await self.server_default(ctx)
        return decode_v2_server_bundle(payload, endpoint="/v2/server")
