from __future__ import annotations

import pytest

from erlc_api import ERLCClient
from erlc_api.models import Player, QueueEntry, V2ServerBundle
from erlc_api.utils.polling import poll_players, poll_queue, poll_server_default


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


def _queue(player: str, position: int) -> QueueEntry:
    return QueueEntry(player=player, position=position, timestamp=None, raw={}, extra={})


@pytest.mark.asyncio
async def test_poll_players_yields_diff_after_first_snapshot() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")
    responses = [[_player("Avi", 1)], [_player("Avi", 1), _player("Bee", 2)]]

    async def fake_players_typed(_ctx):
        return responses.pop(0)

    api.v1.players_typed = fake_players_typed  # type: ignore[method-assign]

    gen = poll_players(api, ctx, interval_s=0.001)
    first = await anext(gen)
    second = await anext(gen)
    await gen.aclose()

    assert first.previous is None
    assert first.diff is None
    assert second.diff is not None
    assert [item.name for item in second.diff.joined] == ["Bee"]


@pytest.mark.asyncio
async def test_poll_queue_yields_queue_diff() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")
    responses = [[_queue("Avi", 1)], [_queue("Avi", 2)]]

    async def fake_queue_typed(_ctx):
        return responses.pop(0)

    api.v1.queue_typed = fake_queue_typed  # type: ignore[method-assign]

    gen = poll_queue(api, ctx, interval_s=0.001)
    await anext(gen)
    second = await anext(gen)
    await gen.aclose()

    assert second.diff is not None
    assert len(second.diff.moved) == 1
    assert second.diff.moved[0].from_position == 1
    assert second.diff.moved[0].to_position == 2


@pytest.mark.asyncio
async def test_poll_server_default_yields_section_diffs() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")
    responses = [
        V2ServerBundle(
            players=[_player("Avi", 1)],
            staff=None,
            join_logs=None,
            queue=None,
            kill_logs=None,
            command_logs=None,
            mod_calls=None,
            vehicles=None,
            server_name=None,
            current_players=1,
            max_players=40,
            raw={},
            extra={},
        ),
        V2ServerBundle(
            players=[_player("Avi", 1), _player("Bee", 2)],
            staff=None,
            join_logs=None,
            queue=None,
            kill_logs=None,
            command_logs=None,
            mod_calls=None,
            vehicles=None,
            server_name=None,
            current_players=2,
            max_players=40,
            raw={},
            extra={},
        ),
    ]

    async def fake_server_default_typed(_ctx):
        return responses.pop(0)

    api.v2.server_default_typed = fake_server_default_typed  # type: ignore[method-assign]

    gen = poll_server_default(api, ctx, interval_s=0.001)
    await anext(gen)
    second = await anext(gen)
    await gen.aclose()

    assert second.diff is not None
    assert second.diff.players is not None
    assert [item.name for item in second.diff.players.joined] == ["Bee"]


@pytest.mark.asyncio
async def test_poll_players_validates_interval() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")
    gen = poll_players(api, ctx, interval_s=0)
    with pytest.raises(ValueError):
        await anext(gen)
