# src/erlc_api/v2.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from .context import ERLCContext
from .models import V2ServerBundle, decode_v2_server_bundle
from .validated import V2ServerBundleValidated, decode_v2_server_bundle_validated

RequestFn = Callable[..., Awaitable[Any]]


@dataclass
class V2ServerQuery:
    _api: "V2"
    _ctx: ERLCContext
    _flags: dict[str, bool] = field(default_factory=dict)

    def include_players(self) -> V2ServerQuery:
        """Include players in the next `/v2/server` request."""
        self._flags["players"] = True
        return self

    def include_staff(self) -> V2ServerQuery:
        """Include staff in the next `/v2/server` request."""
        self._flags["staff"] = True
        return self

    def include_helpers(self) -> V2ServerQuery:
        """Include helpers in the next `/v2/server` request."""
        self._flags["helpers"] = True
        return self

    def include_join_logs(self) -> V2ServerQuery:
        self._flags["join_logs"] = True
        return self

    def include_queue(self) -> V2ServerQuery:
        self._flags["queue"] = True
        return self

    def include_kill_logs(self) -> V2ServerQuery:
        self._flags["kill_logs"] = True
        return self

    def include_command_logs(self) -> V2ServerQuery:
        self._flags["command_logs"] = True
        return self

    def include_mod_calls(self) -> V2ServerQuery:
        self._flags["mod_calls"] = True
        return self

    def include_vehicles(self) -> V2ServerQuery:
        self._flags["vehicles"] = True
        return self

    def include_emergency_calls(self) -> V2ServerQuery:
        self._flags["emergency_calls"] = True
        return self

    def include_all(self) -> V2ServerQuery:
        return (
            self.include_players()
            .include_staff()
            .include_helpers()
            .include_join_logs()
            .include_queue()
            .include_kill_logs()
            .include_command_logs()
            .include_mod_calls()
            .include_vehicles()
            .include_emergency_calls()
        )

    async def fetch(self) -> Any:
        """Execute request with the currently selected include flags (raw mode)."""
        return await self._api.server(self._ctx, **self._flags)

    async def fetch_typed(self) -> V2ServerBundle:
        """Execute request and decode as typed dataclass bundle."""
        payload = await self.fetch()
        return decode_v2_server_bundle(payload, endpoint="/v2/server")

    async def fetch_validated(self, *, strict: bool = False) -> V2ServerBundleValidated:
        """Execute request and validate payload with optional Pydantic strictness."""
        payload = await self.fetch()
        return decode_v2_server_bundle_validated(payload, strict=strict)


@dataclass
class V2:
    _request: RequestFn

    def server_query(self, ctx: ERLCContext) -> V2ServerQuery:
        """Start a fluent include-builder for `/v2/server` requests."""
        return V2ServerQuery(_api=self, _ctx=ctx)

    async def server(
        self,
        ctx: ERLCContext,
        *,
        players: bool = False,
        staff: bool = False,
        helpers: bool = False,
        join_logs: bool = False,
        queue: bool = False,
        kill_logs: bool = False,
        command_logs: bool = False,
        mod_calls: bool = False,
        vehicles: bool = False,
        emergency_calls: bool = False,
    ) -> Any:
        params = {
            "Players": str(players).lower(),
            "Staff": str(staff).lower(),
            "Helpers": str(helpers).lower(),
            "JoinLogs": str(join_logs).lower(),
            "Queue": str(queue).lower(),
            "KillLogs": str(kill_logs).lower(),
            "CommandLogs": str(command_logs).lower(),
            "ModCalls": str(mod_calls).lower(),
            "Vehicles": str(vehicles).lower(),
            "EmergencyCalls": str(emergency_calls).lower(),
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
        helpers: bool = False,
        join_logs: bool = False,
        queue: bool = False,
        kill_logs: bool = False,
        command_logs: bool = False,
        mod_calls: bool = False,
        vehicles: bool = False,
        emergency_calls: bool = False,
    ) -> V2ServerBundle:
        payload = await self.server(
            ctx,
            players=players,
            staff=staff,
            helpers=helpers,
            join_logs=join_logs,
            queue=queue,
            kill_logs=kill_logs,
            command_logs=command_logs,
            mod_calls=mod_calls,
            vehicles=vehicles,
            emergency_calls=emergency_calls,
        )
        return decode_v2_server_bundle(payload, endpoint="/v2/server")

    async def server_validated(
        self,
        ctx: ERLCContext,
        *,
        strict: bool = False,
        players: bool = False,
        staff: bool = False,
        helpers: bool = False,
        join_logs: bool = False,
        queue: bool = False,
        kill_logs: bool = False,
        command_logs: bool = False,
        mod_calls: bool = False,
        vehicles: bool = False,
        emergency_calls: bool = False,
    ) -> V2ServerBundleValidated:
        """Fetch `/v2/server` and validate response via optional Pydantic models."""
        payload = await self.server(
            ctx,
            players=players,
            staff=staff,
            helpers=helpers,
            join_logs=join_logs,
            queue=queue,
            kill_logs=kill_logs,
            command_logs=command_logs,
            mod_calls=mod_calls,
            vehicles=vehicles,
            emergency_calls=emergency_calls,
        )
        return decode_v2_server_bundle_validated(payload, strict=strict)

    async def server_all(self, ctx: ERLCContext) -> Any:
        return await self.server(
            ctx,
            players=True,
            staff=True,
            helpers=True,
            join_logs=True,
            queue=True,
            kill_logs=True,
            command_logs=True,
            mod_calls=True,
            vehicles=True,
            emergency_calls=True,
        )

    async def server_all_typed(self, ctx: ERLCContext) -> V2ServerBundle:
        payload = await self.server_all(ctx)
        return decode_v2_server_bundle(payload, endpoint="/v2/server")

    async def server_all_validated(self, ctx: ERLCContext, *, strict: bool = False) -> V2ServerBundleValidated:
        """Fetch full `/v2/server` bundle and validate via Pydantic models."""
        payload = await self.server_all(ctx)
        return decode_v2_server_bundle_validated(payload, strict=strict)

    async def server_default(self, ctx: ERLCContext) -> Any:
        return await self.server(ctx, players=True, queue=True, staff=True)

    async def server_default_typed(self, ctx: ERLCContext) -> V2ServerBundle:
        payload = await self.server_default(ctx)
        return decode_v2_server_bundle(payload, endpoint="/v2/server")

    async def server_default_validated(self, ctx: ERLCContext, *, strict: bool = False) -> V2ServerBundleValidated:
        """Fetch default `/v2/server` subset and validate via Pydantic models."""
        payload = await self.server_default(ctx)
        return decode_v2_server_bundle_validated(payload, strict=strict)
