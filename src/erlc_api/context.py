# src/erlc_api/context.py
from __future__ import annotations

from dataclasses import dataclass
import hashlib


def _fingerprint(server_key: str) -> str:
    # Stable, non reversible identifier for internal maps
    return hashlib.sha256(server_key.encode("utf-8")).hexdigest()[:16]


def fingerprint_key(server_key: str) -> str:
    """Return a short printable key fingerprint safe for logs."""
    key = (server_key or "").strip()
    if not key:
        return "empty(len=0)"
    return f"sha256:{_fingerprint(key)}(len={len(key)})"

@dataclass(frozen=True)
class ERLCContext:
    server_key: str

    @property
    def key_id(self) -> str:
        return _fingerprint(self.server_key)

    def __repr__(self) -> str:
        # Never leak the key in logs
        return f"ERLCContext(key={fingerprint_key(self.server_key)}, key_id={self.key_id})"
