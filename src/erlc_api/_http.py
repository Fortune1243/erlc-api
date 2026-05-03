from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
import importlib.metadata as importlib_metadata
import time
from datetime import timezone
from typing import Any, Mapping

import httpx

from ._constants import BASE_URL, DEFAULT_TIMEOUT_S
from ._errors import (
    APIError,
    AuthError,
    BadRequestError,
    InvalidCommandError,
    ModuleOutdatedError,
    NetworkError,
    NotFoundError,
    PermissionDeniedError,
    ProhibitedMessageError,
    RateLimitError,
    RestrictedCommandError,
    RobloxCommunicationError,
    ServerOfflineError,
)


def _default_user_agent() -> str:
    try:
        version = importlib_metadata.version("erlc-api")
    except importlib_metadata.PackageNotFoundError:
        version = "0+unknown"
    return f"erlc-api-python/{version}"


@dataclass
class ClientSettings:
    base_url: str = BASE_URL
    timeout_s: float = DEFAULT_TIMEOUT_S
    retry_429: bool = True
    user_agent: str = field(default_factory=_default_user_agent)


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _safe_json(resp: httpx.Response) -> Any:
    if not resp.content:
        return None
    try:
        return resp.json()
    except Exception:
        return resp.text


def _parse_retry_after(resp: httpx.Response, raw: Any = None) -> float | None:
    header = resp.headers.get("Retry-After")
    parsed = _parse_float(header)
    if parsed is not None:
        return max(0.0, parsed)
    if header:
        try:
            dt = parsedate_to_datetime(header)
        except (TypeError, ValueError, IndexError, OverflowError):
            dt = None
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return max(0.0, dt.timestamp() - time.time())
    if isinstance(raw, Mapping):
        for key in ("retry_after", "retryAfter", "retry"):
            parsed = _parse_float(str(raw[key])) if key in raw and raw[key] is not None else None
            if parsed is not None:
                return max(0.0, parsed)
    return None


def _message_from_body(raw: Any) -> str | None:
    if isinstance(raw, Mapping):
        for key in ("message", "Message", "error", "Error"):
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _error_code(raw: Any) -> int | None:
    if not isinstance(raw, Mapping):
        return None
    for key in ("error_code", "errorCode", "code"):
        value = raw.get(key)
        try:
            if value is not None:
                return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _rate_limit_error(method: str, path: str, resp: httpx.Response, raw: Any) -> RateLimitError:
    reset = _parse_float(resp.headers.get("X-RateLimit-Reset"))
    return RateLimitError(
        _message_from_body(raw) or "Rate limited",
        method=method,
        path=path,
        status=resp.status_code,
        body=raw,
        error_code=_error_code(raw),
        bucket=resp.headers.get("X-RateLimit-Bucket"),
        retry_after=_parse_retry_after(resp, raw),
        reset_epoch_s=reset,
    )


def _map_error(method: str, path: str, status: int, raw: Any) -> APIError:
    code = _error_code(raw)
    message = _message_from_body(raw) or "PRC API request failed"

    if status == 404:
        return NotFoundError(message, method=method, path=path, status=status, body=raw, error_code=code)
    if status == 429 or code == 4001:
        dummy = httpx.Response(status, json=raw if raw is not None else {})
        return _rate_limit_error(method, path, dummy, raw)
    if status == 403 or code in {2000, 2001, 2002, 2003, 2004}:
        return AuthError(message, method=method, path=path, status=status, body=raw, error_code=code)
    if code == 3001:
        return InvalidCommandError(message, method=method, path=path, status=status, body=raw, error_code=code)
    if code == 3002 or status == 422:
        return ServerOfflineError(message, method=method, path=path, status=status, body=raw, error_code=code)
    if code == 4002:
        return RestrictedCommandError(message, method=method, path=path, status=status, body=raw, error_code=code)
    if code == 4003:
        return ProhibitedMessageError(message, method=method, path=path, status=status, body=raw, error_code=code)
    if code == 9998:
        return PermissionDeniedError(message, method=method, path=path, status=status, body=raw, error_code=code)
    if code == 9999:
        return ModuleOutdatedError(message, method=method, path=path, status=status, body=raw, error_code=code)
    if code in {1001, 1002} or status >= 500:
        return RobloxCommunicationError(message, method=method, path=path, status=status, body=raw, error_code=code)
    if status == 400:
        return BadRequestError(message, method=method, path=path, status=status, body=raw, error_code=code)
    return APIError(message, method=method, path=path, status=status, body=raw, error_code=code)


