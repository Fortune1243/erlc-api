# src/erlc_api/_http.py
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Mapping, Optional

import httpx

from ._constants import BASE_URL, DEFAULT_TIMEOUT_S, DEFAULT_MAX_RETRIES, DEFAULT_BACKOFF_BASE_S, DEFAULT_BACKOFF_CAP_S
from ._errors import APIError, AuthError, NetworkError, NotFoundError, RateLimitError
from .context import fingerprint_key
from ._ratelimit import RateLimiter

logger = logging.getLogger(__name__)


@dataclass
class ClientConfig:
    base_url: str = BASE_URL
    timeout_s: float = DEFAULT_TIMEOUT_S
    max_retries: int = DEFAULT_MAX_RETRIES
    backoff_base_s: float = DEFAULT_BACKOFF_BASE_S
    backoff_cap_s: float = DEFAULT_BACKOFF_CAP_S
    user_agent: str = "erlc-api-python/1.0.1"

def _parse_int(v: Optional[str]) -> Optional[int]:
    try:
        return int(v) if v is not None else None
    except ValueError:
        return None

def _parse_float(v: Optional[str]) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except ValueError:
        return None

def _safe_json(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return resp.text


async def _sleep_backoff(attempt: int, base: float, cap: float) -> None:
    delay = min(cap, base * (2 ** (attempt - 1)))
    await asyncio.sleep(delay)


def _parse_retry_after(resp: httpx.Response, raw: Any) -> float | None:
    retry_header = _parse_float(resp.headers.get("Retry-After"))
    if retry_header is not None:
        return max(0.0, retry_header)
    if isinstance(raw, dict):
        candidate = raw.get("retry_after") or raw.get("retryAfter") or raw.get("retry")
        try:
            if candidate is None:
                return None
            return max(0.0, float(candidate))
        except (TypeError, ValueError):
            return None
    return None

class AsyncHTTP:
    def __init__(self, config: ClientConfig, limiter: RateLimiter):
        self.config = config
        self._limiter = limiter
        self._route_buckets: dict[tuple[str, str, str], str] = {}
        self._route_bucket_lock = asyncio.Lock()
        self._client: Optional[httpx.AsyncClient] = None
        self._start_lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._start_lock:
            if self._client:
                return
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout_s,
                headers={"User-Agent": self.config.user_agent},
            )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError("HTTP client not started. Call await start() first.")
        return self._client

    @staticmethod
    def _bucket_fallback(method: str, path: str) -> str:
        return f"fallback:{method}:{path}"

    async def _resolve_bucket(self, *, key_id: str, method: str, path: str) -> str:
        route_key = (key_id, method, path)
        async with self._route_bucket_lock:
            existing = self._route_buckets.get(route_key)
        if existing:
            return existing
        return self._bucket_fallback(method, path)

    async def _remember_bucket(self, *, key_id: str, method: str, path: str, bucket: str) -> None:
        route_key = (key_id, method, path)
        async with self._route_bucket_lock:
            self._route_buckets[route_key] = bucket

    async def request(
        self,
        *,
        key_id: str,
        method: str,
        path: str,
        path_template: Optional[str] = None,
        headers: Mapping[str, str],
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        idempotent: bool = True,
    ) -> Any:
        method_u = method.upper()
        template = path_template or path
        key_fingerprint = fingerprint_key(headers.get("Server-Key", ""))

        # Non idempotent calls should not be retried on network or 5xx.
        max_attempts = self.config.max_retries if idempotent else 1

        for attempt in range(1, max_attempts + 1):
            bucket_guess = await self._resolve_bucket(key_id=key_id, method=method_u, path=template)
            await self._limiter.pre_acquire(key_id=key_id, bucket=bucket_guess)
            started_at = time.perf_counter()
            status_for_log: int | str = "ERR"

            try:
                resp = await self.client.request(
                    method_u,
                    path,
                    headers=dict(headers),
                    params=params,
                    json=json,
                )
                status_for_log = resp.status_code

                rl_bucket_header = resp.headers.get("X-RateLimit-Bucket")
                rl_bucket = rl_bucket_header or bucket_guess
                rl_limit = _parse_int(resp.headers.get("X-RateLimit-Limit"))
                rl_remaining = _parse_int(resp.headers.get("X-RateLimit-Remaining"))
                rl_reset = _parse_float(resp.headers.get("X-RateLimit-Reset"))

                if rl_bucket_header:
                    await self._remember_bucket(key_id=key_id, method=method_u, path=template, bucket=rl_bucket_header)

                await self._limiter.update_from_headers(
                    key_id=key_id,
                    bucket=rl_bucket,
                    limit=rl_limit,
                    remaining=rl_remaining,
                    reset_epoch_s=rl_reset,
                )

                if 200 <= resp.status_code < 300:
                    if resp.headers.get("content-type", "").lower().startswith("application/json"):
                        return resp.json()
                    return resp.text

                raw = _safe_json(resp)

                if resp.status_code in (401, 403):
                    raise AuthError(
                        "Unauthorized or forbidden",
                        method=method_u,
                        path=path,
                        status=resp.status_code,
                        body=raw,
                    )
                if resp.status_code == 404:
                    raise NotFoundError(
                        "Not found",
                        method=method_u,
                        path=path,
                        status=404,
                        body=raw,
                    )

                if resp.status_code == 429:
                    retry_after_s = _parse_retry_after(resp, raw)

                    err = RateLimitError(
                        "Rate limited",
                        method=method_u,
                        path=path,
                        status=429,
                        body=raw,
                        bucket=rl_bucket,
                        retry_after=retry_after_s,
                        reset_epoch_s=rl_reset,
                    )

                    # 429 is safe to retry because the server rejected the request.
                    if attempt < self.config.max_retries:
                        if retry_after_s is not None:
                            await asyncio.sleep(max(0.0, retry_after_s))
                            continue
                        if rl_reset is not None:
                            sleep_s = rl_reset - time.time()
                            if sleep_s > 0:
                                await asyncio.sleep(sleep_s)
                                continue
                        await _sleep_backoff(attempt, self.config.backoff_base_s, self.config.backoff_cap_s)
                        continue

                    raise err

                if resp.status_code >= 500 and idempotent and attempt < max_attempts:
                    await _sleep_backoff(attempt, self.config.backoff_base_s, self.config.backoff_cap_s)
                    continue

                raise APIError(
                    "Request failed",
                    method=method_u,
                    path=path,
                    status=resp.status_code,
                    body=raw,
                )

            except (httpx.TimeoutException, httpx.NetworkError, httpx.RequestError) as e:
                status_for_log = "NETWORK_ERROR"
                if idempotent and attempt < max_attempts:
                    await _sleep_backoff(attempt, self.config.backoff_base_s, self.config.backoff_cap_s)
                    continue
                raise NetworkError(
                    f"Network error: {e!s}",
                    method=method_u,
                    path=path,
                    status=None,
                    body=None,
                ) from e
            finally:
                if logger.isEnabledFor(logging.DEBUG):
                    latency_ms = (time.perf_counter() - started_at) * 1000.0
                    logger.debug(
                        "ERLC request key=%s method=%s path=%s status=%s latency_ms=%.2f",
                        key_fingerprint,
                        method_u,
                        path,
                        status_for_log,
                        latency_ms,
                    )

        raise APIError("Request failed after retries", method=method_u, path=path, status=None, body=None)
