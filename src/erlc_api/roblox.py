from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from email.utils import parsedate_to_datetime
import time
from datetime import timezone
from typing import Any

import httpx

from ._errors import ERLCError
from ._http import _default_user_agent
from .cache import CacheStats, MemoryCache


ROBLOX_USERS_BASE_URL = "https://users.roblox.com"
_SENTINEL = object()


class RobloxError(ERLCError):
    """Base exception for Roblox lookup helper failures."""


class RobloxAPIError(RobloxError):
    """Roblox returned a non-success response or an unexpected payload."""


class RobloxNetworkError(RobloxError):
    """Transport-level Roblox lookup failure such as timeout or DNS errors."""


class RobloxRateLimitError(RobloxAPIError):
    """Roblox returned a rate-limit response."""

    def __init__(
        self,
        message: str,
        *,
        method: str,
        path: str,
        status: int = 429,
        body: Any = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, method=method, path=path, status=status, body=body)
        self.retry_after = retry_after

    @property
    def retry_after_s(self) -> float | None:
        return self.retry_after


@dataclass(frozen=True)
class RobloxUser:
    user_id: int | None = None
    name: str | None = None
    display_name: str | None = None
    has_verified_badge: bool | None = None
    requested_username: str | None = None
    description: str | None = None
    created_at: str | None = None
    is_banned: bool | None = None
    external_app_display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return str(value)


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None
    return None


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "yes", "1"}:
            return True
        if text in {"false", "no", "0"}:
            return False
    return None


def _user_id(value: Any) -> int | None:
    parsed = _as_int(value)
    return parsed if parsed is not None and parsed > 0 else None


def _username(value: Any) -> str | None:
    text = _as_str(value)
    return text or None


def _unique_ids(values: Iterable[Any]) -> list[int]:
    out: list[int] = []
    seen: set[int] = set()
    for value in values:
        parsed = _user_id(value)
        if parsed is None or parsed in seen:
            continue
        seen.add(parsed)
        out.append(parsed)
    return out


def _unique_usernames(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        parsed = _username(value)
        if parsed is None:
            continue
        key = parsed.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(parsed)
    return out


def _pick(raw: Mapping[str, Any], *keys: str) -> tuple[str | None, Any]:
    for key in keys:
        if key in raw:
            return key, raw[key]
    return None, None


def _extra(raw: Mapping[str, Any], consumed: set[str]) -> dict[str, Any]:
    return {key: value for key, value in raw.items() if key not in consumed}


def _decode_user(raw: Mapping[str, Any]) -> RobloxUser:
    consumed: set[str] = set()

    id_key, user_id = _pick(raw, "id", "userId", "user_id")
    name_key, name = _pick(raw, "name", "username", "userName")
    display_key, display_name = _pick(raw, "displayName", "display_name")
    verified_key, verified = _pick(raw, "hasVerifiedBadge", "has_verified_badge")
    requested_key, requested = _pick(raw, "requestedUsername", "requested_username")
    description_key, description = _pick(raw, "description")
    created_key, created = _pick(raw, "created", "createdAt", "created_at")
    banned_key, banned = _pick(raw, "isBanned", "is_banned")
    external_key, external = _pick(raw, "externalAppDisplayName", "external_app_display_name")

    consumed.update(
        key
        for key in (
            id_key,
            name_key,
            display_key,
            verified_key,
            requested_key,
            description_key,
            created_key,
            banned_key,
            external_key,
        )
        if key is not None
    )

    return RobloxUser(
        user_id=_as_int(user_id),
        name=_as_str(name),
        display_name=_as_str(display_name),
        has_verified_badge=_as_bool(verified),
        requested_username=_as_str(requested),
        description=_as_str(description),
        created_at=_as_str(created),
        is_banned=_as_bool(banned),
        external_app_display_name=_as_str(external),
        raw=dict(raw),
        extra=_extra(raw, consumed),
    )


def _safe_json(resp: httpx.Response) -> Any:
    if not resp.content:
        return None
    try:
        return resp.json()
    except Exception:
        return resp.text


def _parse_retry_after(resp: httpx.Response) -> float | None:
    header = resp.headers.get("Retry-After")
    if header is None:
        return None
    try:
        return max(0.0, float(header))
    except ValueError:
        pass
    try:
        dt = parsedate_to_datetime(header)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0.0, dt.timestamp() - time.time())


