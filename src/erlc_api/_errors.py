from __future__ import annotations

from typing import Any


def _safe_excerpt(raw: Any, *, limit: int = 300) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        text = raw
    else:
        text = repr(raw)
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


class ERLCError(Exception):
    """Base exception for wrapper failures with request metadata."""

    def __init__(
        self,
        message: str,
        *,
        method: str,
        path: str,
        status: int | None = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.method = method.upper()
        self.path = path
        self.status = status
        self.body_excerpt = _safe_excerpt(body)

    @property
    def status_code(self) -> int | None:
        """Backward-compatible alias used by older callers."""
        return self.status

    def __str__(self) -> str:
        bits: list[str] = [f"{self.__class__.__name__}: {self.message}", f"method={self.method}", f"path={self.path}"]
        if self.status is not None:
            bits.append(f"status={self.status}")
        if self.body_excerpt:
            bits.append(f"body={self.body_excerpt}")
        return " | ".join(bits)


class APIError(ERLCError):
    """Generic API error for non-success responses."""


class AuthError(APIError):
    """Authentication or authorization failure."""


class PermissionDeniedError(AuthError):
    """The authenticated user does not have required permissions."""


class NotFoundError(APIError):
    """API resource was not found."""


class PlayerNotFoundError(NotFoundError):
    """The requested player was not found in the target server."""


class NetworkError(ERLCError):
    """Transport-level failure (timeouts, DNS, connection errors)."""


class RateLimitError(APIError):
    """Rate-limit failure that may include retry hints from the API."""

    def __init__(
        self,
        message: str,
        *,
        method: str,
        path: str,
        status: int = 429,
        body: Any = None,
        bucket: str | None = None,
        retry_after: float | None = None,
        reset_epoch_s: float | None = None,
    ) -> None:
        super().__init__(message, method=method, path=path, status=status, body=body)
        self.bucket = bucket
        self.retry_after = retry_after
        self.reset_epoch_s = reset_epoch_s

    @property
    def retry_after_s(self) -> float | None:
        """Backward-compatible alias used by older callers."""
        return self.retry_after


class CircuitOpenError(ERLCError):
    """Request was rejected because the circuit breaker is open for this bucket."""

    def __init__(
        self,
        message: str,
        *,
        method: str,
        path: str,
        bucket: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, method=method, path=path, status=None, body=None)
        self.bucket = bucket
        self.retry_after = retry_after


class ServerEmptyError(APIError):
    """Server currently has no players or no data in the requested section."""


class RobloxCommunicationError(APIError):
    """PRC backend could not communicate with Roblox services."""


class InvalidCommandError(APIError):
    """Command format/syntax was rejected."""


class ModelDecodeError(ERLCError):
    """Raised when typed decoding fails due to top-level payload shape mismatch."""

    def __init__(
        self,
        message: str,
        *,
        endpoint: str,
        expected: str,
        payload: Any,
    ) -> None:
        super().__init__(
            message,
            method="DECODE",
            path=endpoint,
            status=None,
            body=payload,
        )
        self.endpoint = endpoint
        self.expected = expected
