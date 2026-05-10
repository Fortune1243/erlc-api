from __future__ import annotations

from dataclasses import dataclass
import hashlib
import time


def key_fingerprint(key: str, *, length: int = 12, algorithm: str = "sha256") -> str:
    """Return a stable non-secret fingerprint for logging or diagnostics."""
    if not isinstance(key, str):
        raise TypeError("key must be a string.")
    text = key.strip()
    if not text:
        raise ValueError("key cannot be blank.")
    if length <= 0:
        raise ValueError("length must be positive.")

    algorithm_name = algorithm.lower().strip()
    try:
        digest = hashlib.new(algorithm_name, text.encode("utf-8")).hexdigest()
    except ValueError as exc:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from exc

    return f"{algorithm_name}:{digest[: min(length, len(digest))]}"


@dataclass(frozen=True)
class AuthFailureRecord:
    fingerprint: str
    count: int
    first_seen: float
    last_seen: float

    @property
    def repeated(self) -> bool:
        return self.count > 1

    def to_dict(self) -> dict[str, str | int | float | bool]:
        return {
            "fingerprint": self.fingerprint,
            "count": self.count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "repeated": self.repeated,
        }


class AuthFailureTracker:
    """In-memory auth failure counter keyed by non-secret key fingerprints."""

    def __init__(self, *, now=None) -> None:
        self._now = now or time.time
        self._records: dict[str, AuthFailureRecord] = {}

    def mark(self, key: str) -> AuthFailureRecord:
        fingerprint = key_fingerprint(key)
        now = self._now()
        previous = self._records.get(fingerprint)
        record = AuthFailureRecord(
            fingerprint=fingerprint,
            count=(previous.count + 1) if previous else 1,
            first_seen=previous.first_seen if previous else now,
            last_seen=now,
        )
        self._records[fingerprint] = record
        return record

    def get(self, key_or_fingerprint: str) -> AuthFailureRecord | None:
        if key_or_fingerprint.startswith("sha"):
            return self._records.get(key_or_fingerprint)
        return self._records.get(key_fingerprint(key_or_fingerprint))

    def snapshot(self) -> tuple[AuthFailureRecord, ...]:
        return tuple(sorted(self._records.values(), key=lambda item: item.last_seen, reverse=True))

    def reset(self) -> None:
        self._records.clear()


auth_failures = AuthFailureTracker()


__all__ = ["AuthFailureRecord", "AuthFailureTracker", "auth_failures", "key_fingerprint"]