def _message(raw: Any, default: str) -> str:
    if isinstance(raw, Mapping):
        for key in ("message", "Message", "error", "Error"):
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return default


def _handle_response(
    resp: httpx.Response,
    *,
    method: str,
    path: str,
    allow_404: bool = False,
) -> Any:
    raw = _safe_json(resp)
    if 200 <= resp.status_code < 300:
        return raw
    if resp.status_code == 404 and allow_404:
        return None
    if resp.status_code == 429:
        raise RobloxRateLimitError(
            _message(raw, "Roblox rate limit exceeded"),
            method=method,
            path=path,
            status=resp.status_code,
            body=raw,
            retry_after=_parse_retry_after(resp),
        )
    raise RobloxAPIError(
        _message(raw, "Roblox API request failed"),
        method=method,
        path=path,
        status=resp.status_code,
        body=raw,
    )


def _data(raw: Any, *, endpoint: str) -> list[Any]:
    if not isinstance(raw, Mapping):
        raise RobloxAPIError("Unexpected Roblox response shape.", method="DECODE", path=endpoint, body=raw)
    data = raw.get("data")
    if not isinstance(data, list):
        raise RobloxAPIError("Unexpected Roblox response shape.", method="DECODE", path=endpoint, body=raw)
    return data


def _render(user: RobloxUser, *, raw: bool) -> RobloxUser | dict[str, Any]:
    return dict(user.raw) if raw else user


def _minimal_key(user_id: int) -> str:
    return f"roblox:user:{user_id}"


def _profile_key(user_id: int) -> str:
    return f"roblox:profile:{user_id}"


def _username_key(username: str, *, exclude_banned_users: bool) -> str:
    return f"roblox:username:{int(exclude_banned_users)}:{username.casefold()}"


class _BaseRobloxClient:
    def _init_base(
        self,
        *,
        base_url: str,
        timeout_s: float,
        ttl_s: float,
        user_agent: str | None,
    ) -> None:
        if ttl_s <= 0:
            raise ValueError("ttl_s must be greater than zero.")
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.ttl_s = ttl_s
        self._cache = MemoryCache()
        self._headers = {"User-Agent": user_agent or _default_user_agent()}

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def clear_cache(self) -> None:
        self._cache.clear()

    def cache_stats(self) -> CacheStats:
        return self._cache.stats()

    def _cache_get(self, key: str) -> RobloxUser | None:
        cached = self._cache.get(key, _SENTINEL)
        return None if cached is _SENTINEL else cached

    def _cache_set(self, key: str, user: RobloxUser) -> None:
        self._cache.set(key, user, ttl_s=self.ttl_s)


