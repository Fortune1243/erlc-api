from __future__ import annotations

from typing import Any, Callable

from . import _utility as u


Predicate = Callable[[Any], bool]


class Filter:
    """Chainable list filter."""

    def __init__(self, items: Any, predicates: list[Predicate] | None = None) -> None:
        self._items = u.rows(items)
        self._predicates = list(predicates or [])

    def _where(self, predicate: Predicate) -> Filter:
        return Filter(self._items, [*self._predicates, predicate])

    def team(self, value: str) -> Filter:
        return self._where(lambda item: u.equals(u.get_value(item, "team"), value))

    def permission(self, value: str) -> Filter:
        return self._where(lambda item: u.equals(u.get_value(item, "permission", u.get_value(item, "role")), value))

    def role(self, value: str) -> Filter:
        return self._where(lambda item: u.equals(u.get_value(item, "role"), value))

    def name_contains(self, value: str) -> Filter:
        return self._where(lambda item: u.contains(u.get_value(item, "name", u.get_value(item, "player")), value))

    def after(self, timestamp: int) -> Filter:
        return self._where(lambda item: (u.timestamp_of(item) or -1) >= timestamp)

    def before(self, timestamp: int) -> Filter:
        return self._where(lambda item: (u.timestamp_of(item) or 10**20) <= timestamp)

    def command(self, *, prefix: str | None = None, contains: str | None = None, name: str | None = None) -> Filter:
        return self._where(
            lambda item: u.startswith(u.get_value(item, "command"), prefix)
            and u.contains(u.get_value(item, "command"), contains)
            and (name is None or u.command_name(u.get_value(item, "command")) == name.lower().lstrip(":"))
        )

    def vehicle_owner(self, owner: str) -> Filter:
        return self._where(lambda item: u.equals(u.get_value(item, "owner"), owner))

    def where(self, predicate: Predicate) -> Filter:
        return self._where(predicate)

    def all(self) -> list[Any]:
        out = self._items
        for predicate in self._predicates:
            out = [item for item in out if predicate(item)]
        return out

    def first(self) -> Any | None:
        items = self.all()
        return items[0] if items else None

    def count(self) -> int:
        return len(self.all())

    def group_by(self, field: str) -> dict[Any, list[Any]]:
        groups: dict[Any, list[Any]] = {}
        for item in self.all():
            key = u.get_value(item, field)
            groups.setdefault(key, []).append(item)
        return groups


__all__ = ["Filter"]
