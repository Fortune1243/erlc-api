from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RequestMetric:
    endpoint: str
    method: str
    status: int | None
    latency_ms: float
    retries: int
    key_id: str
    bucket: str | None
    from_cache: bool = False
    coalesced: bool = False


@dataclass(frozen=True)
class CommandMetric:
    command: str
    inferred_success: bool | None
    timed_out: bool
    correlated_with_log: bool


class MetricsSink(Protocol):
    def on_request(self, metric: RequestMetric) -> None: ...

    def on_rate_limit_hit(self, *, endpoint: str, bucket: str | None) -> None: ...

    def on_cache_hit(self, *, endpoint: str) -> None: ...

    def on_cache_miss(self, *, endpoint: str) -> None: ...

    def on_command(self, metric: CommandMetric) -> None: ...


class NoopMetricsSink:
    def on_request(self, metric: RequestMetric) -> None:  # noqa: ARG002
        return

    def on_rate_limit_hit(self, *, endpoint: str, bucket: str | None) -> None:  # noqa: ARG002
        return

    def on_cache_hit(self, *, endpoint: str) -> None:  # noqa: ARG002
        return

    def on_cache_miss(self, *, endpoint: str) -> None:  # noqa: ARG002
        return

    def on_command(self, metric: CommandMetric) -> None:  # noqa: ARG002
        return


@dataclass(frozen=True)
class EndpointStats:
    requests: int = 0
    errors: int = 0
    total_latency_ms: float = 0.0
    rate_limit_hits: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    @property
    def avg_latency_ms(self) -> float:
        if self.requests == 0:
            return 0.0
        return self.total_latency_ms / self.requests

    @property
    def cache_hit_ratio(self) -> float:
        reads = self.cache_hits + self.cache_misses
        if reads == 0:
            return 0.0
        return self.cache_hits / reads


class InMemoryMetricsSink:
    def __init__(self) -> None:
        self._endpoint: dict[str, EndpointStats] = {}
        self._commands_total = 0
        self._commands_success = 0
        self._commands_failure = 0
        self._commands_unknown = 0

    def _get(self, endpoint: str) -> EndpointStats:
        existing = self._endpoint.get(endpoint)
        if existing is not None:
            return existing
        created = EndpointStats()
        self._endpoint[endpoint] = created
        return created

    def on_request(self, metric: RequestMetric) -> None:
        current = self._get(metric.endpoint)
        self._endpoint[metric.endpoint] = EndpointStats(
            requests=current.requests + 1,
            errors=current.errors + (1 if metric.status is None or metric.status >= 400 else 0),
            total_latency_ms=current.total_latency_ms + metric.latency_ms,
            rate_limit_hits=current.rate_limit_hits,
            cache_hits=current.cache_hits,
            cache_misses=current.cache_misses,
        )

    def on_rate_limit_hit(self, *, endpoint: str, bucket: str | None) -> None:  # noqa: ARG002
        current = self._get(endpoint)
        self._endpoint[endpoint] = EndpointStats(
            requests=current.requests,
            errors=current.errors,
            total_latency_ms=current.total_latency_ms,
            rate_limit_hits=current.rate_limit_hits + 1,
            cache_hits=current.cache_hits,
            cache_misses=current.cache_misses,
        )

    def on_cache_hit(self, *, endpoint: str) -> None:
        current = self._get(endpoint)
        self._endpoint[endpoint] = EndpointStats(
            requests=current.requests,
            errors=current.errors,
            total_latency_ms=current.total_latency_ms,
            rate_limit_hits=current.rate_limit_hits,
            cache_hits=current.cache_hits + 1,
            cache_misses=current.cache_misses,
        )

    def on_cache_miss(self, *, endpoint: str) -> None:
        current = self._get(endpoint)
        self._endpoint[endpoint] = EndpointStats(
            requests=current.requests,
            errors=current.errors,
            total_latency_ms=current.total_latency_ms,
            rate_limit_hits=current.rate_limit_hits,
            cache_hits=current.cache_hits,
            cache_misses=current.cache_misses + 1,
        )

    def on_command(self, metric: CommandMetric) -> None:
        self._commands_total += 1
        if metric.inferred_success is True:
            self._commands_success += 1
            return
        if metric.inferred_success is False:
            self._commands_failure += 1
            return
        self._commands_unknown += 1

    def endpoint_stats(self) -> dict[str, EndpointStats]:
        return dict(self._endpoint)

    def command_stats(self) -> dict[str, int]:
        return {
            "total": self._commands_total,
            "success": self._commands_success,
            "failure": self._commands_failure,
            "unknown": self._commands_unknown,
        }


__all__ = [
    "CommandMetric",
    "EndpointStats",
    "InMemoryMetricsSink",
    "MetricsSink",
    "NoopMetricsSink",
    "RequestMetric",
]
