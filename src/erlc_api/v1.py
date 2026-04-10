# src/erlc_api/v1.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import time
from typing import Any, AsyncIterator, Awaitable, Callable, Mapping

from .commands import BuiltCommand, infer_command_success, validate_command_syntax
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


@dataclass(frozen=True)
class CommandHistoryEntry:
    command: str
    sent_at_epoch: float
    inferred_success: bool | None
    message: str | None
    dry_run: bool


@dataclass(frozen=True)
class CommandExecutionResult:
    command: str
    response: CommandResponse
    inferred_success: bool | None
    correlated_log_entry: CommandLogEntry | None
    timed_out_waiting_for_log: bool


@dataclass
class V1:
    _request: RequestFn
    _command_history: list[CommandHistoryEntry] = field(default_factory=list)

    @staticmethod
    def _normalize_command(command: str | BuiltCommand) -> str:
        if isinstance(command, BuiltCommand):
            return str(command).strip()
        if not isinstance(command, str):
            raise TypeError("command must be a string or BuiltCommand.")
        return command.strip()

    @staticmethod
    def _reject_log_command(command: str) -> None:
        lowered = command.lower()
        if lowered == ":log" or (lowered.startswith(":log") and len(lowered) > 4 and lowered[4].isspace()):
            raise ValueError("The :log command is not supported by this wrapper.")

    def command_history(self, *, limit: int | None = None) -> list[CommandHistoryEntry]:
        if limit is None:
            return list(self._command_history)
        take = max(0, limit)
        return list(self._command_history[-take:])

    async def command(self, ctx: ERLCContext, command: str | BuiltCommand, *, dry_run: bool = False) -> Any:
        command_text = self._normalize_command(command)
        validate_command_syntax(command_text)
        self._reject_log_command(command_text)

        if dry_run:
            payload = {
                "Success": True,
                "Message": "Dry-run validation passed. Command not sent.",
                "DryRun": True,
                "Command": command_text,
            }
        else:
            payload = await self._request(
                ctx,
                "POST",
                "/v1/server/command",
                path_template="/v1/server/command",
                json={"command": command_text},
                idempotent=False,
            )

        decoded = decode_command_response(payload, endpoint="/v1/server/command")
        self._command_history.append(
            CommandHistoryEntry(
                command=command_text,
                sent_at_epoch=time.time(),
                inferred_success=infer_command_success(success=decoded.success, message=decoded.message),
                message=decoded.message,
                dry_run=dry_run,
            )
        )
        return payload

    async def send_command(self, ctx: ERLCContext, command: str | BuiltCommand, *, dry_run: bool = False) -> Any:
        if dry_run:
            return await self.command(ctx, command, dry_run=True)
        return await self.command(ctx, command)

    async def command_typed(self, ctx: ERLCContext, command: str | BuiltCommand, *, dry_run: bool = False) -> CommandResponse:
        if dry_run:
            payload = await self.command(ctx, command, dry_run=True)
        else:
            payload = await self.command(ctx, command)
        return decode_command_response(payload, endpoint="/v1/server/command")

    async def command_with_tracking(
        self,
        ctx: ERLCContext,
        command: str | BuiltCommand,
        *,
        dry_run: bool = False,
        wait_for_log: bool = True,
        timeout_s: float = 8.0,
        poll_interval_s: float = 1.0,
    ) -> CommandExecutionResult:
        if timeout_s <= 0:
            raise ValueError("timeout_s must be greater than zero.")
        if poll_interval_s <= 0:
            raise ValueError("poll_interval_s must be greater than zero.")

        command_text = self._normalize_command(command)
        sent_at_epoch = time.time()
        response = await self.command_typed(ctx, command_text, dry_run=dry_run)
        inferred = infer_command_success(success=response.success, message=response.message)

        matched: CommandLogEntry | None = None
        timed_out = False

        if wait_for_log and not dry_run:
            deadline = time.time() + timeout_s
            min_timestamp = int(sent_at_epoch) - 1
            lowered = command_text.lower()

            while time.time() < deadline:
                entries = await self.command_logs_typed(ctx)
                candidates = [
                    entry
                    for entry in entries
                    if entry.command is not None
                    and entry.timestamp is not None
                    and entry.timestamp >= min_timestamp
                    and entry.command.strip().lower() == lowered
                ]
                if candidates:
                    matched = max(candidates, key=lambda item: item.timestamp or 0)
                    break
                await asyncio.sleep(poll_interval_s)
            else:
                timed_out = True

        return CommandExecutionResult(
            command=command_text,
            response=response,
            inferred_success=inferred,
            correlated_log_entry=matched,
            timed_out_waiting_for_log=timed_out,
        )

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

    @staticmethod
    def _log_entry_key(entry: Mapping[str, Any], *, command_field: str | None = None) -> tuple[Any, ...]:
        if command_field is None:
            return (entry.get("Timestamp"), entry.get("Player"), entry.get("Reason"), entry.get("Weapon"))
        return (entry.get("Timestamp"), entry.get("Player"), entry.get(command_field))

    async def _stream_typed_logs(
        self,
        fetch: Callable[[ERLCContext], Awaitable[list[Any]]],
        ctx: ERLCContext,
        *,
        since_timestamp: int | None,
        poll_interval_s: float,
        key_builder: Callable[[Any], tuple[Any, ...]],
    ) -> AsyncIterator[Any]:
        if poll_interval_s <= 0:
            raise ValueError("poll_interval_s must be greater than zero.")

        last_timestamp = since_timestamp
        seen: set[tuple[Any, ...]] = set()

        while True:
            entries = await fetch(ctx)
            for entry in sorted(entries, key=lambda item: item.timestamp or 0):
                ts = entry.timestamp
                if ts is None:
                    continue
                if last_timestamp is not None and ts < last_timestamp:
                    continue
                key = key_builder(entry)
                if key in seen:
                    continue
                seen.add(key)
                if last_timestamp is None or ts > last_timestamp:
                    last_timestamp = ts
                yield entry
            await asyncio.sleep(poll_interval_s)

    async def command_logs_stream(
        self,
        ctx: ERLCContext,
        *,
        since_timestamp: int | None = None,
        poll_interval_s: float = 2.0,
    ) -> AsyncIterator[CommandLogEntry]:
        async for entry in self._stream_typed_logs(
            self.command_logs_typed,
            ctx,
            since_timestamp=since_timestamp,
            poll_interval_s=poll_interval_s,
            key_builder=lambda item: (item.timestamp, item.player, item.command),
        ):
            yield entry

    async def join_logs_stream(
        self,
        ctx: ERLCContext,
        *,
        since_timestamp: int | None = None,
        poll_interval_s: float = 2.0,
    ) -> AsyncIterator[JoinLogEntry]:
        async for entry in self._stream_typed_logs(
            self.join_logs_typed,
            ctx,
            since_timestamp=since_timestamp,
            poll_interval_s=poll_interval_s,
            key_builder=lambda item: (item.timestamp, item.player),
        ):
            yield entry

    async def kill_logs_stream(
        self,
        ctx: ERLCContext,
        *,
        since_timestamp: int | None = None,
        poll_interval_s: float = 2.0,
    ) -> AsyncIterator[KillLogEntry]:
        async for entry in self._stream_typed_logs(
            self.kill_logs_typed,
            ctx,
            since_timestamp=since_timestamp,
            poll_interval_s=poll_interval_s,
            key_builder=lambda item: (item.timestamp, item.killer, item.victim, item.weapon),
        ):
            yield entry
