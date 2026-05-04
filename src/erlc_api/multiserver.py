from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from . import _utility as u
from .bundle import BundleRequest, resolve_request
from .status import ServerStatus, StatusBuilder


READ_METHODS = frozenset(
    {
        "server",
        "players",
        "staff",
        "queue",
        "join_logs",
        "kill_logs",
        "command_logs",
        "mod_calls",
        "bans",
        "vehicles",
        "emergency_calls",
        "validate_key",
        "health_check",
    }
)


@dataclass(frozen=True)
class ServerRef:
    name: str
    server_key: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("server name cannot be blank.")
        if not self.server_key.strip():
            raise ValueError("server_key cannot be blank.")

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "server_key": "***", "metadata": dict(self.metadata)}


@dataclass(frozen=True)
class ServerResult:
    server: ServerRef
    value: Any = None
    error: Exception | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "server": self.server.to_dict(),
            "ok": self.ok,
            "value": u.model_dict(self.value) if self.error is None else None,
            "error": str(self.error) if self.error is not None else None,
        }


def _server_ref(value: Any) -> ServerRef:
    if isinstance(value, ServerRef):
        return value
    if isinstance(value, Mapping):
        return ServerRef(
            name=str(value.get("name")),
            server_key=str(value.get("server_key", value.get("key", ""))),
            metadata=value.get("metadata", {}),
        )
    if isinstance(value, tuple):
        if len(value) == 2:
            return ServerRef(name=str(value[0]), server_key=str(value[1]))
        if len(value) == 3:
            return ServerRef(name=str(value[0]), server_key=str(value[1]), metadata=value[2])
    raise TypeError("servers must be ServerRef objects, mappings, or (name, server_key[, metadata]) tuples.")


def _validate_concurrency(value: int) -> int:
    if isinstance(value, bool) or value <= 0:
        raise ValueError("concurrency must be a positive integer.")
    return int(value)


class AsyncMultiServer:
    def __init__(
        self,
        api: Any,
        servers: Iterable[ServerRef | tuple[Any, ...] | Mapping[str, Any]],
        *,
        concurrency: int = 5,
        raise_on_error: bool = False,
    ) -> None:
        self.api = api
        self.servers = [_server_ref(server) for server in servers]
        self.concurrency = _validate_concurrency(concurrency)
        self.raise_on_error = raise_on_error

    async def _run(self, server: ServerRef, func: Any) -> ServerResult:
        try:
            return ServerResult(server=server, value=await func(server))
        except Exception as exc:
            if self.raise_on_error:
                raise
            return ServerResult(server=server, error=exc)

    async def _map(self, func: Any) -> list[ServerResult]:
        semaphore = asyncio.Semaphore(self.concurrency)

        async def limited(server: ServerRef) -> ServerResult:
            async with semaphore:
                return await self._run(server, func)

        return await asyncio.gather(*(limited(server) for server in self.servers))

    async def server(self, *, preset: str | BundleRequest = "dashboard", raw: bool = False) -> list[ServerResult]:
        request = resolve_request(preset)
        return await self._map(lambda server: self.api.server(server_key=server.server_key, raw=raw, **request.server_kwargs()))

    async def players(self) -> list[ServerResult]:
        return await self.call("players")

    async def status(self, *, preset: str | BundleRequest = "dashboard") -> list[ServerResult]:
        request = resolve_request(preset)

        async def fetch(server: ServerRef) -> ServerStatus:
            bundle = await self.api.server(server_key=server.server_key, **request.server_kwargs())
            return StatusBuilder(bundle).build()

        return await self._map(fetch)

    async def aggregate(self) -> dict[str, Any]:
        results = await self.status()
        statuses = [result.value for result in results if result.ok]
        return {
            "servers": len(self.servers),
            "ok": sum(1 for result in results if result.ok),
            "errors": sum(1 for result in results if not result.ok),
            "players": sum(getattr(status, "player_count", 0) for status in statuses),
            "queue": sum(getattr(status, "queue_count", 0) for status in statuses),
            "staff": sum(getattr(status, "staff_count", 0) for status in statuses),
            "results": [result.to_dict() for result in results],
        }

    async def call(self, method_name: str, **kwargs: Any) -> list[ServerResult]:
        if method_name not in READ_METHODS:
            raise ValueError("MultiServer.call only supports read-only client methods.")
        method = getattr(self.api, method_name)
        return await self._map(lambda server: method(server_key=server.server_key, **kwargs))


class MultiServer:
    def __init__(
        self,
        api: Any,
        servers: Iterable[ServerRef | tuple[Any, ...] | Mapping[str, Any]],
        *,
        concurrency: int = 5,
        raise_on_error: bool = False,
    ) -> None:
        self.api = api
        self.servers = [_server_ref(server) for server in servers]
        self.concurrency = _validate_concurrency(concurrency)
        self.raise_on_error = raise_on_error

    def _run(self, server: ServerRef, func: Any) -> ServerResult:
        try:
            return ServerResult(server=server, value=func(server))
        except Exception as exc:
            if self.raise_on_error:
                raise
            return ServerResult(server=server, error=exc)

    def _map(self, func: Any) -> list[ServerResult]:
        if self.concurrency == 1:
            return [self._run(server, func) for server in self.servers]
        results: list[ServerResult | None] = [None] * len(self.servers)
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = {executor.submit(self._run, server, func): index for index, server in enumerate(self.servers)}
            for future in as_completed(futures):
                results[futures[future]] = future.result()
        return [result for result in results if result is not None]

    def server(self, *, preset: str | BundleRequest = "dashboard", raw: bool = False) -> list[ServerResult]:
        request = resolve_request(preset)
        return self._map(lambda server: self.api.server(server_key=server.server_key, raw=raw, **request.server_kwargs()))

    def players(self) -> list[ServerResult]:
        return self.call("players")

    def status(self, *, preset: str | BundleRequest = "dashboard") -> list[ServerResult]:
        request = resolve_request(preset)

        def fetch(server: ServerRef) -> ServerStatus:
            bundle = self.api.server(server_key=server.server_key, **request.server_kwargs())
            return StatusBuilder(bundle).build()

        return self._map(fetch)

    def aggregate(self) -> dict[str, Any]:
        results = self.status()
        statuses = [result.value for result in results if result.ok]
        return {
            "servers": len(self.servers),
            "ok": sum(1 for result in results if result.ok),
            "errors": sum(1 for result in results if not result.ok),
            "players": sum(getattr(status, "player_count", 0) for status in statuses),
            "queue": sum(getattr(status, "queue_count", 0) for status in statuses),
            "staff": sum(getattr(status, "staff_count", 0) for status in statuses),
            "results": [result.to_dict() for result in results],
        }

    def call(self, method_name: str, **kwargs: Any) -> list[ServerResult]:
        if method_name not in READ_METHODS:
            raise ValueError("MultiServer.call only supports read-only client methods.")
        method = getattr(self.api, method_name)
        return self._map(lambda server: method(server_key=server.server_key, **kwargs))


__all__ = [
    "AsyncMultiServer",
    "MultiServer",
    "READ_METHODS",
    "ServerRef",
    "ServerResult",
]
