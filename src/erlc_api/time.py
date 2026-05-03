from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass(frozen=True)
class TimeWindow:
    start: int
    end: int

    def contains(self, timestamp: int | None) -> bool:
        return timestamp is not None and self.start <= timestamp <= self.end


class TimeTools:
    """Timestamp parsing and display helpers."""

    def now(self) -> int:
        return int(datetime.now(tz=timezone.utc).timestamp())

    def parse(self, value: Any, *, enhanced: bool = False) -> int | None:
        if value is None:
            return None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return int(value)
        text = str(value).strip()
        if not text:
            return None
        try:
            return int(float(text))
        except ValueError:
            pass
        try:
            return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp())
        except ValueError:
            if not enhanced:
                return None
        try:
            from dateutil import parser
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("Enhanced time parsing requires `pip install erlc-api[time]`.") from exc
        parsed = parser.parse(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp())

    def format(self, timestamp: int | None, *, tz: timezone = timezone.utc) -> str | None:
        if timestamp is None:
            return None
        return datetime.fromtimestamp(timestamp, tz=tz).isoformat()

    def age(self, timestamp: int | None, *, now: int | None = None) -> str:
        if timestamp is None:
            return "unknown"
        delta = max(0, (now or self.now()) - timestamp)
        if delta < 60:
            return f"{delta}s"
        if delta < 3600:
            return f"{delta // 60}m"
        if delta < 86400:
            return f"{delta // 3600}h"
        return f"{delta // 86400}d"

    def last(self, *, seconds: int = 0, minutes: int = 0, hours: int = 0, days: int = 0, now: int | None = None) -> TimeWindow:
        end = now or self.now()
        delta = timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        return TimeWindow(start=int(end - delta.total_seconds()), end=end)

    def between(self, start: Any, end: Any) -> TimeWindow:
        parsed_start = self.parse(start)
        parsed_end = self.parse(end)
        if parsed_start is None or parsed_end is None:
            raise ValueError("start and end must be parseable timestamps.")
        return TimeWindow(start=parsed_start, end=parsed_end)


__all__ = ["TimeTools", "TimeWindow"]
