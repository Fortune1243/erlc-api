from __future__ import annotations

import pytest

from erlc_api import ERLCClient
from erlc_api.helpers import ParsedLogCommand, extract_log_commands, fetch_log_commands


def test_extract_log_commands_parses_valid_entries() -> None:
    entries = [
        {
            "Player": "Example:1",
            "Timestamp": 1704614400,
            "Command": ":log incident external-review-started",
        }
    ]

    result = extract_log_commands(entries)

    assert result == [
        ParsedLogCommand(
            player="Example:1",
            timestamp=1704614400,
            payload="incident external-review-started",
            raw_command=":log incident external-review-started",
            raw_entry=entries[0],
        )
    ]


def test_extract_log_commands_is_case_insensitive_and_trims_leading_whitespace() -> None:
    entries = [
        {
            "Player": "Example:1",
            "Timestamp": 1704614400,
            "Command": "   :LoG incident one",
        }
    ]

    result = extract_log_commands(entries)

    assert [item.payload for item in result] == ["incident one"]


def test_extract_log_commands_ignores_invalid_entries() -> None:
    entries = [
        {"Command": ":log"},
        {"Command": ":logger incident one"},
        {"Timestamp": 1704614400},
        {"Command": 123},
        {"Command": ":log    "},
    ]

    result = extract_log_commands(entries)

    assert result == []


def test_extract_log_commands_filters_by_payload_prefix() -> None:
    entries = [
        {"Command": ":log incident one"},
        {"Command": ":log review two"},
    ]

    result = extract_log_commands(entries, payload_prefix="incident")

    assert [item.payload for item in result] == ["incident one"]


@pytest.mark.asyncio
async def test_fetch_log_commands_calls_command_logs_once_and_parses() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")
    calls = 0

    async def fake_command_logs(_ctx):
        nonlocal calls
        calls += 1
        return [
            {
                "Player": "Example:1",
                "Timestamp": 1704614400,
                "Command": ":log incident one",
            },
            {"Command": ":h hello"},
        ]

    api.v1.command_logs = fake_command_logs  # type: ignore[method-assign]

    result = await fetch_log_commands(api, ctx)

    assert calls == 1
    assert [item.payload for item in result] == ["incident one"]


@pytest.mark.asyncio
async def test_fetch_log_commands_returns_empty_for_non_list_response() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")

    async def fake_command_logs(_ctx):
        return {"Command": ":log incident one"}

    api.v1.command_logs = fake_command_logs  # type: ignore[method-assign]

    result = await fetch_log_commands(api, ctx)

    assert result == []
