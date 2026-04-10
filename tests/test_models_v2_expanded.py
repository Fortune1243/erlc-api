from __future__ import annotations

from erlc_api.models import decode_v2_server_bundle


def test_decode_v2_bundle_parses_expanded_v2_fields() -> None:
    payload = {
        "Players": [
            {
                "Player": "Avi",
                "UserId": 10,
                "WantedStars": 3,
                "Location": {
                    "LocationX": 125.5,
                    "LocationZ": -99.25,
                    "PostalCode": "102",
                    "StreetName": "Main",
                    "BuildingNumber": "44A",
                },
            }
        ],
        "Staff": [{"Player": "AdminA", "Permission": "Admin"}],
        "Helpers": [{"Player": "HelperA", "Permission": "Helper"}],
        "Vehicles": [
            {
                "Owner": "Avi",
                "Model": "Falcon",
                "ColorHex": "#112233",
                "ColorName": "Navy",
            }
        ],
        "EmergencyCalls": [
            {
                "Team": "Police",
                "Caller": "CitizenA",
                "Position": [1, 2, 3],
                "StartedAt": 1700000000,
            }
        ],
    }

    result = decode_v2_server_bundle(payload)

    assert result.players is not None
    player = result.players[0]
    assert player.wanted_stars == 3
    assert player.location_typed is not None
    assert player.location_typed.location_x == 125.5
    assert player.location_typed.postal_code == "102"

    assert result.helpers is not None
    assert result.helpers[0].name == "HelperA"

    assert result.vehicles is not None
    assert result.vehicles[0].color_hex == "#112233"
    assert result.vehicles[0].color_name == "Navy"

    assert result.emergency_calls is not None
    call = result.emergency_calls[0]
    assert call.team == "Police"
    assert call.position == [1.0, 2.0, 3.0]
