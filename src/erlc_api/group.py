from __future__ import annotations

from typing import Any, Callable

from . import _utility as u


class Grouper:
    """Group model lists by common ER:LC fields."""

    def __init__(self, items: Any) -> None:
        self._items = u.rows(items)

    def by(self, key: str | Callable[[Any], Any]) -> dict[Any, list[Any]]:
        groups: dict[Any, list[Any]] = {}
        for item in self._items:
            value = key(item) if callable(key) else u.get_value(item, key)
            groups.setdefault(value, []).append(item)
        return groups

    def team(self) -> dict[Any, list[Any]]:
        return self.by("team")

    def permission(self) -> dict[Any, list[Any]]:
        return self.by(lambda item: u.get_value(item, "permission", u.get_value(item, "role")))

    def staff_role(self) -> dict[Any, list[Any]]:
        return self.by("role")

    def vehicle_owner(self) -> dict[Any, list[Any]]:
        return self.by("owner")

    def command_name(self) -> dict[Any, list[Any]]:
        return self.by(lambda item: u.command_name(u.get_value(item, "command")))

    def day(self) -> dict[str | None, list[Any]]:
        return self.by(lambda item: (u.datetime_from_timestamp(u.timestamp_of(item)) or None).date().isoformat() if u.timestamp_of(item) is not None else None)

    def hour(self) -> dict[str | None, list[Any]]:
        return self.by(lambda item: (u.datetime_from_timestamp(u.timestamp_of(item)) or None).strftime("%Y-%m-%d %H:00") if u.timestamp_of(item) is not None else None)

    def emergency_team(self) -> dict[Any, list[Any]]:
        return self.team()


__all__ = ["Grouper"]
