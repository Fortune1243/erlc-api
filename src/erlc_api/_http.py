# src/erlc_api/_http.py
from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
import importlib.metadata as importlib_metadata
import logging
import random
import time
from datetime import timezone
from typing import Any, Callable, Mapping, Optional

import httpx

from ._cache import CacheBackend, CacheStats, InMemoryCacheBackend
from ._constants import (
    BASE_URL,
    DEFAULT_BACKOFF_BASE_S,
    DEFAULT_BACKOFF_CAP_S,
    DEFAULT_BACKOFF_JITTER_S,
    DEFAULT_CACHE_TTL_BY_PATH,
    DEFAULT_CIRCUIT_FAILURE_THRESHOLD,
    DEFAULT_CIRCUIT_OPEN_S,
    DEFAULT_ENABLE_CACHE,
    DEFAULT_ENABLE_CIRCUIT_BREAKER,
    DEFAULT_ENABLE_REQUEST_COALESCING,
    DEFAULT_MAX_RETRIES,
    DEFAULT_REQUEST_REPLAY_SIZE,
    DEFAULT_RETRY_429,
    DEFAULT_RETRY_5XX,
    DEFAULT_RETRY_NETWORK,
    DEFAULT_TIMEOUT_S,
)
from ._errors import (
    APIError,
    AuthError,
    CircuitOpenError,
    InvalidCommandError,
    NetworkError,
    NotFoundError,
    PermissionDeniedError,
    PlayerNotFoundError,
    RateLimitError,
    RobloxCommunicationError,
    ServerEmptyError,
)
from ._metrics import CommandMetric, MetricsSink, NoopMetricsSink, RequestMetric
from ._ratelimit import RateLimiter
from .context import fingerprint_key

logger = logging.getLogger(__name__)


def _default_user_agent() -> str:
    try:
        package_version = importlib_metadata.version("erlc-api")
    except importlib_metadata.PackageNotFoundError:
        package_version = "0+unknown"
    return f"erlc-api-python/{package_version}"


@dataclass
class ClientConfig:
    base_url: str = BASE_URL
    timeout_s: float = DEFAULT_TIMEOUT_S
    max_retries: int = DEFAULT_MAX_RETRIES
    backoff_base_s: float = DEFAULT_BACKOFF_BASE_S
    backoff_cap_s: float = DEFAULT_BACKOFF_CAP_S
    backoff_jitter_s: float = DEFAULT_BACKOFF_JITTER_S
    retry_429: bool = DEFAULT_RETRY_429
    retry_5xx: bool = DEFAULT_RETRY_5XX
    retry_network: bool = DEFAULT_RETRY_NETWORK
    user_agent: str = field(default_factory=_default_user_agent)

    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry_s: float = 30.0

    request_coalescing: bool = DEFAULT_ENABLE_REQUEST_COALESCING
    cache_enabled: bool = DEFAULT_ENABLE_CACHE
    cache_ttl_by_path: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_CACHE_TTL_BY_PATH))
    cache_backend: CacheBackend | None = None

    circuit_breaker_enabled: bool = DEFAULT_ENABLE_CIRCUIT_BREAKER
    circuit_failure_threshold: int = DEFAULT_CIRCUIT_FAILURE_THRESHOLD
    circuit_open_s: float = DEFAULT_CIRCUIT_OPEN_S

    metrics_sink: MetricsSink | None = None
    debug_dump: bool = False
    use_structlog: bool = False
    request_replay_size: int = DEFAULT_REQUEST_REPLAY_SIZE

    opentelemetry_tracing_enabled: bool = False
    json_dumps: Callable[[Any], str] | None = None


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


async def _sleep_backoff(attempt: int, base: float, cap: float, jitter: float) -> None:
    delay = min(cap, base * (2 ** (attempt - 1)))
    if jitter > 0:
        delay += random.uniform(0.0, jitter)
    await asyncio.sleep(delay)


def _parse_retry_after(resp: httpx.Response, raw: Any) -> float | None:
    retry_after_header = resp.headers.get("Retry-After")
    retry_header = _parse_float(retry_after_header)
    if retry_header is not None:
        return max(0.0, retry_header)
    if retry_after_header is not None:
        try:
            retry_at = parsedate_to_datetime(retry_after_header)
        except (TypeError, ValueError, IndexError, OverflowError):
            retry_at = None
        if retry_at is not None:
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(0.0, retry_at.timestamp() - time.time())
    if isinstance(raw, dict):
        candidate = raw.get("retry_after") or raw.get("retryAfter") or raw.get("retry")
        try:
            if candidate is None:
                return None
            return max(0.0, float(candidate))
        except (TypeError, ValueError):
            return None
    return None


