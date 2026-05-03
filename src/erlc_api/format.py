from __future__ import annotations

from typing import Any

from . import _utility as u
from .models import CommandResult, ServerBundle


class Formatter:
    """Compact text formatter for Discord, console, and logs."""

    def __init__(self, *, max_length: int | None = None) -> None:
        self.max_length = max_length

    def _clip(self, text: str) -> str:
        if self.max_length is None or len(text) <= self.max_length:
            return text
        return f"{text[: self.max_length - 3]}..."

    def player(self, player: Any) -> str:
        name = u.get_value(player, "name", u.get_value(player, "player", "unknown"))
        user_id = u.get_value(player, "user_id")
        team = u.get_value(player, "team")
        bits = [str(name)]
        if user_id is not None:
            bits.append(f"({user_id})")
        if team:
            bits.append(f"- {team}")
        return self._clip(" ".join(bits))

    def players(self, players: Any) -> str:
        items = u.players(players) or u.rows(players)
        if not items:
            return "No players"
        return self._clip("\n".join(self.player(item) for item in items))

    def queue(self, queue: Any) -> str:
        items = u.queue(queue)
        if not items:
            return "Queue is empty"
        return self._clip("\n".join(f"{index}. {user_id}" for index, user_id in enumerate(items, start=1)))

    def server(self, bundle: ServerBundle) -> str:
        count = bundle.current_players
        max_players = bundle.max_players
        suffix = f"{count}/{max_players}" if count is not None and max_players is not None else "unknown players"
        return self._clip(f"{bundle.name or 'Unnamed server'} - {suffix}")

    def logs(self, logs: Any) -> str:
        items = u.rows(logs)
        if not items:
            return "No logs"
        lines = []
        for item in items:
            ts = u.timestamp_of(item)
            actor = u.get_value(item, "name", u.get_value(item, "player", u.get_value(item, "caller", "")))
            command = u.get_value(item, "command", "")
            lines.append(" ".join(str(part) for part in (ts, actor, command) if part not in (None, "")))
        return self._clip("\n".join(lines))

    def vehicles(self, vehicles: Any) -> str:
        items = u.vehicles(vehicles) or u.rows(vehicles)
        if not items:
            return "No vehicles"
        return self._clip("\n".join(f"{u.get_value(item, 'name')} - {u.get_value(item, 'owner')}" for item in items))

    def staff(self, staff: Any) -> str:
        items = u.staff(staff)
        if not items:
            return "No staff"
        return self._clip("\n".join(f"{item.role}: {item.name or item.user_id}" for item in items))

    def error(self, error: Exception) -> str:
        return self._clip(str(error))

    def command_result(self, result: CommandResult) -> str:
        status = "ok" if result.success is True else "failed" if result.success is False else "unknown"
        return self._clip(f"{status}: {result.message or ''}".strip())

    def discord(self, value: Any) -> str:
        text = value if isinstance(value, str) else str(value)
        return self._clip(text.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere"))

    def rich_table(self, items: Any):
        try:
            from rich.table import Table
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("Rich formatting requires `pip install erlc-api.py[rich]`.") from exc

        rows = [u.model_dict(item) for item in u.rows(items)]
        table = Table()
        columns = sorted({key for row in rows if isinstance(row, dict) for key in row})
        for column in columns:
            table.add_column(str(column))
        for row in rows:
            table.add_row(*[str(row.get(column, "")) if isinstance(row, dict) else str(row) for column in columns])
        return table


__all__ = ["Formatter"]
