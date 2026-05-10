from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from . import _utility as u


@dataclass(frozen=True)
class DashboardSummary:
    player_count: int = 0
    queue_count: int = 0
    staff_count: int = 0
    vehicle_count: int = 0
    emergency_call_count: int = 0
    players_by_team: dict[str, int] = field(default_factory=dict)
    staff_by_role: dict[str, int] = field(default_factory=dict)
    vehicles_by_owner: dict[str, int] = field(default_factory=dict)


class Analyzer:
    """Small analytics helper for bundles and logs."""

    def __init__(self, data: Any) -> None:
        self.data = data

    def dashboard(self) -> DashboardSummary:
        players = u.players(self.data)
        staff = u.staff(self.data)
        vehicles = u.vehicles(self.data)
        return DashboardSummary(
            player_count=len(players),
            queue_count=len(u.queue(self.data)),
            staff_count=len(staff),
            vehicle_count=len(vehicles),
            emergency_call_count=len(u.emergency_calls(self.data)),
            players_by_team=self.team_distribution(),
            staff_by_role=dict(Counter(member.role or "unknown" for member in staff)),
            vehicles_by_owner=dict(Counter(vehicle.owner or "unknown" for vehicle in vehicles)),
        )

    def team_distribution(self) -> dict[str, int]:
        return dict(Counter(player.team or "unknown" for player in u.players(self.data)))

    def command_usage(self) -> dict[str, int]:
        return dict(Counter(u.command_name(entry.command) or "unknown" for entry in u.command_logs(self.data)))

    def command_categories(self) -> dict[str, int]:
        from .commands import get_command_metadata

        counter: Counter[str] = Counter()
        for entry in u.command_logs(self.data):
            metadata = get_command_metadata(entry.command or "") if entry.command else None
            counter[metadata.category if metadata else "unknown"] += 1
        return dict(counter)

    def staff_activity(self) -> dict[str, int]:
        counter: Counter[str] = Counter()
        for entry in u.command_logs(self.data):
            counter[entry.name or entry.player or "unknown"] += 1
        for entry in u.mod_calls(self.data):
            counter[entry.moderator_name or entry.moderator or "unknown"] += 1
        return dict(counter)

    def moderation_trends(self) -> dict[str, int]:
        counter: Counter[str] = Counter()
        for entry in u.command_logs(self.data):
            name = u.command_name(entry.command)
            if name in {"warn", "ban", "kick", "mod", "pm"}:
                counter[name] += 1
        counter["mod_calls"] += len(u.mod_calls(self.data))
        return dict(counter)

    def peak_counts(self, snapshots: list[Any] | None = None) -> dict[str, int]:
        items = snapshots if snapshots is not None else u.server_bundles(self.data)
        player_counts = [len(u.players(item)) for item in items]
        queue_counts = [len(u.queue(item)) for item in items]
        return {
            "players": max(player_counts, default=len(u.players(self.data))),
            "queue": max(queue_counts, default=len(u.queue(self.data))),
        }


__all__ = ["Analyzer", "DashboardSummary"]
