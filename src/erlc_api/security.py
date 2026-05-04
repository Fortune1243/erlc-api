from __future__ import annotations

import hashlib


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


__all__ = ["key_fingerprint"]
