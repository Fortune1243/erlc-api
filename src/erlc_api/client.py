from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import os
from typing import Any, Iterable, Mapping

from ._constants import BASE_URL
from ._errors import APIError, AuthError, NetworkError, RateLimitError
from ._http import AsyncTransport, ClientSettings, SyncTransport
from .commands import Command, CommandPolicy, CommandPreview, normalize_command, preview_command as _preview_command
from .models import (
    BanList,
    CommandLogEntry,
    CommandResult,
    EmergencyCall,
    JoinLogEntry,
    KillLogEntry,
    ModCallEntry,
    Player,
    ServerBundle,
    ServerLogs,
    StaffList,
    Vehicle,
    decode_bans,
    decode_command_logs,
    decode_command_result,
    decode_emergency_calls,
    decode_join_logs,
    decode_kill_logs,
    decode_mod_calls,
    decode_players,
    decode_queue,
    decode_server_bundle,
    decode_server_logs,
    decode_staff,
    decode_vehicles,
)


class ValidationStatus(StrEnum):
    OK = "ok"
    AUTH_ERROR = "auth_error"
    RATE_LIMITED = "rate_limited"
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"


@dataclass(frozen=True)
class ValidationResult:
    status: ValidationStatus
    retry_after: float | None = None
    api_status: int | None = None


_V2_INCLUDE_PARAMS = {
    "players": "Players",
    "staff": "Staff",
    "join_logs": "JoinLogs",
    "queue": "Queue",
    "kill_logs": "KillLogs",
    "command_logs": "CommandLogs",
    "mod_calls": "ModCalls",
    "emergency_calls": "EmergencyCalls",
    "vehicles": "Vehicles",
}

_LOG_KIND_ALIASES = {
    "join": "join_logs",
    "joins": "join_logs",
    "join_log": "join_logs",
    "join_logs": "join_logs",
    "kill": "kill_logs",
    "kills": "kill_logs",
    "kill_log": "kill_logs",
    "kill_logs": "kill_logs",
    "command": "command_logs",
    "commands": "command_logs",
    "cmd": "command_logs",
    "cmds": "command_logs",
    "command_log": "command_logs",
    "command_logs": "command_logs",
    "mod": "mod_calls",
    "mods": "mod_calls",
    "mod_call": "mod_calls",
    "mod_calls": "mod_calls",
    "all": "all",
    "logs": "all",
    "server_logs": "all",
}


def _settings(
    *,
    base_url: str,
    timeout_s: float,
    retry_429: bool,
    user_agent: str | None,
) -> ClientSettings:
    settings = ClientSettings(base_url=base_url, timeout_s=timeout_s, retry_429=retry_429)
    if user_agent is not None:
        settings.user_agent = user_agent
    return settings


def _default_key(default: str | None, override: str | None) -> str:
    key = (override if override is not None else default) or ""
    key = key.strip()
    if not key:
        raise ValueError("A server key is required. Pass it to the client or as server_key=...")
    return key


def _env_keys(
    *,
    server_key: str | None,
    global_key: str | None,
    server_key_var: str,
    global_key_var: str,
) -> tuple[str, str | None]:
    resolved_server_key = server_key if server_key is not None else os.environ.get(server_key_var)
    key = (resolved_server_key or "").strip()
    if not key:
        raise ValueError(f"A server key is required. Set {server_key_var} or pass server_key=...")

    resolved_global_key = global_key if global_key is not None else os.environ.get(global_key_var)
    global_text = (resolved_global_key or "").strip()
    return key, global_text or None


def _names(value: Iterable[str] | str | None) -> list[str]:
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value)


def _bundle_kwargs(
    request: str | Iterable[str] | Any | None,
    *,
    include: Iterable[str] | str | None,
    exclude: Iterable[str] | str | None,
) -> dict[str, bool]:
    from .bundle import resolve_request

    bundle_request = resolve_request(request)
    include_names = _names(include)
    exclude_names = _names(exclude)
    if include_names:
        bundle_request = bundle_request.include(*include_names)
    if exclude_names:
        bundle_request = bundle_request.exclude(*exclude_names)
    return bundle_request.server_kwargs()


def _log_kind(kind: str) -> str:
    key = kind.strip().lower().replace("-", "_")
    try:
        return _LOG_KIND_ALIASES[key]
    except KeyError as exc:
        raise ValueError(f"Unknown log kind: {kind}") from exc


