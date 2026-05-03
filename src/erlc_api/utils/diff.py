from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ..models import Player, ServerBundle, StaffList, StaffMember


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().lower()
    return text or None


def _player_key(player: Player) -> str | None:
    if player.user_id is not None:
        return f"id:{player.user_id}"
    name = _normalize_text(player.name)
    return f"name:{name}" if name else None


def _staff_members(staff: StaffList | Iterable[StaffMember]) -> list[StaffMember]:
    if isinstance(staff, StaffList):
        return staff.members
    return list(staff)


def _staff_key(staff: StaffMember) -> str | None:
    if staff.user_id is not None:
        return f"id:{staff.user_id}"
    name = _normalize_text(staff.name)
    role = _normalize_text(staff.role)
    if name and role:
        return f"{role}:{name}"
    if name:
        return f"name:{name}"
    return None


def _index(items: Iterable[object], key_fn: object) -> dict[str, object]:
    out: dict[str, object] = {}
    for item in items:
        key = key_fn(item)  # type: ignore[misc]
        if key is not None:
            out[key] = item
    return out


@dataclass(frozen=True)
class PlayerDiff:
    joined: list[Player] = field(default_factory=list)
    left: list[Player] = field(default_factory=list)
    stayed: list[Player] = field(default_factory=list)
    previous_count: int = 0
    current_count: int = 0


@dataclass(frozen=True)
class StaffDiff:
    added: list[StaffMember] = field(default_factory=list)
    removed: list[StaffMember] = field(default_factory=list)
    unchanged: list[StaffMember] = field(default_factory=list)
    previous_count: int = 0
    current_count: int = 0


@dataclass(frozen=True)
class QueueMove:
    item: int
    from_position: int | None
    to_position: int | None


@dataclass(frozen=True)
class QueueDiff:
    joined: list[int] = field(default_factory=list)
    left: list[int] = field(default_factory=list)
    moved: list[QueueMove] = field(default_factory=list)
    unchanged: list[int] = field(default_factory=list)
    previous_count: int = 0
    current_count: int = 0


@dataclass(frozen=True)
class ServerDefaultDiff:
    players: PlayerDiff | None
    queue: QueueDiff | None
    staff: StaffDiff | None


def diff_players(previous: list[Player], current: list[Player]) -> PlayerDiff:
    previous_by_key = _index(previous, _player_key)
    current_by_key = _index(current, _player_key)
    previous_keys = set(previous_by_key)
    current_keys = set(current_by_key)
    joined_keys = current_keys - previous_keys
    left_keys = previous_keys - current_keys
    stayed_keys = current_keys & previous_keys
    return PlayerDiff(
        joined=[item for item in current if _player_key(item) in joined_keys],
        left=[item for item in previous if _player_key(item) in left_keys],
        stayed=[item for item in current if _player_key(item) in stayed_keys],
        previous_count=len(previous),
        current_count=len(current),
    )


def diff_staff(previous: StaffList | Iterable[StaffMember], current: StaffList | Iterable[StaffMember]) -> StaffDiff:
    previous_members = _staff_members(previous)
    current_members = _staff_members(current)
    previous_by_key = _index(previous_members, _staff_key)
    current_by_key = _index(current_members, _staff_key)
    previous_keys = set(previous_by_key)
    current_keys = set(current_by_key)
    added_keys = current_keys - previous_keys
    removed_keys = previous_keys - current_keys
    unchanged_keys = current_keys & previous_keys
    return StaffDiff(
        added=[item for item in current_members if _staff_key(item) in added_keys],
        removed=[item for item in previous_members if _staff_key(item) in removed_keys],
        unchanged=[item for item in current_members if _staff_key(item) in unchanged_keys],
        previous_count=len(previous_members),
        current_count=len(current_members),
    )


def diff_queue(previous: list[int], current: list[int]) -> QueueDiff:
    previous_set = set(previous)
    current_set = set(current)
    joined = [item for item in current if item not in previous_set]
    left = [item for item in previous if item not in current_set]
    unchanged = [item for item in current if item in previous_set]
    moved: list[QueueMove] = []
    for item in unchanged:
        from_position = previous.index(item) + 1
        to_position = current.index(item) + 1
        if from_position != to_position:
            moved.append(QueueMove(item=item, from_position=from_position, to_position=to_position))
    return QueueDiff(
        joined=joined,
        left=left,
        moved=moved,
        unchanged=unchanged,
        previous_count=len(previous),
        current_count=len(current),
    )


def diff_server_default(previous: ServerBundle, current: ServerBundle) -> ServerDefaultDiff:
    players_diff = None
    queue_diff = None
    staff_diff = None
    if previous.players is not None or current.players is not None:
        players_diff = diff_players(previous.players or [], current.players or [])
    if previous.queue is not None or current.queue is not None:
        queue_diff = diff_queue(previous.queue or [], current.queue or [])
    if previous.staff is not None or current.staff is not None:
        staff_diff = diff_staff(previous.staff or StaffList(), current.staff or StaffList())
    return ServerDefaultDiff(players=players_diff, queue=queue_diff, staff=staff_diff)


__all__ = [
    "PlayerDiff",
    "QueueDiff",
    "QueueMove",
    "ServerDefaultDiff",
    "StaffDiff",
    "diff_players",
    "diff_queue",
    "diff_server_default",
    "diff_staff",
]
