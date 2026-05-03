from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Callable


Clock = Callable[[], float]


def _normalize_key(key: object) -> str:
    text = str(key).strip()
    if not text:
        raise ValueError("idempotency key cannot be blank.")
    return text


def _validate_ttl(ttl_s: float) -> float:
    if ttl_s <= 0:
        raise ValueError("ttl_s must be greater than zero.")
    return float(ttl_s)


class MemoryDeduper:
    """In-memory TTL deduper. `check_and_mark` returns True when already seen."""

    def __init__(self, ttl_s: float = 300, *, now: Clock | None = None) -> None:
        self.ttl_s = _validate_ttl(ttl_s)
        self._now = now or time.time
        self._items: dict[str, float] = {}

    def seen(self, key: object) -> bool:
        self.prune()
        return _normalize_key(key) in self._items

    def mark(self, key: object) -> str:
        normalized = _normalize_key(key)
        self._items[normalized] = self._now() + self.ttl_s
        return normalized

    def check_and_mark(self, key: object) -> bool:
        if self.seen(key):
            return True
        self.mark(key)
        return False

    def prune(self) -> int:
        now = self._now()
        expired = [key for key, expires_at in self._items.items() if expires_at <= now]
        for key in expired:
            self._items.pop(key, None)
        return len(expired)


class FileDeduper:
    """File-backed TTL deduper for webhooks and watcher restarts."""

    def __init__(self, path: str | Path, ttl_s: float = 300, *, now: Clock | None = None) -> None:
        self.path = Path(path)
        self.ttl_s = _validate_ttl(ttl_s)
        self._now = now or time.time

    def seen(self, key: object) -> bool:
        items = self._load(prune=True)
        return _normalize_key(key) in items

    def mark(self, key: object) -> str:
        normalized = _normalize_key(key)
        items = self._load(prune=True)
        items[normalized] = self._now() + self.ttl_s
        self._save(items)
        return normalized

    def check_and_mark(self, key: object) -> bool:
        if self.seen(key):
            return True
        self.mark(key)
        return False

    def prune(self) -> int:
        before = self._load(prune=False)
        after = self._pruned(before)
        self._save(after)
        return len(before) - len(after)

    def _load(self, *, prune: bool) -> dict[str, float]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(raw, dict):
            return {}
        items: dict[str, float] = {}
        for key, value in raw.items():
            try:
                items[str(key)] = float(value)
            except (TypeError, ValueError):
                continue
        return self._pruned(items) if prune else items

    def _pruned(self, items: dict[str, float]) -> dict[str, float]:
        now = self._now()
        return {key: expires_at for key, expires_at in items.items() if expires_at > now}

    def _save(self, items: dict[str, float]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(f"{self.path.name}.tmp")
        tmp.write_text(json.dumps(items, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)


__all__ = ["FileDeduper", "MemoryDeduper"]
