from __future__ import annotations

from typing import Any


def _safe_excerpt(value: Any, *, limit: int = 300) -> str | None:
    if value is None:
        return None
    text = value if isinstance(value, str) else repr(value)
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


class ERLCError(Exception):
    """Base exception for PRC API wrapper failures."""

    def __init__(
        self,
        message: str,
        *,
        method: str | None = None,
        path: str | None = None,
        status: int | None = None,
        body: Any = None,
        error_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.method = method.upper() if method else None
        self.path = path
        self.status = status
        self.error_code = error_code
        self.body_excerpt = _safe_excerpt(body)

    @property
    def status_code(self) -> int | None:
        return self.status

    def __str__(self) -> str:
        parts = [f"{self.__class__.__name__}: {self.message}"]
        if self.method:
            parts.append(f"method={self.method}")
        if self.path:
            parts.append(f"path={self.path}")
        if self.status is not None:
            parts.append(f"status={self.status}")
        if self.error_code is not None:
            parts.append(f"error_code={self.error_code}")
        if self.body_excerpt:
            parts.append(f"body={self.body_excerpt}")
        return " | ".join(parts)


class APIError(ERLCError):
    """Generic non-success response from the PRC API."""


class BadRequestError(APIError):
    """The API rejected the request payload, path, or parameters."""


class AuthError(APIError):
    """Missing, malformed, expired, banned, or unauthorized API credentials."""


class PermissionDeniedError(AuthError):
    """The API key is valid but cannot access the requested resource."""


class NotFoundError(APIError):
    """The requested API resource was not found."""


class NetworkError(ERLCError):
    """Transport-level failure such as timeout, DNS, or connection errors."""


class RateLimitError(APIError):
    """PRC rate limit response with retry metadata when provided."""

    def __init__(
        self,
        message: str,
        *,
        method: str,
        path: str,
        status: int = 429,
        body: Any = None,
        error_code: int | None = None,
        bucket: str | None = None,
        retry_after: float | None = None,
        reset_epoch_s: float | None = None,
    ) -> None:
        super().__init__(
            message,
            method=method,
            path=path,
            status=status,
            body=body,
            error_code=error_code,
        )
        self.bucket = bucket
        self.retry_after = retry_after
        self.reset_epoch_s = reset_epoch_s

    @property
    def retry_after_s(self) -> float | None:
        return self.retry_after


class InvalidCommandError(BadRequestError):
    """The command request is missing, malformed, or invalid."""


class RestrictedCommandError(PermissionDeniedError):
    """The command exists but PRC restricts it from API execution."""


class ProhibitedMessageError(BadRequestError):
    """The API rejected command text because the message is prohibited."""


class ServerOfflineError(APIError):
    """The target private server is offline or has no players."""


class ServerEmptyError(ServerOfflineError):
    """Backward-compatible alias for server offline/no players."""


class RobloxCommunicationError(APIError):
    """PRC could not communicate with Roblox or the in-game module."""


class ModuleOutdatedError(APIError):
    """The in-game private server module is out of date."""


class PlayerNotFoundError(NotFoundError):
    """The requested player was not found."""


class ModelDecodeError(ERLCError):
    """Typed model decoding failed because the payload shape was unexpected."""

    def __init__(self, message: str, *, endpoint: str, expected: str, payload: Any) -> None:
        super().__init__(
            message,
            method="DECODE",
            path=endpoint,
            body=payload,
        )
        self.endpoint = endpoint
        self.expected = expected


class CircuitOpenError(APIError):
    """Removed in v2.0; retained only so old imports fail less abruptly."""