def _build_headers(*, server_key: str, global_key: str | None, headers: Mapping[str, str] | None) -> dict[str, str]:
    out = {"Server-Key": server_key}
    if global_key:
        out["Authorization"] = global_key
    if headers:
        for key, value in headers.items():
            if key.lower() in {"server-key", "authorization"}:
                continue
            out[key] = value
    return out


def _decode_response(resp: httpx.Response) -> Any:
    if not resp.content:
        return None
    content_type = resp.headers.get("content-type", "").lower()
    if "json" in content_type:
        return resp.json()
    try:
        return resp.json()
    except Exception:
        return resp.text


class AsyncTransport:
    def __init__(self, settings: ClientSettings, *, global_key: str | None = None) -> None:
        self.settings = settings
        self.global_key = global_key
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        if self._client is not None:
            return
        self._client = httpx.AsyncClient(
            base_url=self.settings.base_url,
            timeout=self.settings.timeout_s,
            headers={"User-Agent": self.settings.user_agent},
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("HTTP client is not started.")
        return self._client

    async def request(
        self,
        *,
        server_key: str,
        method: str,
        path: str,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        await self.start()
        method_u = method.upper()
        request_headers = _build_headers(server_key=server_key, global_key=self.global_key, headers=headers)

        for attempt in range(2):
            try:
                resp = await self.client.request(
                    method_u,
                    path,
                    params=params,
                    json=json,
                    headers=request_headers,
                )
            except (httpx.TimeoutException, httpx.NetworkError, httpx.RequestError) as exc:
                raise NetworkError(f"Network error: {exc}", method=method_u, path=path) from exc

            if 200 <= resp.status_code < 300:
                return _decode_response(resp)

            raw = _safe_json(resp)
            if resp.status_code == 429:
                err = _rate_limit_error(method_u, path, resp, raw)
                if self.settings.retry_429 and attempt == 0:
                    sleep_s = err.retry_after
                    if sleep_s is None and err.reset_epoch_s is not None:
                        sleep_s = max(0.0, err.reset_epoch_s - time.time())
                    if sleep_s is not None:
                        await asyncio.sleep(sleep_s)
                        continue
                raise err
            raise _map_error(method_u, path, resp.status_code, raw)

        raise APIError("PRC API request failed", method=method_u, path=path)


class SyncTransport:
    def __init__(self, settings: ClientSettings, *, global_key: str | None = None) -> None:
        self.settings = settings
        self.global_key = global_key
        self._client: httpx.Client | None = None

    def start(self) -> None:
        if self._client is not None:
            return
        self._client = httpx.Client(
            base_url=self.settings.base_url,
            timeout=self.settings.timeout_s,
            headers={"User-Agent": self.settings.user_agent},
        )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
        self._client = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            raise RuntimeError("HTTP client is not started.")
        return self._client

    def request(
        self,
        *,
        server_key: str,
        method: str,
        path: str,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        self.start()
        method_u = method.upper()
        request_headers = _build_headers(server_key=server_key, global_key=self.global_key, headers=headers)

        for attempt in range(2):
            try:
                resp = self.client.request(
                    method_u,
                    path,
                    params=params,
                    json=json,
                    headers=request_headers,
                )
            except (httpx.TimeoutException, httpx.NetworkError, httpx.RequestError) as exc:
                raise NetworkError(f"Network error: {exc}", method=method_u, path=path) from exc

            if 200 <= resp.status_code < 300:
                return _decode_response(resp)

            raw = _safe_json(resp)
            if resp.status_code == 429:
                err = _rate_limit_error(method_u, path, resp, raw)
                if self.settings.retry_429 and attempt == 0:
                    sleep_s = err.retry_after
                    if sleep_s is None and err.reset_epoch_s is not None:
                        sleep_s = max(0.0, err.reset_epoch_s - time.time())
                    if sleep_s is not None:
                        time.sleep(sleep_s)
                        continue
                raise err
            raise _map_error(method_u, path, resp.status_code, raw)

        raise APIError("PRC API request failed", method=method_u, path=path)


AsyncHTTP = AsyncTransport


__all__ = [
    "AsyncHTTP",
    "AsyncTransport",
    "ClientSettings",
    "SyncTransport",
    "_default_user_agent",
    "_parse_retry_after",
]
