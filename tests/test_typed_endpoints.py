from __future__ import annotations

import pytest

from erlc_api import ERLCClient, ModelDecodeError


@pytest.mark.asyncio
async def test_v1_players_typed_decodes_payload() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")

    async def fake_players(_ctx):
        return [{"Player": "Avi", "UserId": 101}]

    api.v1.players = fake_players  # type: ignore[method-assign]

    result = await api.v1.players_typed(ctx)

    assert [item.name for item in result] == ["Avi"]
    assert result[0].user_id == 101


@pytest.mark.asyncio
async def test_v1_command_typed_raises_decode_error_for_list_payload() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")

    async def fake_command(_ctx, _command):
        return ["not", "object"]

    api.v1.command = fake_command  # type: ignore[method-assign]

    with pytest.raises(ModelDecodeError):
        await api.v1.command_typed(ctx, ":help")


@pytest.mark.asyncio
async def test_v2_server_default_typed_decodes_bundle() -> None:
    api = ERLCClient()
    ctx = api.ctx("abcd1234")

    async def fake_server_default(_ctx):
        return {
            "Players": [{"Player": "Avi"}],
            "Queue": [{"Player": "Bee", "Position": 1}],
            "Staff": [{"Player": "Mod"}],
        }

    api.v2.server_default = fake_server_default  # type: ignore[method-assign]

    result = await api.v2.server_default_typed(ctx)

    assert result.players is not None and len(result.players) == 1
    assert result.queue is not None and len(result.queue) == 1
    assert result.staff is not None and len(result.staff) == 1
