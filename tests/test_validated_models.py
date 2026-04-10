from __future__ import annotations

import pytest

from erlc_api.validated import decode_v2_server_bundle_validated


def test_decode_v2_validated_optional_dependency_behavior() -> None:
    payload = {
        "Players": [
            {
                "Player": "Avi",
                "UserId": "42",
            }
        ]
    }

    try:
        import pydantic  # noqa: F401
    except Exception:
        with pytest.raises(RuntimeError):
            decode_v2_server_bundle_validated(payload, strict=False)
        return

    model = decode_v2_server_bundle_validated(payload, strict=False)
    assert model.players is not None
    assert model.players[0].user_id == 42

    with pytest.raises(Exception):
        decode_v2_server_bundle_validated(payload, strict=True)
