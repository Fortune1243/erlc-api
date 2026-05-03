from __future__ import annotations

import pytest

from erlc_api import AsyncERLC, ModelDecodeError, Player, ServerBundle, StaffList, cmd, normalize_command
from erlc_api.models import decode_server_bundle, parse_player_identifier
from erlc_api.utils import diff_players, diff_queue, filter_players, find_player
from erlc_api.web import compute_dashboard_metrics, players_to_dto, v2_bundle_to_dto


def test_command_normalization_accepts_colonless_plain_strings_and_builder() -> None:
    assert normalize_command("h hello") == ":h hello"
    assert normalize_command(":log test") == ":log test"
    assert str(cmd("pm", "Avi", "hello")) == ":pm Avi hello"
    assert str(cmd.h("hello")) == ":h hello"


def test_command_normalization_rejects_only_unsafe_shapes() -> None:
    with pytest.raises(ValueError):
        normalize_command("   ")
    with pytest.raises(ValueError):
        normalize_command("h hello\nbad")


def test_parse_player_identifier() -> None:
    assert parse_player_identifier("Avi:123") == ("Avi", 123)
    assert parse_player_identifier("Avi") == ("Avi", None)
    assert parse_player_identifier(123) == (None, 123)


def test_decode_server_bundle_preserves_unknown_fields_and_to_dict() -> None:
    bundle = decode_server_bundle(
        {
            "Name": "Server",
            "Players": [{"Player": "Avi:100", "ExtraField": "kept"}],
            "Queue": [100],
            "Mystery": "preserved",
        }
    )

    assert bundle.players is not None
    assert bundle.players[0].extra == {"ExtraField": "kept"}
    assert bundle.extra == {"Mystery": "preserved"}
    assert bundle.to_dict()["players"][0]["user_id"] == 100


def test_decode_server_bundle_raises_on_wrong_top_level_shape() -> None:
    with pytest.raises(ModelDecodeError):
        decode_server_bundle([])


def test_filters_finders_and_diffs() -> None:
    previous = [Player(name="Avi", user_id=1)]
    current = [Player(name="Avi", user_id=1), Player(name="Bee", user_id=2, team="Police")]

    assert filter_players(current, team="Police")[0].name == "Bee"
    assert find_player(current, 2).name == "Bee"  # type: ignore[union-attr]
    assert diff_players(previous, current).joined[0].name == "Bee"

    queue_diff = diff_queue([1, 2, 3], [2, 1, 4])
    assert queue_diff.joined == [4]
    assert queue_diff.left == [3]
    assert queue_diff.moved[0].item == 2


def test_web_dto_and_metrics_under_new_models() -> None:
    bundle = ServerBundle(
        name="Server",
        players=[Player(name="Avi", user_id=1, team="Police")],
        queue=[1, 2],
        staff=StaffList(admins={1: "Avi"}),
    )

    assert players_to_dto(bundle.players or [])[0]["name"] == "Avi"
    assert v2_bundle_to_dto(bundle)["name"] == "Server"
    metrics = compute_dashboard_metrics(bundle)
    assert metrics.player_count == 1
    assert metrics.staff_count == 1


@pytest.mark.asyncio
async def test_polling_uses_flat_client_methods() -> None:
    api = AsyncERLC("key")
    calls = 0

    async def fake_players(*, server_key=None, raw=False):  # noqa: ARG001
        nonlocal calls
        calls += 1
        if calls == 1:
            return [Player(name="Avi", user_id=1)]
        return [Player(name="Avi", user_id=1), Player(name="Bee", user_id=2)]

    api.players = fake_players  # type: ignore[method-assign]

    from erlc_api.utils import poll_players

    stream = poll_players(api, interval_s=0.01)
    first = await anext(stream)
    second = await anext(stream)
    await stream.aclose()

    assert first.diff is None
    assert second.diff is not None
    assert second.diff.joined[0].name == "Bee"

