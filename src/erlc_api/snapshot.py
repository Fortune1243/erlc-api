from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any

from . import _utility as u


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(u.model_dict(value), ensure_ascii=False, default=str))


@dataclass(frozen=True)
class Snapshot:
    saved_at: float
    data: Any

    def to_dict(self) -> dict[str, Any]:
        return {"saved_at": self.saved_at, "data": _json_safe(self.data)}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True)
class SnapshotDiff:
    previous: Snapshot | None
    current: Snapshot
    changed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "previous": self.previous.to_dict() if self.previous is not None else None,
            "current": self.current.to_dict(),
            "changed": self.changed,
        }


class SnapshotStore:
    """JSONL snapshot store for typed models and raw payloads."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, bundle: Any) -> Snapshot:
        snapshot = Snapshot(saved_at=time.time(), data=_json_safe(bundle))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(snapshot.to_json())
            stream.write("\n")
        return snapshot

    def latest(self) -> Snapshot | None:
        snapshots = self.history(limit=1)
        return snapshots[0] if snapshots else None

    def history(self, limit: int | None = None) -> list[Snapshot]:
        if limit is not None and limit < 0:
            raise ValueError("limit must be greater than or equal to zero.")
        if limit == 0 or not self.path.exists():
            return []

        snapshots: list[Snapshot] = []
        with self.path.open("r", encoding="utf-8") as stream:
            for line in stream:
                text = line.strip()
                if not text:
                    continue
                try:
                    raw = json.loads(text)
                    snapshots.append(Snapshot(saved_at=float(raw["saved_at"]), data=raw.get("data")))
                except (TypeError, ValueError, KeyError, json.JSONDecodeError):
                    continue
        return snapshots[-limit:] if limit is not None else snapshots

    def diff_latest(self, bundle: Any) -> SnapshotDiff:
        previous = self.latest()
        current = Snapshot(saved_at=time.time(), data=_json_safe(bundle))
        changed = previous is None or previous.data != current.data
        return SnapshotDiff(previous=previous, current=current, changed=changed)

    def prune(self, *, max_entries: int) -> int:
        if max_entries <= 0:
            raise ValueError("max_entries must be greater than zero.")
        snapshots = self.history()
        if len(snapshots) <= max_entries:
            return 0

        kept = snapshots[-max_entries:]
        removed = len(snapshots) - len(kept)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as stream:
            for snapshot in kept:
                stream.write(snapshot.to_json())
                stream.write("\n")
        return removed


__all__ = ["Snapshot", "SnapshotDiff", "SnapshotStore"]
