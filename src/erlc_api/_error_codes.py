from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ._errors import (
    APIError,
    AuthError,
    BadRequestError,
    InvalidCommandError,
    ModuleOutdatedError,
    PermissionDeniedError,
    ProhibitedMessageError,
    RateLimitError,
    RestrictedCommandError,
    RobloxCommunicationError,
    ServerOfflineError,
    NotFoundError,
)


@dataclass(frozen=True)
class ErrorCodeInfo:
    code: int
    name: str
    category: str
    exception: type[APIError]
    retryable: bool
    auth_related: bool
    message: str
    advice: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "category": self.category,
            "exception": self.exception.__name__,
            "retryable": self.retryable,
            "auth_related": self.auth_related,
            "message": self.message,
            "advice": self.advice,
        }


_ERROR_CODES: dict[int, ErrorCodeInfo] = {
    0: ErrorCodeInfo(
        0,
        "unknown_error",
        "unknown",
        APIError,
        False,
        False,
        "PRC returned an unknown API error.",
        "Log the status, error code, and redacted response body for diagnostics.",
    ),
    1001: ErrorCodeInfo(
        1001,
        "roblox_communication_error",
        "upstream",
        RobloxCommunicationError,
        True,
        False,
        "PRC could not communicate with Roblox or the in-game module.",
        "Treat as temporary unless repeated, then inspect server/module health.",
    ),
    1002: ErrorCodeInfo(
        1002,
        "roblox_communication_error",
        "upstream",
        RobloxCommunicationError,
        True,
        False,
        "PRC could not communicate with Roblox or the in-game module.",
        "Treat as temporary unless repeated, then inspect server/module health.",
    ),
    2000: ErrorCodeInfo(
        2000,
        "authorization_error",
        "auth",
        AuthError,
        False,
        True,
        "The API credentials are missing, invalid, banned, or unauthorized.",
        "Check the server key, optional global key, and PRC key permissions.",
    ),
    2001: ErrorCodeInfo(
        2001,
        "authorization_error",
        "auth",
        AuthError,
        False,
        True,
        "The API credentials are missing, invalid, banned, or unauthorized.",
        "Check the server key, optional global key, and PRC key permissions.",
    ),
    2002: ErrorCodeInfo(
        2002,
        "authorization_error",
        "auth",
        AuthError,
        False,
        True,
        "The API credentials are missing, invalid, banned, or unauthorized.",
        "Check the server key, optional global key, and PRC key permissions.",
    ),
    2003: ErrorCodeInfo(
        2003,
        "authorization_error",
        "auth",
        AuthError,
        False,
        True,
        "The API credentials are missing, invalid, banned, or unauthorized.",
        "Check the server key, optional global key, and PRC key permissions.",
    ),
    2004: ErrorCodeInfo(
        2004,
        "authorization_error",
        "auth",
        AuthError,
        False,
        True,
        "The API credentials are missing, invalid, banned, or unauthorized.",
        "Check the server key, optional global key, and PRC key permissions.",
    ),
    3001: ErrorCodeInfo(
        3001,
        "invalid_command",
        "command",
        InvalidCommandError,
        False,
        False,
        "The command request is missing, malformed, or invalid.",
        "Use `dry_run=True` to inspect the normalized command before sending.",
    ),
    3002: ErrorCodeInfo(
        3002,
        "server_offline",
        "server",
        ServerOfflineError,
        True,
        False,
        "The server is offline, unavailable, or has no players.",
        "Retry later or show an offline/degraded status to users.",
    ),
    4001: ErrorCodeInfo(
        4001,
        "rate_limited",
        "rate_limit",
        RateLimitError,
        True,
        False,
        "The request was rate-limited by PRC.",
        "Use retry metadata, enable `rate_limited=True`, or slow polling.",
    ),
    4002: ErrorCodeInfo(
        4002,
        "restricted_command",
        "command",
        RestrictedCommandError,
        False,
        False,
        "The command exists but PRC restricts it from API execution.",
        "Use a different moderation workflow or command.",
    ),
    4003: ErrorCodeInfo(
        4003,
        "prohibited_message",
        "command",
        ProhibitedMessageError,
        False,
        False,
        "PRC rejected the command text because the message is prohibited.",
        "Inspect message content and avoid resending the same text.",
    ),
    9998: ErrorCodeInfo(
        9998,
        "permission_denied",
        "auth",
        PermissionDeniedError,
        False,
        True,
        "The API key is valid but lacks permission for the requested resource.",
        "Check PRC permissions for the key and endpoint.",
    ),
    9999: ErrorCodeInfo(
        9999,
        "module_outdated",
        "server",
        ModuleOutdatedError,
        False,
        False,
        "The in-game private server module is out of date.",
        "Update the in-game ER:LC private server module.",
    ),
}


def _coerce_code(value: Any) -> int | None:
    if value is None:
        return None
    if hasattr(value, "error_code"):
        return _coerce_code(getattr(value, "error_code"))
    if isinstance(value, Mapping):
        for key in ("error_code", "errorCode", "code"):
            if key in value:
                return _coerce_code(value[key])
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def explain_error_code(code_or_error: Any) -> ErrorCodeInfo | None:
    code = _coerce_code(code_or_error)
    if code is None:
        return None
    return _ERROR_CODES.get(code)


def list_error_codes(category: str | None = None) -> list[ErrorCodeInfo]:
    if category is None:
        return [_ERROR_CODES[code] for code in sorted(_ERROR_CODES)]
    wanted = category.strip().lower()
    return [info for info in list_error_codes() if info.category.lower() == wanted]


def exception_for_error_code(code: int | None, status: int | None = None) -> type[APIError]:
    info = explain_error_code(code)
    if info is not None:
        return info.exception
    if status == 404:
        return NotFoundError
    if status == 429:
        return RateLimitError
    if status == 403:
        return AuthError
    if status == 422:
        return ServerOfflineError
    if status is not None and status >= 500:
        return RobloxCommunicationError
    if status == 400:
        return BadRequestError
    return APIError


__all__ = [
    "ErrorCodeInfo",
    "exception_for_error_code",
    "explain_error_code",
    "list_error_codes",
]