def _body_text(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw.lower()
    if isinstance(raw, Mapping):
        candidate = raw.get("error") or raw.get("message") or raw.get("Message")
        if isinstance(candidate, str):
            return candidate.lower()
        return str(raw).lower()
    return str(raw).lower()


def _redact_headers(headers: Mapping[str, str]) -> dict[str, str]:
    safe = dict(headers)
    for key in list(safe.keys()):
        if key.lower() == "server-key":
            safe[key] = fingerprint_key(safe[key])
    return safe


def _safe_excerpt(raw: Any, *, limit: int = 250) -> str:
    text = str(raw)
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


class AsyncHTTP:
    def __init__(self, config: ClientConfig, limiter: RateLimiter):
        self.config = config
        self._limiter = limiter
        self._route_buckets: dict[tuple[str, str, str], str] = {}
        self._route_bucket_lock = asyncio.Lock()
        self._client: Optional[httpx.AsyncClient] = None
        self._start_lock = asyncio.Lock()

        self._cache: CacheBackend | None = None
        if self.config.cache_enabled:
            self._cache = self.config.cache_backend or InMemoryCacheBackend()

        self._metrics: MetricsSink = self.config.metrics_sink or NoopMetricsSink()
        self._cache_endpoint_stats: dict[str, dict[str, int]] = {}

        self._inflight: dict[str, asyncio.Future[Any]] = {}
        self._inflight_lock = asyncio.Lock()

        self._recent_requests: deque[dict[str, Any]] = deque(maxlen=max(1, self.config.request_replay_size))

        self._slogger: Any | None = None
        if self.config.use_structlog:
            try:
                import structlog

                self._slogger = structlog.get_logger(__name__)
            except Exception:
                self._slogger = None

        self._tracer: Any | None = None
        if self.config.opentelemetry_tracing_enabled:
            try:
                from opentelemetry import trace

                self._tracer = trace.get_tracer("erlc_api.http")
            except Exception:
                self._tracer = None

    async def start(self) -> None:
        async with self._start_lock:
            if self._client:
                return
            limits = httpx.Limits(
                max_connections=self.config.max_connections,
                max_keepalive_connections=self.config.max_keepalive_connections,
                keepalive_expiry=self.config.keepalive_expiry_s,
            )
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout_s,
                limits=limits,
                headers={"User-Agent": self.config.user_agent},
            )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
        self._client = None

        async with self._inflight_lock:
            for fut in self._inflight.values():
                if not fut.done():
                    fut.cancel()
            self._inflight.clear()

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

    @staticmethod
    def _normalize_params(params: Optional[Mapping[str, Any]]) -> str:
        if not params:
            return ""
        normalized = []
        for key, value in sorted(params.items(), key=lambda item: item[0]):
            normalized.append(f"{key}={value}")
        return "&".join(normalized)

    def _request_key(self, *, key_id: str, method: str, template: str, params: Optional[Mapping[str, Any]]) -> str:
        return f"{key_id}|{method}|{template}|{self._normalize_params(params)}"

    def _cache_ttl_for(self, template: str) -> float:
        return max(0.0, float(self.config.cache_ttl_by_path.get(template, 0.0)))

    def _should_cache(self, *, method: str, idempotent: bool, template: str) -> bool:
        if not idempotent or method != "GET":
            return False
        if self._cache is None:
            return False
        return self._cache_ttl_for(template) > 0.0

    def _cache_stat_bucket(self, endpoint: str) -> dict[str, int]:
        bucket = self._cache_endpoint_stats.get(endpoint)
        if bucket is not None:
            return bucket
        created = {"hit": 0, "miss": 0}
        self._cache_endpoint_stats[endpoint] = created
        return created

    def cache_stats(self) -> dict[str, Any]:
        endpoint_stats: dict[str, Any] = {}
        for endpoint, values in self._cache_endpoint_stats.items():
            reads = values["hit"] + values["miss"]
            endpoint_stats[endpoint] = {
                "hits": values["hit"],
                "misses": values["miss"],
                "hit_ratio": (values["hit"] / reads) if reads else 0.0,
            }

        backend_stats: CacheStats | None = self._cache.stats() if self._cache is not None else None
        return {
            "endpoints": endpoint_stats,
            "backend": backend_stats,
        }

    async def invalidate_cache(self, *, key_id: str, endpoint: str | None = None) -> None:
        if self._cache is None:
            return
        if endpoint:
            await self._cache.invalidate_prefix(f"{key_id}|GET|{endpoint}|")
            return
        await self._cache.invalidate_prefix(f"{key_id}|")

    async def clear_cache(self) -> None:
        if self._cache is None:
            return
        await self._cache.clear()

    def recent_requests(self, *, limit: int = 20) -> list[dict[str, Any]]:
        take = max(1, limit)
        return list(self._recent_requests)[-take:]

    def emit_command_metric(self, metric: CommandMetric) -> None:
        """Emit a command-level metric through the configured metrics sink."""
        self._metrics.on_command(metric)

    @staticmethod
    def _error_for_status(*, method: str, path: str, status: int, body: Any) -> APIError:
        message_body = _body_text(body)

        if status == 403:
            if "permission" in message_body or "denied" in message_body or "forbidden" in message_body:
                return PermissionDeniedError("Permission denied", method=method, path=path, status=status, body=body)
            return AuthError("Unauthorized or forbidden", method=method, path=path, status=status, body=body)

        if status == 404:
            if "player" in message_body and "not found" in message_body:
                return PlayerNotFoundError("Player not found", method=method, path=path, status=status, body=body)
            return NotFoundError("Not found", method=method, path=path, status=status, body=body)

        if status == 422 and "empty" in message_body and "server" in message_body:
            return ServerEmptyError("Server has no data for this request", method=method, path=path, status=status, body=body)

        if status in (400, 422) and "command" in message_body and ("invalid" in message_body or "syntax" in message_body):
            return InvalidCommandError("Invalid command", method=method, path=path, status=status, body=body)

        if status >= 500 and "roblox" in message_body:
            return RobloxCommunicationError(
                "Roblox backend communication error",
                method=method,
                path=path,
                status=status,
                body=body,
            )

        return APIError("Request failed", method=method, path=path, status=status, body=body)

    async def _execute_network_request(
        self,
        *,
        key_id: str,
        method_u: str,
        path: str,
        template: str,
        headers: Mapping[str, str],
        params: Optional[Mapping[str, Any]],
        json: Any,
        idempotent: bool,
    ) -> Any:
        key_fingerprint = fingerprint_key(headers.get("Server-Key", ""))
        retry_count = max(0, self.config.max_retries) if idempotent else 0
        max_attempts = 1 + retry_count

        for attempt in range(1, max_attempts + 1):
            bucket_guess = await self._resolve_bucket(key_id=key_id, method=method_u, path=template)
            circuit_retry_after = await self._limiter.pre_acquire(key_id=key_id, bucket=bucket_guess)
            if circuit_retry_after is not None:
                raise CircuitOpenError(
                    "Circuit breaker open for this rate-limit bucket",
                    method=method_u,
                    path=path,
                    bucket=bucket_guess,
                    retry_after=circuit_retry_after,
                )

            started_at = time.perf_counter()
            status_for_log: int | str = "ERR"
            bucket_for_outcome: str | None = bucket_guess

            try:
                request_headers = dict(headers)
                request_kwargs: dict[str, Any] = {
                    "method": method_u,
                    "url": path,
                    "headers": request_headers,
                    "params": params,
                }
                if json is not None and self.config.json_dumps is not None:
                    request_kwargs["content"] = self.config.json_dumps(json).encode("utf-8")
                    request_headers.setdefault("Content-Type", "application/json")
                else:
                    request_kwargs["json"] = json

                if self._tracer is not None:
                    with self._tracer.start_as_current_span(
                        "erlc_api.request",
                        attributes={
                            "erlc.method": method_u,
                            "erlc.path": template,
                            "erlc.key_id": key_id,
                            "erlc.attempt": attempt,
                        },
                    ):
                        resp = await self.client.request(**request_kwargs)
                else:
                    resp = await self.client.request(**request_kwargs)

                status_for_log = resp.status_code

                rl_bucket_header = resp.headers.get("X-RateLimit-Bucket")
                rl_bucket = rl_bucket_header or bucket_guess
                bucket_for_outcome = rl_bucket
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
                    await self._limiter.mark_success(key_id=key_id, bucket=rl_bucket)
                    if resp.headers.get("content-type", "").lower().startswith("application/json"):
                        return resp.json()
                    return resp.text

                raw = _safe_json(resp)

                if resp.status_code == 401:
                    await self._limiter.mark_failure(key_id=key_id, bucket=rl_bucket)
                    raise AuthError(
                        "Unauthorized",
                        method=method_u,
                        path=path,
                        status=resp.status_code,
                        body=raw,
                    )

                if resp.status_code == 429:
                    await self._limiter.mark_failure(key_id=key_id, bucket=rl_bucket)
                    retry_after_s = _parse_retry_after(resp, raw)
                    self._metrics.on_rate_limit_hit(endpoint=template, bucket=rl_bucket)

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

                    if self.config.retry_429 and attempt < max_attempts:
                        if retry_after_s is not None:
                            await asyncio.sleep(max(0.0, retry_after_s))
                            continue
                        if rl_reset is not None:
                            sleep_s = rl_reset - time.time()
                            if sleep_s > 0:
                                await asyncio.sleep(sleep_s)
                                continue
                        await _sleep_backoff(
                            attempt,
                            self.config.backoff_base_s,
                            self.config.backoff_cap_s,
                            self.config.backoff_jitter_s,
                        )
                        continue

                    raise err

                if resp.status_code >= 500:
                    await self._limiter.mark_failure(key_id=key_id, bucket=rl_bucket)
                    if idempotent and self.config.retry_5xx and attempt < max_attempts:
                        await _sleep_backoff(
                            attempt,
                            self.config.backoff_base_s,
                            self.config.backoff_cap_s,
                            self.config.backoff_jitter_s,
                        )
                        continue
                    raise self._error_for_status(method=method_u, path=path, status=resp.status_code, body=raw)

                await self._limiter.mark_success(key_id=key_id, bucket=rl_bucket)
                raise self._error_for_status(method=method_u, path=path, status=resp.status_code, body=raw)

            except (httpx.TimeoutException, httpx.NetworkError, httpx.RequestError) as e:
                status_for_log = "NETWORK_ERROR"
                await self._limiter.mark_failure(key_id=key_id, bucket=bucket_for_outcome)
                if idempotent and self.config.retry_network and attempt < max_attempts:
                    await _sleep_backoff(
                        attempt,
                        self.config.backoff_base_s,
                        self.config.backoff_cap_s,
                        self.config.backoff_jitter_s,
                    )
                    continue
                raise NetworkError(
                    f"Network error: {e!s}",
                    method=method_u,
                    path=path,
                    status=None,
                    body=None,
                ) from e
            finally:
                latency_ms = (time.perf_counter() - started_at) * 1000.0
                self._metrics.on_request(
                    RequestMetric(
                        endpoint=template,
                        method=method_u,
                        status=status_for_log if isinstance(status_for_log, int) else None,
                        latency_ms=latency_ms,
                        retries=attempt - 1,
                        key_id=key_id,
                        bucket=bucket_for_outcome,
                    )
                )

                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "ERLC request key=%s method=%s path=%s status=%s latency_ms=%.2f",
                        key_fingerprint,
                        method_u,
                        path,
                        status_for_log,
                        latency_ms,
                    )
                    if self.config.debug_dump:
                        logger.debug(
                            "ERLC request_dump method=%s path=%s headers=%s params=%s body=%s",
                            method_u,
                            path,
                            _redact_headers(headers),
                            params,
                            _safe_excerpt(json),
                        )

                if self._slogger is not None:
                    self._slogger.info(
                        "erlc_request",
                        key=key_fingerprint,
                        method=method_u,
                        path=path,
                        status=status_for_log,
                        latency_ms=round(latency_ms, 2),
                    )

                self._recent_requests.append(
                    {
                        "key": key_fingerprint,
                        "method": method_u,
                        "path": path,
                        "template": template,
                        "status": status_for_log,
                        "latency_ms": latency_ms,
                        "params": dict(params) if params else None,
                        "body_excerpt": _safe_excerpt(json) if json is not None else None,
                        "ts": time.time(),
                    }
                )

        raise APIError("Request failed after retries", method=method_u, path=path, status=None, body=None)

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

        request_key = self._request_key(key_id=key_id, method=method_u, template=template, params=params)
        should_cache = self._should_cache(method=method_u, idempotent=idempotent, template=template)

        if should_cache and self._cache is not None:
            cached = await self._cache.get(request_key)
            bucket = self._cache_stat_bucket(template)
            if cached is not None:
                bucket["hit"] += 1
                self._metrics.on_cache_hit(endpoint=template)
                return cached
            bucket["miss"] += 1
            self._metrics.on_cache_miss(endpoint=template)

        owner = False
        shared_future: asyncio.Future[Any] | None = None
        if idempotent and method_u == "GET" and self.config.request_coalescing:
            async with self._inflight_lock:
                existing = self._inflight.get(request_key)
                if existing is not None:
                    shared_future = existing
                else:
                    loop = asyncio.get_running_loop()
                    shared_future = loop.create_future()
                    shared_future.add_done_callback(lambda fut: fut.exception() if not fut.cancelled() else None)
                    self._inflight[request_key] = shared_future
                    owner = True

            if not owner and shared_future is not None:
                return await shared_future

        try:
            response = await self._execute_network_request(
                key_id=key_id,
                method_u=method_u,
                path=path,
                template=template,
                headers=headers,
                params=params,
                json=json,
                idempotent=idempotent,
            )

            if should_cache and self._cache is not None:
                await self._cache.set(request_key, response, self._cache_ttl_for(template))

            if owner and shared_future is not None and not shared_future.done():
                shared_future.set_result(response)
            return response
        except Exception as exc:
            if owner and shared_future is not None and not shared_future.done():
                shared_future.set_exception(exc)
            raise
        finally:
            if owner:
                async with self._inflight_lock:
                    current = self._inflight.get(request_key)
                    if current is shared_future:
                        self._inflight.pop(request_key, None)
