from __future__ import annotations

import time

import pytest

from erlc_api import ERLCClient
from erlc_api.commands import CommandBuilder


@pytest.mark.asyncio
async def test_v1_command_supports_dry_run() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")

    payload = await api.v1.command(ctx, CommandBuilder.pm(target="Bee", message="Hello"), dry_run=True)

    assert payload["Success"] is True
    assert payload["DryRun"] is True


@pytest.mark.asyncio
async def test_v1_command_with_tracking_correlates_log_entries() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")
    now = int(time.time())

    async def fake_request(_ctx, method, path, **_kwargs):
        if method == "POST" and path == "/v1/server/command":
            return {"Success": True, "Message": "Executed"}
        if method == "GET" and path == "/v1/server/commandlogs":
            return [{"Player": "Avi", "Command": ":pm Bee Hello", "Timestamp": now}]
        raise AssertionError(f"unexpected request {method} {path}")

    api.v1._request = fake_request  # type: ignore[method-assign]

    result = await api.v1.command_with_tracking(
        ctx,
        CommandBuilder.pm(target="Bee", message="Hello"),
        timeout_s=0.2,
        poll_interval_s=0.01,
    )

    assert result.inferred_success is True
    assert result.correlated_log_entry is not None
    assert result.timed_out_waiting_for_log is False


@pytest.mark.asyncio
async def test_v1_command_logs_stream_yields_new_entries() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")

    async def fake_command_logs_typed(_ctx):
        return [
            type("E", (), {"timestamp": 1700000000, "player": "Avi", "command": ":help"})(),
        ]

    api.v1.command_logs_typed = fake_command_logs_typed  # type: ignore[method-assign]

    agen = api.v1.command_logs_stream(ctx, since_timestamp=1700000000, poll_interval_s=0.01)
    first = await anext(agen)
    await agen.aclose()

    assert first.command == ":help"
