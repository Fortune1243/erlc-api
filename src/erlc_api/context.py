# src/erlc_api/context.py
from __future__ import annotations

from dataclasses import dataclass
import hashlib


def fingerprint_key(server_key: str) -> str:
    """Return a short printable key fingerprint safe for logs."""
    key = (server_key or "").strip()
    if not key:
        return "empty(len=0)"
    if len(key) <= 8:
        return f"{key[:4]}...{key[-4:]}(len={len(key)})"
    return f"{key[:4]}...{key[-4:]}(len={len(key)})"


def _fingerprint(server_key: str) -> str:
    # Stable, non reversible identifier for internal maps
    return hashlib.sha256(server_key.encode("utf-8")).hexdigest()[:16]

@dataclass(frozen=True)
class ERLCContext:
    server_key: str

    @property
    def key_id(self) -> str:
        return _fingerprint(self.server_key)

    def __repr__(self) -> str:
        # Never leak the key in logs
        return f"ERLCContext(key={fingerprint_key(self.server_key)}, key_id={self.key_id})"
