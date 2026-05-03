from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from . import _utility as u


KeyFn = Callable[[Any], Any]


@dataclass(frozen=True)
class CollectionDiff:
    added: list[Any] = field(default_factory=list)
    removed: list[Any] = field(default_factory=list)
    unchanged: list[Any] = field(default_factory=list)
    previous_count: int = 0
    current_count: int = 0

    @property
    def changed(self) -> bool:
        return bool(self.added or self.removed)


@dataclass(frozen=True)
class BundleDiff:
    players: CollectionDiff
    queue: CollectionDiff
    staff: CollectionDiff
    vehicles: CollectionDiff
    command_logs: CollectionDiff
    mod_calls: CollectionDiff
    emergency_calls: CollectionDiff

    @property
    def changed(self) -> bool:
        return any(
            section.changed
            for section in (
                self.players,
                self.queue,
                self.staff,
                self.vehicles,
                self.command_logs,
                self.mod_calls,
                self.emergency_calls,
            )
        )


def _key(item: Any) -> Any:
    for field_name in ("user_id", "player_id", "plate", "call_number"):
        value = u.get_value(item, field_name)
        if value is not None:
            return (field_name, value)
    timestamp = u.timestamp_of(item)
    if timestamp is not None:
        return (
            "timestamp",
            timestamp,
            u.get_value(item, "player"),
            u.get_value(item, "command"),
            u.get_value(item, "caller"),
        )
    return repr(u.model_dict(item))


def _diff(previous: list[Any], current: list[Any], key_fn: KeyFn = _key) -> CollectionDiff:
    previous_by_key = {key_fn(item): item for item in previous}
    current_by_key = {key_fn(item): item for item in current}
    previous_keys = set(previous_by_key)
    current_keys = set(current_by_key)
    return CollectionDiff(
        added=[item for item in current if key_fn(item) in current_keys - previous_keys],
        removed=[item for item in previous if key_fn(item) in previous_keys - current_keys],
        unchanged=[item for item in current if key_fn(item) in current_keys & previous_keys],
        previous_count=len(previous),
        current_count=len(current),
    )


class Differ:
    """Diff two bundles or two model collections."""

    def __init__(self, previous: Any, current: Any) -> None:
        self.previous = previous
        self.current = current

    def collection(self, *, key: KeyFn = _key) -> CollectionDiff:
        return _diff(u.rows(self.previous), u.rows(self.current), key)

    def players(self) -> CollectionDiff:
        return _diff(u.players(self.previous), u.players(self.current), lambda item: item.user_id or item.name)

    def queue(self) -> CollectionDiff:
        return _diff(u.queue(self.previous), u.queue(self.current), lambda item: item)

    def staff(self) -> CollectionDiff:
        return _diff(u.staff(self.previous), u.staff(self.current), lambda item: item.user_id or (item.role, item.name))

    def vehicles(self) -> CollectionDiff:
        return _diff(u.vehicles(self.previous), u.vehicles(self.current), lambda item: item.plate or (item.owner, item.name))

    def command_logs(self) -> CollectionDiff:
        return _diff(u.command_logs(self.previous), u.command_logs(self.current))

    def mod_calls(self) -> CollectionDiff:
        return _diff(u.mod_calls(self.previous), u.mod_calls(self.current))

    def emergency_calls(self) -> CollectionDiff:
        return _diff(u.emergency_calls(self.previous), u.emergency_calls(self.current))

    def bundle(self) -> BundleDiff:
        return BundleDiff(
            players=self.players(),
            queue=self.queue(),
            staff=self.staff(),
            vehicles=self.vehicles(),
            command_logs=self.command_logs(),
            mod_calls=self.mod_calls(),
            emergency_calls=self.emergency_calls(),
        )


__all__ = ["BundleDiff", "CollectionDiff", "Differ"]