def _command_text(command: str | Command, policy: CommandPolicy | None) -> str:
    return policy.validate(command) if policy is not None else normalize_command(command)


def _include_params(
    *,
    include: Iterable[str] | str | None,
    all: bool,
    players: bool,
    staff: bool,
    join_logs: bool,
    queue: bool,
    kill_logs: bool,
    command_logs: bool,
    mod_calls: bool,
    emergency_calls: bool,
    vehicles: bool,
) -> dict[str, str]:
    selected = {
        "players": players,
        "staff": staff,
        "join_logs": join_logs,
        "queue": queue,
        "kill_logs": kill_logs,
        "command_logs": command_logs,
        "mod_calls": mod_calls,
        "emergency_calls": emergency_calls,
        "vehicles": vehicles,
    }
    if all:
        selected = {key: True for key in selected}
    if include is not None:
        names = [include] if isinstance(include, str) else list(include)
        for name in names:
            key = name.strip().lower().replace("-", "_")
            if key == "all":
                selected = {item: True for item in selected}
                continue
            if key not in selected:
                raise ValueError(f"Unknown v2 include: {name}")
            selected[key] = True
    return {param: "true" for key, param in _V2_INCLUDE_PARAMS.items() if selected[key]}


def _configure_async_rate_limiter(transport: AsyncTransport, enabled: bool) -> None:
    if not enabled:
        return
    if getattr(transport, "rate_limiter", None) is None:
        from .ratelimit import AsyncRateLimiter

        transport.rate_limiter = AsyncRateLimiter()


def _configure_sync_rate_limiter(transport: SyncTransport, enabled: bool) -> None:
    if not enabled:
        return
    if getattr(transport, "rate_limiter", None) is None:
        from .ratelimit import RateLimiter

        transport.rate_limiter = RateLimiter()


