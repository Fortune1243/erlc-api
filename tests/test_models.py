from __future__ import annotations

from datetime import timezone

import pytest

from erlc_api import ERLCError, ModelDecodeError
from erlc_api.models import (
    decode_command_logs,
    decode_players,
    decode_server_info,
    decode_v2_server_bundle,
)


def test_decode_players_parses_known_fields_and_preserves_extra() -> None:
    payload = [
        {
            "Player": "Avi",
            "UserId": "42",
            "Team": "Police",
            "Permission": "Moderator",
            "Callsign": "A-1",
            "UnknownFlag": True,
        }
    ]

    result = decode_players(payload)

    assert len(result) == 1
    player = result[0]
    assert player.name == "Avi"
    assert player.user_id == 42
    assert player.team == "Police"
    assert player.permission == "Moderator"
    assert player.callsign == "A-1"
    assert player.extra == {"UnknownFlag": True}


def test_decode_players_raises_on_top_level_shape_mismatch() -> None:
    with pytest.raises(ModelDecodeError):
        decode_players({"Player": "Avi"})


def test_decode_server_info_raises_on_top_level_shape_mismatch() -> None:
    with pytest.raises(ModelDecodeError):
        decode_server_info(["not", "an", "object"])


def test_decode_command_logs_skips_non_mapping_entries() -> None:
    payload = [
        {"Player": "Avi", "Command": ":help", "Timestamp": 1700000000},
        "bad-item",
    ]

    result = decode_command_logs(payload)

    assert len(result) == 1
    assert result[0].command == ":help"
    assert result[0].timestamp_datetime is not None
    assert result[0].timestamp_datetime.tzinfo == timezone.utc


def test_decode_v2_bundle_parses_present_sections() -> None:
    payload = {
        "Players": [{"Player": "Avi", "UserId": 1}],
        "Queue": [{"Player": "Bee", "Position": 2}],
        "Staff": [{"Player": "Mod", "Permission": "Admin"}],
        "ServerName": "Test Server",
        "CurrentPlayers": 12,
        "MaxPlayers": 40,
        "Unmapped": {"x": 1},
    }

    result = decode_v2_server_bundle(payload)

    assert result.server_name == "Test Server"
    assert result.current_players == 12
    assert result.max_players == 40
    assert result.players is not None and result.players[0].name == "Avi"
    assert result.queue is not None and result.queue[0].position == 2
    assert result.staff is not None and result.staff[0].permission == "Admin"
    assert result.extra == {"Unmapped": {"x": 1}}


def test_model_decode_error_is_erlc_error() -> None:
    with pytest.raises(ERLCError):
        decode_players("bad")
