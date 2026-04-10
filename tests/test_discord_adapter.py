from __future__ import annotations

import asyncio

import pytest

from erlc_api import ERLCClient
from erlc_api.discord import (
    CommandLogEvent,
    ModCallEvent,
    PlayerJoinEvent,
    iter_command_log_events,
    iter_mod_call_events,
    iter_player_events,
)
from erlc_api.models import CommandLogEntry, ModCallEntry, Player
from erlc_api.utils.diff import PlayerDiff
from erlc_api.utils.polling import PollSnapshot


def _player(name: str, user_id: int) -> Player:
    return Player(
        name=name,
        user_id=user_id,
        permission=None,
        team=None,
        callsign=None,
        location=None,
        raw={},
        extra={},
    )


@pytest.mark.asyncio
async def test_iter_player_events_uses_diff_joined(monkeypatch: pytest.MonkeyPatch) -> None:
    first = [_player("Avi", 1)]
    second = [_player("Avi", 1), _player("Bee", 2)]

    async def fake_poll_players(*_args, **_kwargs):
        yield PollSnapshot(current=first, previous=None, diff=None, fetched_at_epoch=1.0)
        yield PollSnapshot(
            current=second,
            previous=first,
            diff=PlayerDiff(joined=[second[1]], left=[], stayed=[first[0]], previous_count=1, current_count=2),
            fetched_at_epoch=2.0,
        )

    monkeypatch.setattr("erlc_api.discord.poll_players", fake_poll_players)

    api = ERLCClient()
    ctx = api.ctx("abcd1234")
    events = [event async for event in iter_player_events(api, ctx, interval_s=0.001)]

    assert len(events) == 1
    assert isinstance(events[0], PlayerJoinEvent)
    assert events[0].player.name == "Bee"


@pytest.mark.asyncio
async def test_iter_mod_call_events_emits_new_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")
    responses = [
        [ModCallEntry(player="Avi", reason="RDM", location="Gas", timestamp=100, raw={}, extra={})],
        [
            ModCallEntry(player="Avi", reason="RDM", location="Gas", timestamp=100, raw={}, extra={}),
            ModCallEntry(player="Bee", reason="FRP", location="Bank", timestamp=120, raw={}, extra={}),
        ],
    ]

    async def fake_mod_calls_typed(_ctx):
        return responses.pop(0)

    async def fake_sleep(_seconds: float) -> None:
        return None

    api.v1.mod_calls_typed = fake_mod_calls_typed  # type: ignore[method-assign]
    monkeypatch.setattr("erlc_api.discord.asyncio.sleep", fake_sleep)

    gen = iter_mod_call_events(api, ctx, interval_s=0.001)
    event = await asyncio.wait_for(anext(gen), timeout=0.2)
    await gen.aclose()

    assert isinstance(event, ModCallEvent)
    assert event.entry.player == "Bee"


@pytest.mark.asyncio
async def test_iter_command_log_events_emits_new_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")
    responses = [
        [CommandLogEntry(player="Avi", command=":help", timestamp=100, raw={}, extra={})],
        [
            CommandLogEntry(player="Avi", command=":help", timestamp=100, raw={}, extra={}),
            CommandLogEntry(player="Bee", command=":log hi", timestamp=120, raw={}, extra={}),
        ],
    ]

    async def fake_command_logs_typed(_ctx):
        return responses.pop(0)

    async def fake_sleep(_seconds: float) -> None:
        return None

    api.v1.command_logs_typed = fake_command_logs_typed  # type: ignore[method-assign]
    monkeypatch.setattr("erlc_api.discord.asyncio.sleep", fake_sleep)

    gen = iter_command_log_events(api, ctx, interval_s=0.001)
    event = await asyncio.wait_for(anext(gen), timeout=0.2)
    await gen.aclose()

    assert isinstance(event, CommandLogEvent)
    assert event.entry.player == "Bee"