class AsyncERLC:
    """Async, flat, v2-first PRC API wrapper."""

    def __init__(
        self,
        server_key: str | None = None,
        *,
        global_key: str | None = None,
        base_url: str = BASE_URL,
        timeout_s: float = 20.0,
        retry_429: bool = True,
        rate_limited: bool = True,
        user_agent: str | None = None,
        transport: AsyncTransport | None = None,
    ) -> None:
        self.server_key = server_key.strip() if isinstance(server_key, str) else server_key
        self.global_key = global_key.strip() if isinstance(global_key, str) else global_key
        self.settings = _settings(base_url=base_url, timeout_s=timeout_s, retry_429=retry_429, user_agent=user_agent)
        self._transport = transport or AsyncTransport(self.settings, global_key=self.global_key)
        self.rate_limited = rate_limited
        _configure_async_rate_limiter(self._transport, rate_limited)

    @classmethod
    def from_env(
        cls,
        *,
        server_key: str | None = None,
        global_key: str | None = None,
        server_key_var: str = "ERLC_SERVER_KEY",
        global_key_var: str = "ERLC_GLOBAL_KEY",
        **kwargs: Any,
    ) -> AsyncERLC:
        resolved_server_key, resolved_global_key = _env_keys(
            server_key=server_key,
            global_key=global_key,
            server_key_var=server_key_var,
            global_key_var=global_key_var,
        )
        return cls(resolved_server_key, global_key=resolved_global_key, **kwargs)

    @property
    def rate_limits(self) -> Any:
        limiter = getattr(self._transport, "rate_limiter", None)
        return limiter.snapshot() if limiter is not None else None

    async def start(self) -> None:
        await self._transport.start()

    async def close(self) -> None:
        await self._transport.close()

    async def __aenter__(self) -> AsyncERLC:
        await self.start()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.close()

    async def request(
        self,
        method: str,
        path: str,
        *,
        server_key: str | None = None,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self._transport.request(
            server_key=_default_key(self.server_key, server_key),
            method=method,
            path=path,
            params=params,
            json=json,
            headers=headers,
        )

    async def server(
        self,
        *,
        server_key: str | None = None,
        raw: bool = False,
        include: Iterable[str] | str | None = None,
        all: bool = False,
        players: bool = False,
        staff: bool = False,
        join_logs: bool = False,
        queue: bool = False,
        kill_logs: bool = False,
        command_logs: bool = False,
        mod_calls: bool = False,
        emergency_calls: bool = False,
        vehicles: bool = False,
    ) -> Any | ServerBundle:
        payload = await self.request(
            "GET",
            "/v2/server",
            server_key=server_key,
            params=_include_params(
                include=include,
                all=all,
                players=players,
                staff=staff,
                join_logs=join_logs,
                queue=queue,
                kill_logs=kill_logs,
                command_logs=command_logs,
                mod_calls=mod_calls,
                emergency_calls=emergency_calls,
                vehicles=vehicles,
            ),
        )
        return payload if raw else decode_server_bundle(payload)

    async def players(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[Player]:
        payload = await self.server(server_key=server_key, raw=True, players=True)
        return payload["Players"] if raw else decode_players(payload.get("Players", []))

    async def staff(self, *, server_key: str | None = None, raw: bool = False) -> Any | StaffList:
        payload = await self.server(server_key=server_key, raw=True, staff=True)
        return payload["Staff"] if raw else decode_staff(payload.get("Staff", {}))

    async def queue(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[int]:
        payload = await self.server(server_key=server_key, raw=True, queue=True)
        return payload["Queue"] if raw else decode_queue(payload.get("Queue", []))

    async def join_logs(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[JoinLogEntry]:
        payload = await self.server(server_key=server_key, raw=True, join_logs=True)
        return payload["JoinLogs"] if raw else decode_join_logs(payload.get("JoinLogs", []))

    async def kill_logs(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[KillLogEntry]:
        payload = await self.server(server_key=server_key, raw=True, kill_logs=True)
        return payload["KillLogs"] if raw else decode_kill_logs(payload.get("KillLogs", []))

    async def command_logs(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[CommandLogEntry]:
        payload = await self.server(server_key=server_key, raw=True, command_logs=True)
        return payload["CommandLogs"] if raw else decode_command_logs(payload.get("CommandLogs", []))

    async def mod_calls(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[ModCallEntry]:
        payload = await self.server(server_key=server_key, raw=True, mod_calls=True)
        return payload["ModCalls"] if raw else decode_mod_calls(payload.get("ModCalls", []))

    async def emergency_calls(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[EmergencyCall]:
        payload = await self.server(server_key=server_key, raw=True, emergency_calls=True)
        return payload["EmergencyCalls"] if raw else decode_emergency_calls(payload.get("EmergencyCalls", []))

    async def vehicles(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[Vehicle]:
        payload = await self.server(server_key=server_key, raw=True, vehicles=True)
        return payload["Vehicles"] if raw else decode_vehicles(payload.get("Vehicles", []))

    async def bundle(
        self,
        request: str | Iterable[str] | Any | None = None,
        *,
        include: Iterable[str] | str | None = None,
        exclude: Iterable[str] | str | None = None,
        server_key: str | None = None,
        raw: bool = False,
    ) -> Any | ServerBundle:
        return await self.server(
            server_key=server_key,
            raw=raw,
            **_bundle_kwargs(request, include=include, exclude=exclude),
        )

    async def logs(self, kind: str, *, server_key: str | None = None, raw: bool = False) -> Any | ServerLogs | list[Any]:
        resolved = _log_kind(kind)
        if resolved == "join_logs":
            return await self.join_logs(server_key=server_key, raw=raw)
        if resolved == "kill_logs":
            return await self.kill_logs(server_key=server_key, raw=raw)
        if resolved == "command_logs":
            return await self.command_logs(server_key=server_key, raw=raw)
        if resolved == "mod_calls":
            return await self.mod_calls(server_key=server_key, raw=raw)

        payload = await self.server(
            server_key=server_key,
            raw=True,
            join_logs=True,
            kill_logs=True,
            command_logs=True,
            mod_calls=True,
        )
        return payload if raw else decode_server_logs(payload)

    async def bans(self, *, server_key: str | None = None, raw: bool = False) -> Any | BanList:
        payload = await self.request("GET", "/v1/server/bans", server_key=server_key)
        return payload if raw else decode_bans(payload)

    async def preview_command(self, command: str | Command, *, policy: CommandPolicy | None = None) -> CommandPreview:
        return _preview_command(command, policy=policy)

    async def command(
        self,
        command: str | Command,
        *,
        server_key: str | None = None,
        raw: bool = False,
        dry_run: bool = False,
        policy: CommandPolicy | None = None,
    ) -> Any | CommandResult:
        command_text = _command_text(command, policy)
        if dry_run:
            payload = {"message": "Dry-run validation passed. Command not sent.", "success": True, "command": command_text}
            return payload if raw else decode_command_result(payload)
        payload = await self.request(
            "POST",
            "/v2/server/command",
            server_key=server_key,
            json={"command": command_text},
        )
        return payload if raw else decode_command_result(payload)

    async def validate_key(self, *, server_key: str | None = None) -> ValidationResult:
        try:
            await self.server(server_key=server_key, raw=True)
            return ValidationResult(status=ValidationStatus.OK)
        except AuthError:
            return ValidationResult(status=ValidationStatus.AUTH_ERROR)
        except RateLimitError as exc:
            return ValidationResult(status=ValidationStatus.RATE_LIMITED, retry_after=exc.retry_after)
        except NetworkError:
            return ValidationResult(status=ValidationStatus.NETWORK_ERROR)
        except APIError as exc:
            return ValidationResult(status=ValidationStatus.API_ERROR, api_status=exc.status)

    async def health_check(self, *, server_key: str | None = None) -> ValidationResult:
        return await self.validate_key(server_key=server_key)


class ERLC:
    """Sync, flat, v2-first PRC API wrapper for scripts."""

    def __init__(
        self,
        server_key: str | None = None,
        *,
        global_key: str | None = None,
        base_url: str = BASE_URL,
        timeout_s: float = 20.0,
        retry_429: bool = True,
        rate_limited: bool = True,
        user_agent: str | None = None,
        transport: SyncTransport | None = None,
    ) -> None:
        self.server_key = server_key.strip() if isinstance(server_key, str) else server_key
        self.global_key = global_key.strip() if isinstance(global_key, str) else global_key
        self.settings = _settings(base_url=base_url, timeout_s=timeout_s, retry_429=retry_429, user_agent=user_agent)
        self._transport = transport or SyncTransport(self.settings, global_key=self.global_key)
        self.rate_limited = rate_limited
        _configure_sync_rate_limiter(self._transport, rate_limited)

    @classmethod
    def from_env(
        cls,
        *,
        server_key: str | None = None,
        global_key: str | None = None,
        server_key_var: str = "ERLC_SERVER_KEY",
        global_key_var: str = "ERLC_GLOBAL_KEY",
        **kwargs: Any,
    ) -> ERLC:
        resolved_server_key, resolved_global_key = _env_keys(
            server_key=server_key,
            global_key=global_key,
            server_key_var=server_key_var,
            global_key_var=global_key_var,
        )
        return cls(resolved_server_key, global_key=resolved_global_key, **kwargs)

    @property
    def rate_limits(self) -> Any:
        limiter = getattr(self._transport, "rate_limiter", None)
        return limiter.snapshot() if limiter is not None else None

    def start(self) -> None:
        self._transport.start()

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> ERLC:
        self.start()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        server_key: str | None = None,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return self._transport.request(
            server_key=_default_key(self.server_key, server_key),
            method=method,
            path=path,
            params=params,
            json=json,
            headers=headers,
        )

    def server(
        self,
        *,
        server_key: str | None = None,
        raw: bool = False,
        include: Iterable[str] | str | None = None,
        all: bool = False,
        players: bool = False,
        staff: bool = False,
        join_logs: bool = False,
        queue: bool = False,
        kill_logs: bool = False,
        command_logs: bool = False,
        mod_calls: bool = False,
        emergency_calls: bool = False,
        vehicles: bool = False,
    ) -> Any | ServerBundle:
        payload = self.request(
            "GET",
            "/v2/server",
            server_key=server_key,
            params=_include_params(
                include=include,
                all=all,
                players=players,
                staff=staff,
                join_logs=join_logs,
                queue=queue,
                kill_logs=kill_logs,
                command_logs=command_logs,
                mod_calls=mod_calls,
                emergency_calls=emergency_calls,
                vehicles=vehicles,
            ),
        )
        return payload if raw else decode_server_bundle(payload)

    def players(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[Player]:
        payload = self.server(server_key=server_key, raw=True, players=True)
        return payload["Players"] if raw else decode_players(payload.get("Players", []))

    def staff(self, *, server_key: str | None = None, raw: bool = False) -> Any | StaffList:
        payload = self.server(server_key=server_key, raw=True, staff=True)
        return payload["Staff"] if raw else decode_staff(payload.get("Staff", {}))

    def queue(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[int]:
        payload = self.server(server_key=server_key, raw=True, queue=True)
        return payload["Queue"] if raw else decode_queue(payload.get("Queue", []))

    def join_logs(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[JoinLogEntry]:
        payload = self.server(server_key=server_key, raw=True, join_logs=True)
        return payload["JoinLogs"] if raw else decode_join_logs(payload.get("JoinLogs", []))

    def kill_logs(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[KillLogEntry]:
        payload = self.server(server_key=server_key, raw=True, kill_logs=True)
        return payload["KillLogs"] if raw else decode_kill_logs(payload.get("KillLogs", []))

    def command_logs(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[CommandLogEntry]:
        payload = self.server(server_key=server_key, raw=True, command_logs=True)
        return payload["CommandLogs"] if raw else decode_command_logs(payload.get("CommandLogs", []))

    def mod_calls(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[ModCallEntry]:
        payload = self.server(server_key=server_key, raw=True, mod_calls=True)
        return payload["ModCalls"] if raw else decode_mod_calls(payload.get("ModCalls", []))

    def emergency_calls(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[EmergencyCall]:
        payload = self.server(server_key=server_key, raw=True, emergency_calls=True)
        return payload["EmergencyCalls"] if raw else decode_emergency_calls(payload.get("EmergencyCalls", []))

    def vehicles(self, *, server_key: str | None = None, raw: bool = False) -> Any | list[Vehicle]:
        payload = self.server(server_key=server_key, raw=True, vehicles=True)
        return payload["Vehicles"] if raw else decode_vehicles(payload.get("Vehicles", []))

    def bundle(
        self,
        request: str | Iterable[str] | Any | None = None,
        *,
        include: Iterable[str] | str | None = None,
        exclude: Iterable[str] | str | None = None,
        server_key: str | None = None,
        raw: bool = False,
    ) -> Any | ServerBundle:
        return self.server(
            server_key=server_key,
            raw=raw,
            **_bundle_kwargs(request, include=include, exclude=exclude),
        )

    def logs(self, kind: str, *, server_key: str | None = None, raw: bool = False) -> Any | ServerLogs | list[Any]:
        resolved = _log_kind(kind)
        if resolved == "join_logs":
            return self.join_logs(server_key=server_key, raw=raw)
        if resolved == "kill_logs":
            return self.kill_logs(server_key=server_key, raw=raw)
        if resolved == "command_logs":
            return self.command_logs(server_key=server_key, raw=raw)
        if resolved == "mod_calls":
            return self.mod_calls(server_key=server_key, raw=raw)

        payload = self.server(
            server_key=server_key,
            raw=True,
            join_logs=True,
            kill_logs=True,
            command_logs=True,
            mod_calls=True,
        )
        return payload if raw else decode_server_logs(payload)

    def bans(self, *, server_key: str | None = None, raw: bool = False) -> Any | BanList:
        payload = self.request("GET", "/v1/server/bans", server_key=server_key)
        return payload if raw else decode_bans(payload)

    def preview_command(self, command: str | Command, *, policy: CommandPolicy | None = None) -> CommandPreview:
        return _preview_command(command, policy=policy)

    def command(
        self,
        command: str | Command,
        *,
        server_key: str | None = None,
        raw: bool = False,
        dry_run: bool = False,
        policy: CommandPolicy | None = None,
    ) -> Any | CommandResult:
        command_text = _command_text(command, policy)
        if dry_run:
            payload = {"message": "Dry-run validation passed. Command not sent.", "success": True, "command": command_text}
            return payload if raw else decode_command_result(payload)
        payload = self.request(
            "POST",
            "/v2/server/command",
            server_key=server_key,
            json={"command": command_text},
        )
        return payload if raw else decode_command_result(payload)

    def validate_key(self, *, server_key: str | None = None) -> ValidationResult:
        try:
            self.server(server_key=server_key, raw=True)
            return ValidationResult(status=ValidationStatus.OK)
        except AuthError:
            return ValidationResult(status=ValidationStatus.AUTH_ERROR)
        except RateLimitError as exc:
            return ValidationResult(status=ValidationStatus.RATE_LIMITED, retry_after=exc.retry_after)
        except NetworkError:
            return ValidationResult(status=ValidationStatus.NETWORK_ERROR)
        except APIError as exc:
            return ValidationResult(status=ValidationStatus.API_ERROR, api_status=exc.status)

    def health_check(self, *, server_key: str | None = None) -> ValidationResult:
        return self.validate_key(server_key=server_key)


Client = ERLC
AsyncClient = AsyncERLC


__all__ = [
    "AsyncClient",
    "AsyncERLC",
    "Client",
    "ERLC",
    "ValidationResult",
    "ValidationStatus",
]
