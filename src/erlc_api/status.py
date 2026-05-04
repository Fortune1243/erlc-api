from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any

from . import _utility as u
from .bundle import BundleRequest


@dataclass(frozen=True)
class StatusIssue:
    severity: str
    message: str
    code: str | None = None
    advice: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "message": self.message,
            "code": self.code,
            "advice": self.advice,
        }


@dataclass(frozen=True)
class ServerStatus:
    server_name: str | None = None
    current_players: int | None = None
    max_players: int | None = None
    player_count: int = 0
    queue_count: int = 0
    staff_count: int = 0
    vehicle_count: int = 0
    emergency_call_count: int = 0
    health: str = "ok"
    issues: list[StatusIssue] = field(default_factory=list)
    generated_at: float = field(default_factory=time.time)
    raw: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_name": self.server_name,
            "current_players": self.current_players,
            "max_players": self.max_players,
            "player_count": self.player_count,
            "queue_count": self.queue_count,
            "staff_count": self.staff_count,
            "vehicle_count": self.vehicle_count,
            "emergency_call_count": self.emergency_call_count,
            "health": self.health,
            "issues": [issue.to_dict() for issue in self.issues],
            "generated_at": self.generated_at,
            "raw": u.model_dict(self.raw),
        }


def _health(issues: list[StatusIssue]) -> str:
    severities = {issue.severity for issue in issues}
    if "critical" in severities or "error" in severities:
        return "error"
    if "warning" in severities:
        return "warning"
    if "info" in severities:
        return "info"
    return "ok"


class StatusBuilder:
    def __init__(self, data: Any) -> None:
        self.data = data

    def build(self) -> ServerStatus:
        players = u.players(self.data)
        queue = u.queue(self.data)
        staff = u.staff(self.data)
        vehicles = u.vehicles(self.data)
        calls = u.emergency_calls(self.data)
        current_players = getattr(self.data, "current_players", None)
        max_players = getattr(self.data, "max_players", None)
        player_count = len(players) if players else int(current_players or 0)

        issues: list[StatusIssue] = []
        if current_players is not None and max_players and current_players >= max_players:
            issues.append(StatusIssue("warning", "Server is full.", code="server_full", advice="Expect queue growth."))
        elif current_players is not None and max_players and current_players / max_players >= 0.9:
            issues.append(StatusIssue("info", "Server is close to full.", code="server_near_full"))
        if queue:
            severity = "warning" if len(queue) >= 10 else "info"
            issues.append(StatusIssue(severity, f"Queue has {len(queue)} waiting player(s).", code="queue_active"))
        if player_count > 0 and not staff:
            issues.append(StatusIssue("warning", "No staff detected while players are online.", code="no_staff"))
        if calls:
            issues.append(StatusIssue("info", f"{len(calls)} emergency call(s) active.", code="emergency_calls"))

        return ServerStatus(
            server_name=getattr(self.data, "name", None),
            current_players=current_players,
            max_players=max_players,
            player_count=player_count,
            queue_count=len(queue),
            staff_count=len(staff),
            vehicle_count=len(vehicles),
            emergency_call_count=len(calls),
            health=_health(issues),
            issues=issues,
            raw=self.data,
        )


class AsyncStatus:
    def __init__(self, api: Any, *, server_key: str | None = None) -> None:
        self.api = api
        self.server_key = server_key

    async def get(self, *, server_key: str | None = None, preset: str | BundleRequest = "dashboard") -> ServerStatus:
        request = BundleRequest.preset(preset) if isinstance(preset, str) else preset
        bundle = await self.api.server(server_key=server_key or self.server_key, **request.server_kwargs())
        return StatusBuilder(bundle).build()

    async def __call__(self, **kwargs: Any) -> ServerStatus:
        return await self.get(**kwargs)


class Status:
    def __init__(self, api: Any, *, server_key: str | None = None) -> None:
        self.api = api
        self.server_key = server_key

    def get(self, *, server_key: str | None = None, preset: str | BundleRequest = "dashboard") -> ServerStatus:
        request = BundleRequest.preset(preset) if isinstance(preset, str) else preset
        bundle = self.api.server(server_key=server_key or self.server_key, **request.server_kwargs())
        return StatusBuilder(bundle).build()

    def __call__(self, **kwargs: Any) -> ServerStatus:
        return self.get(**kwargs)


__all__ = [
    "AsyncStatus",
    "ServerStatus",
    "Status",
    "StatusBuilder",
    "StatusIssue",
]
