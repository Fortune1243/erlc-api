from __future__ import annotations

import time

import pytest

from erlc_api import ERLCClient
from erlc_api._http import ClientConfig


class _CaptureMetricsSink:
    def __init__(self) -> None:
        self.command_metrics = []

    def on_request(self, metric) -> None:  # noqa: ANN001
        return

    def on_rate_limit_hit(self, *, endpoint: str, bucket: str | None) -> None:  # noqa: ARG002
        return

    def on_cache_hit(self, *, endpoint: str) -> None:  # noqa: ARG002
        return

    def on_cache_miss(self, *, endpoint: str) -> None:  # noqa: ARG002
        return

    def on_command(self, metric) -> None:  # noqa: ANN001
        self.command_metrics.append(metric)


@pytest.mark.asyncio
async def test_command_emits_command_metric() -> None:
    sink = _CaptureMetricsSink()
    api = ERLCClient(config=ClientConfig(metrics_sink=sink))
    ctx = api.ctx("abcd1234")

    async def fake_request(_ctx, method, path, **_kwargs):
        if method == "POST" and path == "/v1/server/command":
            return {"Success": True, "Message": "Executed"}
        raise AssertionError(f"unexpected request {method} {path}")

    api.v1._request = fake_request  # type: ignore[method-assign]

    await api.v1.command(ctx, ":help")

    assert len(sink.command_metrics) == 1
    metric = sink.command_metrics[0]
    assert metric.command == ":help"
    assert metric.inferred_success is True
    assert metric.timed_out is False
    assert metric.correlated_with_log is False


@pytest.mark.asyncio
async def test_send_command_emits_command_metric() -> None:
    sink = _CaptureMetricsSink()
    api = ERLCClient(config=ClientConfig(metrics_sink=sink))
    ctx = api.ctx("abcd1234")

    async def fake_request(_ctx, method, path, **_kwargs):
        if method == "POST" and path == "/v1/server/command":
            return {"Success": True, "Message": "Done"}
        raise AssertionError(f"unexpected request {method} {path}")

    api.v1._request = fake_request  # type: ignore[method-assign]

    await api.v1.send_command(ctx, ":h hi")

    assert len(sink.command_metrics) == 1
    assert sink.command_metrics[0].command == ":h hi"


@pytest.mark.asyncio
async def test_command_with_tracking_emits_single_correlated_metric() -> None:
    sink = _CaptureMetricsSink()
    api = ERLCClient(config=ClientConfig(metrics_sink=sink))
    ctx = api.ctx("abcd1234")
    now = int(time.time())

    async def fake_request(_ctx, method, path, **_kwargs):
        if method == "POST" and path == "/v1/server/command":
            return {"Success": True, "Message": "Executed"}
        if method == "GET" and path == "/v1/server/commandlogs":
            return [{"Player": "Avi", "Command": ":help", "Timestamp": now}]
        raise AssertionError(f"unexpected request {method} {path}")

    api.v1._request = fake_request  # type: ignore[method-assign]

    result = await api.v1.command_with_tracking(ctx, ":help", timeout_s=0.2, poll_interval_s=0.01)

    assert result.correlated_log_entry is not None
    assert len(sink.command_metrics) == 1
    metric = sink.command_metrics[0]
    assert metric.command == ":help"
    assert metric.correlated_with_log is True
    assert metric.timed_out is False


@pytest.mark.asyncio
async def test_command_with_tracking_timeout_metric() -> None:
    sink = _CaptureMetricsSink()
    api = ERLCClient(config=ClientConfig(metrics_sink=sink))
    ctx = api.ctx("abcd1234")

    async def fake_request(_ctx, method, path, **_kwargs):
        if method == "POST" and path == "/v1/server/command":
            return {"Success": True, "Message": "Executed"}
        if method == "GET" and path == "/v1/server/commandlogs":
            return []
        raise AssertionError(f"unexpected request {method} {path}")

    api.v1._request = fake_request  # type: ignore[method-assign]

    result = await api.v1.command_with_tracking(ctx, ":help", timeout_s=0.05, poll_interval_s=0.01)

    assert result.timed_out_waiting_for_log is True
    assert len(sink.command_metrics) == 1
    metric = sink.command_metrics[0]
    assert metric.timed_out is True
    assert metric.correlated_with_log is False