class RobloxClient(_BaseRobloxClient):
    """Sync Roblox user/profile lookup helper."""

    def __init__(
        self,
        *,
        base_url: str = ROBLOX_USERS_BASE_URL,
        timeout_s: float = 10.0,
        ttl_s: float = 3600.0,
        user_agent: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._init_base(base_url=base_url, timeout_s=timeout_s, ttl_s=ttl_s, user_agent=user_agent)
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout_s, headers=self._headers)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> RobloxClient:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def _request(self, method: str, path: str, *, json: Any = None, allow_404: bool = False) -> Any:
        method_u = method.upper()
        try:
            resp = self._client.request(
                method_u,
                self._url(path),
                json=json,
                headers=self._headers,
                timeout=self.timeout_s,
            )
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RequestError) as exc:
            raise RobloxNetworkError(f"Roblox network error: {exc}", method=method_u, path=path) from exc
        return _handle_response(resp, method=method_u, path=path, allow_404=allow_404)

    def profile(self, user_id: Any, *, raw: bool = False) -> RobloxUser | dict[str, Any] | None:
        parsed = _user_id(user_id)
        if parsed is None:
            return None

        key = _profile_key(parsed)
        cached = self._cache_get(key)
        if cached is not None:
            return _render(cached, raw=raw)

        payload = self._request("GET", f"/v1/users/{parsed}", allow_404=True)
        if payload is None:
            return None
        if not isinstance(payload, Mapping):
            raise RobloxAPIError("Unexpected Roblox response shape.", method="DECODE", path=f"/v1/users/{parsed}", body=payload)
        user = _decode_user(payload)
        if user.user_id is None:
            return None
        self._cache_set(key, user)
        return _render(user, raw=raw)

    def user(self, user_id: Any, *, raw: bool = False) -> RobloxUser | dict[str, Any] | None:
        return self.profile(user_id, raw=raw)

    def users(self, user_ids: Iterable[Any], *, raw: bool = False) -> dict[int, RobloxUser | dict[str, Any]]:
        ids = _unique_ids(user_ids)
        found: dict[int, RobloxUser] = {}
        missing: list[int] = []

        for item in ids:
            cached = self._cache_get(_minimal_key(item))
            if cached is None:
                missing.append(item)
            else:
                found[item] = cached

        if missing:
            payload = self._request("POST", "/v1/users", json={"userIds": missing, "excludeBannedUsers": False})
            for item in _data(payload, endpoint="/v1/users"):
                if not isinstance(item, Mapping):
                    continue
                user = _decode_user(item)
                if user.user_id is None:
                    continue
                self._cache_set(_minimal_key(user.user_id), user)
                found[user.user_id] = user

        return {item: _render(found[item], raw=raw) for item in ids if item in found}

    def username(self, user_id: Any) -> str | None:
        user = self.user(user_id)
        return user.name if isinstance(user, RobloxUser) else None

    def user_by_username(
        self,
        username: Any,
        *,
        exclude_banned_users: bool = False,
        raw: bool = False,
    ) -> RobloxUser | dict[str, Any] | None:
        parsed = _username(username)
        if parsed is None:
            return None
        return self.users_by_username([parsed], exclude_banned_users=exclude_banned_users, raw=raw).get(parsed)

    def users_by_username(
        self,
        usernames: Iterable[Any],
        *,
        exclude_banned_users: bool = False,
        raw: bool = False,
    ) -> dict[str, RobloxUser | dict[str, Any]]:
        names = _unique_usernames(usernames)
        found: dict[str, RobloxUser] = {}
        missing: list[str] = []

        for name in names:
            cached = self._cache_get(_username_key(name, exclude_banned_users=exclude_banned_users))
            if cached is None:
                missing.append(name)
            else:
                found[name] = cached

        if missing:
            payload = self._request(
                "POST",
                "/v1/usernames/users",
                json={"usernames": missing, "excludeBannedUsers": exclude_banned_users},
            )
            by_request: dict[str, RobloxUser] = {}
            for item in _data(payload, endpoint="/v1/usernames/users"):
                if not isinstance(item, Mapping):
                    continue
                user = _decode_user(item)
                requested = user.requested_username or user.name
                if requested is None:
                    continue
                by_request[requested.casefold()] = user

            for name in missing:
                matched = by_request.get(name.casefold())
                if matched is None:
                    continue
                self._cache_set(_username_key(name, exclude_banned_users=exclude_banned_users), matched)
                found[name] = matched

        return {name: _render(found[name], raw=raw) for name in names if name in found}


