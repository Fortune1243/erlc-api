# src/erlc_api/v1.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Mapping, Optional

from .context import ERLCContext

RequestFn = Callable[..., Awaitable[Any]]

@dataclass
class V1:
    _request: RequestFn

    async def command(self, ctx: ERLCContext, command: str) -> Any:
        return await self._request(
            ctx,
            "POST",
            "/v1/server/command",
            path_template="/v1/server/command",
            json={"command": command},
            idempotent=False,
        )

    async def server(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server",
            path_template="/v1/server",
        )

    async def players(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/players",
            path_template="/v1/server/players",
        )

    async def join_logs(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/joinlogs",
            path_template="/v1/server/joinlogs",
        )

    async def queue(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/queue",
            path_template="/v1/server/queue",
        )

    async def kill_logs(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/killlogs",
            path_template="/v1/server/killlogs",
        )

    async def command_logs(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/commandlogs",
            path_template="/v1/server/commandlogs",
        )

    async def mod_calls(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/modcalls",
            path_template="/v1/server/modcalls",
        )

    async def bans(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/bans",
            path_template="/v1/server/bans",
        )

    async def vehicles(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/vehicles",
            path_template="/v1/server/vehicles",
        )

    async def staff(self, ctx: ERLCContext) -> Any:
        return await self._request(
            ctx,
            "GET",
            "/v1/server/staff",
            path_template="/v1/server/staff",
        )
