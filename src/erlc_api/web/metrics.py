from __future__ import annotations

from dataclasses import dataclass, field

from ..models import Player, ServerBundle, StaffList, StaffMember, Vehicle


def _increment(bucket: dict[str, int], key: str | None) -> None:
    label = (key or "unknown").strip() or "unknown"
    bucket[label] = bucket.get(label, 0) + 1


def count_players_by_team(players: list[Player]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for player in players:
        _increment(counts, player.team)
    return counts


def _staff_members(staff: StaffList | list[StaffMember]) -> list[StaffMember]:
    return staff.members if isinstance(staff, StaffList) else staff


def count_staff_by_permission(staff_members: StaffList | list[StaffMember]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for member in _staff_members(staff_members):
        _increment(counts, member.role)
    return counts


def count_vehicles_by_team(vehicles: list[Vehicle]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for vehicle in vehicles:
        _increment(counts, vehicle.team)
    return counts


@dataclass(frozen=True)
class DashboardMetrics:
    player_count: int
    queue_count: int
    staff_count: int
    vehicle_count: int
    players_by_team: dict[str, int] = field(default_factory=dict)
    staff_by_permission: dict[str, int] = field(default_factory=dict)
    vehicles_by_team: dict[str, int] = field(default_factory=dict)


def compute_dashboard_metrics(bundle: ServerBundle) -> DashboardMetrics:
    players = bundle.players or []
    queue = bundle.queue or []
    staff = bundle.staff or StaffList()
    staff_members = staff.members
    vehicles = bundle.vehicles or []
    return DashboardMetrics(
        player_count=len(players),
        queue_count=len(queue),
        staff_count=len(staff_members),
        vehicle_count=len(vehicles),
        players_by_team=count_players_by_team(players),
        staff_by_permission=count_staff_by_permission(staff_members),
        vehicles_by_team=count_vehicles_by_team(vehicles),
    )


__all__ = [
    "DashboardMetrics",
    "compute_dashboard_metrics",
    "count_players_by_team",
    "count_staff_by_permission",
    "count_vehicles_by_team",
]