class AsyncRobloxClient(_BaseRobloxClient):
    """Async Roblox user/profile lookup helper."""

    def __init__(
        self,
        *,
        base_url: str = ROBLOX_USERS_BASE_URL,
        timeout_s: float = 10.0,
        ttl_s: float = 3600.0,
        user_agent: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._init_base(base_url=base_url, timeout_s=timeout_s, ttl_s=ttl_s, user_agent=user_agent)
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=timeout_s, headers=self._headers)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncRobloxClient:
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.close()

    async def _request(self, method: str, path: str, *, json: Any = None, allow_404: bool = False) -> Any:
        method_u = method.upper()
        try:
            resp = await self._client.request(
                method_u,
                self._url(path),
                json=json,
                headers=self._headers,
                timeout=self.timeout_s,
            )
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RequestError) as exc:
            raise RobloxNetworkError(f"Roblox network error: {exc}", method=method_u, path=path) from exc
        return _handle_response(resp, method=method_u, path=path, allow_404=allow_404)

    async def profile(self, user_id: Any, *, raw: bool = False) -> RobloxUser | dict[str, Any] | None:
        parsed = _user_id(user_id)
        if parsed is None:
            return None

        key = _profile_key(parsed)
        cached = self._cache_get(key)
        if cached is not None:
            return _render(cached, raw=raw)

        payload = await self._request("GET", f"/v1/users/{parsed}", allow_404=True)
        if payload is None:
            return None
        if not isinstance(payload, Mapping):
            raise RobloxAPIError("Unexpected Roblox response shape.", method="DECODE", path=f"/v1/users/{parsed}", body=payload)
        user = _decode_user(payload)
        if user.user_id is None:
            return None
        self._cache_set(key, user)
        return _render(user, raw=raw)

    async def user(self, user_id: Any, *, raw: bool = False) -> RobloxUser | dict[str, Any] | None:
        return await self.profile(user_id, raw=raw)

    async def users(self, user_ids: Iterable[Any], *, raw: bool = False) -> dict[int, RobloxUser | dict[str, Any]]:
        ids = _unique_ids(user_ids)
        found: dict[int, RobloxUser] = {}
        missing: list[int] = []

        for item in ids:
            cached = self._cache_get(_minimal_key(item))
            if cached is None:
                missing.append(item)
            else:
                found[item] = cached

        if missing:
            payload = await self._request("POST", "/v1/users", json={"userIds": missing, "excludeBannedUsers": False})
            for item in _data(payload, endpoint="/v1/users"):
                if not isinstance(item, Mapping):
                    continue
                user = _decode_user(item)
                if user.user_id is None:
                    continue
                self._cache_set(_minimal_key(user.user_id), user)
                found[user.user_id] = user

        return {item: _render(found[item], raw=raw) for item in ids if item in found}

    async def username(self, user_id: Any) -> str | None:
        user = await self.user(user_id)
        return user.name if isinstance(user, RobloxUser) else None

    async def user_by_username(
        self,
        username: Any,
        *,
        exclude_banned_users: bool = False,
        raw: bool = False,
    ) -> RobloxUser | dict[str, Any] | None:
        parsed = _username(username)
        if parsed is None:
            return None
        return (await self.users_by_username([parsed], exclude_banned_users=exclude_banned_users, raw=raw)).get(parsed)

    async def users_by_username(
        self,
        usernames: Iterable[Any],
        *,
        exclude_banned_users: bool = False,
        raw: bool = False,
    ) -> dict[str, RobloxUser | dict[str, Any]]:
        names = _unique_usernames(usernames)
        found: dict[str, RobloxUser] = {}
        missing: list[str] = []

        for name in names:
            cached = self._cache_get(_username_key(name, exclude_banned_users=exclude_banned_users))
            if cached is None:
                missing.append(name)
            else:
                found[name] = cached

        if missing:
            payload = await self._request(
                "POST",
                "/v1/usernames/users",
                json={"usernames": missing, "excludeBannedUsers": exclude_banned_users},
            )
            by_request: dict[str, RobloxUser] = {}
            for item in _data(payload, endpoint="/v1/usernames/users"):
                if not isinstance(item, Mapping):
                    continue
                user = _decode_user(item)
                requested = user.requested_username or user.name
                if requested is None:
                    continue
                by_request[requested.casefold()] = user

            for name in missing:
                matched = by_request.get(name.casefold())
                if matched is None:
                    continue
                self._cache_set(_username_key(name, exclude_banned_users=exclude_banned_users), matched)
                found[name] = matched

        return {name: _render(found[name], raw=raw) for name in names if name in found}


__all__ = [
    "AsyncRobloxClient",
    "ROBLOX_USERS_BASE_URL",
    "RobloxAPIError",
    "RobloxClient",
    "RobloxError",
    "RobloxNetworkError",
    "RobloxRateLimitError",
    "RobloxUser",
]
