from __future__ import annotations

from typing import Any, Callable

from . import _utility as u


class Sorter:
    """Chainable sorter for model lists."""

    def __init__(self, items: Any, key: Callable[[Any], Any] | None = None, reverse: bool = False) -> None:
        self._items = u.rows(items)
        self._key = key
        self._reverse = reverse

    def by(self, field: str, *, reverse: bool = False) -> Sorter:
        return Sorter(self._items, lambda item: u.get_value(item, field) or "", reverse)

    def name(self, *, reverse: bool = False) -> Sorter:
        return Sorter(self._items, lambda item: u.normalize_text(u.get_value(item, "name", u.get_value(item, "player"))), reverse)

    def timestamp(self, *, reverse: bool = False) -> Sorter:
        return Sorter(self._items, lambda item: u.timestamp_of(item) or 0, reverse)

    def newest(self) -> Sorter:
        return self.timestamp(reverse=True)

    def oldest(self) -> Sorter:
        return self.timestamp(reverse=False)

    def team(self, *, reverse: bool = False) -> Sorter:
        return self.by("team", reverse=reverse)

    def permission(self, *, reverse: bool = False) -> Sorter:
        return Sorter(self._items, lambda item: u.get_value(item, "permission", u.get_value(item, "role")) or "", reverse)

    def wanted_stars(self, *, reverse: bool = True) -> Sorter:
        return Sorter(self._items, lambda item: u.get_value(item, "wanted_stars") or 0, reverse)

    def vehicle_owner(self, *, reverse: bool = False) -> Sorter:
        return self.by("owner", reverse=reverse)

    def vehicle_model(self, *, reverse: bool = False) -> Sorter:
        return self.by("name", reverse=reverse)

    def queue_position(self, *, reverse: bool = False) -> Sorter:
        return Sorter(self._items, lambda item: self._items.index(item), reverse)

    def all(self) -> list[Any]:
        if self._key is None:
            return list(self._items)
        return sorted(self._items, key=self._key, reverse=self._reverse)

    def first(self) -> Any | None:
        items = self.all()
        return items[0] if items else None


__all__ = ["Sorter"]
