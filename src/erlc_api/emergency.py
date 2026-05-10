from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
from typing import Any, Iterable

from . import _utility as u
from .models import EmergencyCall, Player, PlayerLocation


@dataclass(frozen=True)
class EmergencyCallSummary:
    total: int
    by_team: dict[str, int]
    unresponded: int
    active: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "by_team": self.by_team,
            "unresponded": self.unresponded,
            "active": self.active,
        }


def _point(value: Any) -> tuple[float, float] | None:
    if isinstance(value, Player):
        return _point(value.location)
    if isinstance(value, PlayerLocation):
        if value.location_x is None or value.location_z is None:
            return None
        return (float(value.location_x), float(value.location_z))
    if isinstance(value, EmergencyCall):
        if len(value.position) >= 2:
            return (float(value.position[0]), float(value.position[-1]))
        return None
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return (float(value[0]), float(value[-1]))
        except (TypeError, ValueError):
            return None
    return None


def distance(a: Any, b: Any) -> float | None:
    first = _point(a)
    second = _point(b)
    if first is None or second is None:
        return None
    return math.dist(first, second)


class EmergencyCallTools:
    def __init__(self, data: Any) -> None:
        self.calls = u.emergency_calls(data)

    def all(self) -> list[EmergencyCall]:
        return list(self.calls)

    def active(self) -> list[EmergencyCall]:
        return [call for call in self.calls if call.started_at is not None]

    def unresponded(self) -> list[EmergencyCall]:
        return [call for call in self.calls if not call.players]

    def by_team(self, team: str) -> list[EmergencyCall]:
        return [call for call in self.calls if u.equals(call.team, team)]

    def nearest_to(self, player_or_location: Any) -> EmergencyCall | None:
        ranked = [
            (dist, call)
            for call in self.calls
            if (dist := distance(call, player_or_location)) is not None
        ]
        ranked.sort(key=lambda item: item[0])
        return ranked[0][1] if ranked else None

    def nearest_players_to_call(self, call: EmergencyCall, players: Iterable[Player], *, limit: int = 1) -> list[Player]:
        ranked = [
            (dist, player)
            for player in players
            if (dist := distance(call, player)) is not None
        ]
        ranked.sort(key=lambda item: item[0])
        return [player for _, player in ranked[:limit]]

    def summary(self) -> EmergencyCallSummary:
        by_team = Counter(call.team or "Unknown" for call in self.calls)
        return EmergencyCallSummary(
            total=len(self.calls),
            by_team=dict(by_team),
            unresponded=len(self.unresponded()),
            active=len(self.active()),
        )


__all__ = ["EmergencyCallSummary", "EmergencyCallTools", "distance"]
