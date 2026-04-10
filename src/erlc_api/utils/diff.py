from __future__ import annotations

from dataclasses import dataclass, field

from ..models import Player, QueueEntry, StaffMember, V2ServerBundle


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().lower()
    return text or None


def _player_key(player: Player) -> str | None:
    if player.user_id is not None:
        return f"id:{player.user_id}"
    normalized_name = _normalize_text(player.name)
    if normalized_name:
        return f"name:{normalized_name}"
    return None


def _staff_key(staff: StaffMember) -> str | None:
    normalized_callsign = _normalize_text(staff.callsign)
    if normalized_callsign:
        return f"callsign:{normalized_callsign}"
    normalized_name = _normalize_text(staff.name)
    if normalized_name:
        return f"name:{normalized_name}"
    return None


def _queue_key(entry: QueueEntry) -> str | None:
    normalized_player = _normalize_text(entry.player)
    if normalized_player:
        return f"player:{normalized_player}"
    if entry.position is not None:
        return f"position:{entry.position}"
    return None


def _index_by_key(items: list[object], key_fn: object) -> dict[str, object]:
    keyed: dict[str, object] = {}
    for item in items:
        key = key_fn(item)  # type: ignore[misc]
        if key is None:
            continue
        keyed[key] = item
    return keyed


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
    item: QueueEntry
    from_position: int | None
    to_position: int | None


@dataclass(frozen=True)
class QueueDiff:
    joined: list[QueueEntry] = field(default_factory=list)
    left: list[QueueEntry] = field(default_factory=list)
    moved: list[QueueMove] = field(default_factory=list)
    unchanged: list[QueueEntry] = field(default_factory=list)
    previous_count: int = 0
    current_count: int = 0


@dataclass(frozen=True)
class ServerDefaultDiff:
    players: PlayerDiff | None
    queue: QueueDiff | None
    staff: StaffDiff | None


def diff_players(previous: list[Player], current: list[Player]) -> PlayerDiff:
    previous_by_key = _index_by_key(previous, _player_key)
    current_by_key = _index_by_key(current, _player_key)

    previous_keys = set(previous_by_key.keys())
    current_keys = set(current_by_key.keys())

    joined_keys = current_keys - previous_keys
    left_keys = previous_keys - current_keys
    stayed_keys = current_keys & previous_keys

    joined = [player for player in current if _player_key(player) in joined_keys]
    left = [player for player in previous if _player_key(player) in left_keys]
    stayed = [player for player in current if _player_key(player) in stayed_keys]

    return PlayerDiff(
        joined=joined,
        left=left,
        stayed=stayed,
        previous_count=len(previous),
        current_count=len(current),
    )


def diff_staff(previous: list[StaffMember], current: list[StaffMember]) -> StaffDiff:
    previous_by_key = _index_by_key(previous, _staff_key)
    current_by_key = _index_by_key(current, _staff_key)

    previous_keys = set(previous_by_key.keys())
    current_keys = set(current_by_key.keys())

    added_keys = current_keys - previous_keys
    removed_keys = previous_keys - current_keys
    unchanged_keys = current_keys & previous_keys

    added = [item for item in current if _staff_key(item) in added_keys]
    removed = [item for item in previous if _staff_key(item) in removed_keys]
    unchanged = [item for item in current if _staff_key(item) in unchanged_keys]

    return StaffDiff(
        added=added,
        removed=removed,
        unchanged=unchanged,
        previous_count=len(previous),
        current_count=len(current),
    )


def diff_queue(previous: list[QueueEntry], current: list[QueueEntry]) -> QueueDiff:
    previous_by_key = _index_by_key(previous, _queue_key)
    current_by_key = _index_by_key(current, _queue_key)

    previous_keys = set(previous_by_key.keys())
    current_keys = set(current_by_key.keys())

    joined_keys = current_keys - previous_keys
    left_keys = previous_keys - current_keys
    overlap_keys = current_keys & previous_keys

    joined = [item for item in current if _queue_key(item) in joined_keys]
    left = [item for item in previous if _queue_key(item) in left_keys]

    moved: list[QueueMove] = []
    unchanged: list[QueueEntry] = []

    for key in overlap_keys:
        current_item = current_by_key[key]  # type: ignore[index]
        previous_item = previous_by_key[key]  # type: ignore[index]
        if (
            isinstance(current_item, QueueEntry)
            and isinstance(previous_item, QueueEntry)
            and current_item.position != previous_item.position
        ):
            moved.append(
                QueueMove(
                    item=current_item,
                    from_position=previous_item.position,
                    to_position=current_item.position,
                )
            )
            continue
        if isinstance(current_item, QueueEntry):
            unchanged.append(current_item)

    return QueueDiff(
        joined=joined,
        left=left,
        moved=moved,
        unchanged=unchanged,
        previous_count=len(previous),
        current_count=len(current),
    )


def diff_server_default(previous: V2ServerBundle, current: V2ServerBundle) -> ServerDefaultDiff:
    players_diff: PlayerDiff | None = None
    queue_diff: QueueDiff | None = None
    staff_diff: StaffDiff | None = None

    if previous.players is not None or current.players is not None:
        players_diff = diff_players(previous.players or [], current.players or [])

    if previous.queue is not None or current.queue is not None:
        queue_diff = diff_queue(previous.queue or [], current.queue or [])

    if previous.staff is not None or current.staff is not None:
        staff_diff = diff_staff(previous.staff or [], current.staff or [])

    return ServerDefaultDiff(players=players_diff, queue=queue_diff, staff=staff_diff)


__all__ = [
    "PlayerDiff",
    "StaffDiff",
    "QueueMove",
    "QueueDiff",
    "ServerDefaultDiff",
    "diff_players",
    "diff_queue",
    "diff_server_default",
    "diff_staff",
]
