from __future__ import annotations

from dataclasses import dataclass
from math import ceil


def _positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return int(value)


def _positive_float(value: float, name: str) -> float:
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return float(value)


@dataclass(frozen=True)
class PollPlan:
    interval_s: float
    timeout_s: float
    server_count: int = 1
    endpoint_count: int = 1

    def __post_init__(self) -> None:
        _positive_float(self.interval_s, "interval_s")
        _positive_float(self.timeout_s, "timeout_s")
        _positive_int(self.server_count, "server_count")
        _positive_int(self.endpoint_count, "endpoint_count")

    @property
    def polls(self) -> int:
        return max(1, ceil(self.timeout_s / self.interval_s))

    @property
    def estimated_requests(self) -> int:
        return self.polls * self.server_count * self.endpoint_count

    def to_dict(self) -> dict[str, float | int]:
        return {
            "interval_s": self.interval_s,
            "timeout_s": self.timeout_s,
            "server_count": self.server_count,
            "endpoint_count": self.endpoint_count,
            "polls": self.polls,
            "estimated_requests": self.estimated_requests,
        }

    def describe(self) -> str:
        return (
            f"Poll every {self.interval_s:g}s for up to {self.timeout_s:g}s "
            f"({self.estimated_requests} estimated requests)."
        )


def safe_interval(
    *,
    server_count: int = 1,
    endpoint_count: int = 1,
    base_interval_s: float = 2.0,
    min_interval_s: float = 2.0,
) -> float:
    """Return conservative polling guidance, not an official PRC rate limit."""

    servers = _positive_int(server_count, "server_count")
    endpoints = _positive_int(endpoint_count, "endpoint_count")
    base = _positive_float(base_interval_s, "base_interval_s")
    minimum = _positive_float(min_interval_s, "min_interval_s")
    return max(minimum, base * servers * endpoints)


def poll_plan(
    *,
    server_count: int = 1,
    endpoint_count: int = 1,
    timeout_s: float = 60.0,
    base_interval_s: float = 2.0,
    min_interval_s: float = 2.0,
) -> PollPlan:
    return PollPlan(
        interval_s=safe_interval(
            server_count=server_count,
            endpoint_count=endpoint_count,
            base_interval_s=base_interval_s,
            min_interval_s=min_interval_s,
        ),
        timeout_s=timeout_s,
        server_count=server_count,
        endpoint_count=endpoint_count,
    )


__all__ = ["PollPlan", "poll_plan", "safe_interval"]
