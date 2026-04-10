from __future__ import annotations

from typing import Any

try:
    from pydantic import AliasChoices, BaseModel, ConfigDict, Field
except Exception:  # pragma: no cover - optional dependency
    BaseModel = None  # type: ignore[assignment]
    AliasChoices = None  # type: ignore[assignment]
    ConfigDict = None  # type: ignore[assignment]
    Field = None  # type: ignore[assignment]


def _require_pydantic() -> None:
    if BaseModel is None:
        raise RuntimeError("Pydantic models require `pydantic>=2`. Install with `pip install erlc-api[pydantic]`.")


if BaseModel is not None:

    class _BaseValidatedModel(BaseModel):
        model_config = ConfigDict(extra="allow", populate_by_name=True)


    class PlayerLocationValidated(_BaseValidatedModel):
        location_x: float | None = Field(None, validation_alias=AliasChoices("LocationX", "locationX", "x"))
        location_z: float | None = Field(None, validation_alias=AliasChoices("LocationZ", "locationZ", "z"))
        postal_code: str | None = Field(
            None,
            validation_alias=AliasChoices("PostalCode", "postalCode", "postal_code"),
        )
        street_name: str | None = Field(
            None,
            validation_alias=AliasChoices("StreetName", "streetName", "street_name"),
        )
        building_number: str | None = Field(
            None,
            validation_alias=AliasChoices("BuildingNumber", "buildingNumber", "building_number"),
        )


    class PlayerValidated(_BaseValidatedModel):
        name: str | None = Field(
            None,
            validation_alias=AliasChoices("Player", "Name", "Username", "player", "name", "username"),
        )
        user_id: int | None = Field(None, validation_alias=AliasChoices("UserId", "PlayerId", "Id", "userId", "id"))
        permission: str | None = Field(None, validation_alias=AliasChoices("Permission", "permission", "Rank", "rank"))
        team: str | None = Field(None, validation_alias=AliasChoices("Team", "team"))
        callsign: str | None = Field(None, validation_alias=AliasChoices("Callsign", "callsign"))
        location: PlayerLocationValidated | None = Field(None, validation_alias=AliasChoices("Location", "location"))
        wanted_stars: int | None = Field(
            None,
            validation_alias=AliasChoices("WantedStars", "wantedStars", "wanted_stars"),
        )


    class StaffMemberValidated(_BaseValidatedModel):
        name: str | None = Field(
            None,
            validation_alias=AliasChoices("Player", "Name", "Username", "player", "name", "username"),
        )
        callsign: str | None = Field(None, validation_alias=AliasChoices("Callsign", "callsign"))
        permission: str | None = Field(None, validation_alias=AliasChoices("Permission", "permission", "Rank", "rank"))


    class QueueEntryValidated(_BaseValidatedModel):
        player: str | None = Field(None, validation_alias=AliasChoices("Player", "player", "Name", "name"))
        position: int | None = Field(None, validation_alias=AliasChoices("Position", "QueuePosition", "position"))
        timestamp: int | None = Field(None, validation_alias=AliasChoices("Timestamp", "timestamp"))


    class JoinLogValidated(_BaseValidatedModel):
        player: str | None = Field(None, validation_alias=AliasChoices("Player", "player", "Name", "name"))
        timestamp: int | None = Field(None, validation_alias=AliasChoices("Timestamp", "timestamp"))


    class KillLogValidated(_BaseValidatedModel):
        killer: str | None = Field(None, validation_alias=AliasChoices("Killer", "killer"))
        victim: str | None = Field(None, validation_alias=AliasChoices("Victim", "victim"))
        weapon: str | None = Field(None, validation_alias=AliasChoices("Weapon", "weapon"))
        timestamp: int | None = Field(None, validation_alias=AliasChoices("Timestamp", "timestamp"))


    class CommandLogValidated(_BaseValidatedModel):
        player: str | None = Field(None, validation_alias=AliasChoices("Player", "player", "Name", "name"))
        command: str | None = Field(None, validation_alias=AliasChoices("Command", "command"))
        timestamp: int | None = Field(None, validation_alias=AliasChoices("Timestamp", "timestamp"))


    class ModCallValidated(_BaseValidatedModel):
        player: str | None = Field(None, validation_alias=AliasChoices("Player", "Caller", "player", "caller"))
        reason: str | None = Field(None, validation_alias=AliasChoices("Reason", "reason"))
        location: str | None = Field(None, validation_alias=AliasChoices("Location", "location"))
        timestamp: int | None = Field(None, validation_alias=AliasChoices("Timestamp", "timestamp"))


    class VehicleValidated(_BaseValidatedModel):
        owner: str | None = Field(None, validation_alias=AliasChoices("Owner", "owner", "Player", "player"))
        model: str | None = Field(None, validation_alias=AliasChoices("Model", "Vehicle", "model", "vehicle"))
        color: str | None = Field(None, validation_alias=AliasChoices("Color", "Colour", "color", "colour"))
        color_hex: str | None = Field(None, validation_alias=AliasChoices("ColorHex", "colorHex", "color_hex"))
        color_name: str | None = Field(None, validation_alias=AliasChoices("ColorName", "colorName", "color_name"))
        plate: str | None = Field(None, validation_alias=AliasChoices("Plate", "plate", "LicensePlate", "licensePlate"))
        team: str | None = Field(None, validation_alias=AliasChoices("Team", "team"))


    class EmergencyCallValidated(_BaseValidatedModel):
        team: str | None = Field(None, validation_alias=AliasChoices("Team", "team"))
        caller: str | None = Field(None, validation_alias=AliasChoices("Caller", "caller", "Player", "player"))
        position: list[float] | None = Field(None, validation_alias=AliasChoices("Position", "position"))
        started_at: int | None = Field(
            None,
            validation_alias=AliasChoices("StartedAt", "startedAt", "Timestamp", "timestamp"),
        )


    class V2ServerBundleValidated(_BaseValidatedModel):
        players: list[PlayerValidated] | None = Field(None, validation_alias=AliasChoices("Players", "players"))
        staff: list[StaffMemberValidated] | None = Field(None, validation_alias=AliasChoices("Staff", "staff"))
        helpers: list[StaffMemberValidated] | None = Field(None, validation_alias=AliasChoices("Helpers", "helpers"))
        join_logs: list[JoinLogValidated] | None = Field(
            None,
            validation_alias=AliasChoices("JoinLogs", "join_logs", "joinLogs"),
        )
        queue: list[QueueEntryValidated] | None = Field(None, validation_alias=AliasChoices("Queue", "queue"))
        kill_logs: list[KillLogValidated] | None = Field(
            None,
            validation_alias=AliasChoices("KillLogs", "kill_logs", "killLogs"),
        )
        command_logs: list[CommandLogValidated] | None = Field(
            None,
            validation_alias=AliasChoices("CommandLogs", "command_logs", "commandLogs"),
        )
        mod_calls: list[ModCallValidated] | None = Field(
            None,
            validation_alias=AliasChoices("ModCalls", "mod_calls", "modCalls"),
        )
        vehicles: list[VehicleValidated] | None = Field(None, validation_alias=AliasChoices("Vehicles", "vehicles"))
        emergency_calls: list[EmergencyCallValidated] | None = Field(
            None,
            validation_alias=AliasChoices("EmergencyCalls", "emergencyCalls", "emergency_calls"),
        )
        server_name: str | None = Field(None, validation_alias=AliasChoices("ServerName", "Name", "serverName", "name"))
        current_players: int | None = Field(
            None,
            validation_alias=AliasChoices("CurrentPlayers", "currentPlayers"),
        )
        max_players: int | None = Field(None, validation_alias=AliasChoices("MaxPlayers", "maxPlayers"))


else:
    V2ServerBundleValidated = Any  # type: ignore[misc,assignment]


def decode_v2_server_bundle_validated(payload: Any, *, strict: bool = False) -> V2ServerBundleValidated:
    _require_pydantic()
    return V2ServerBundleValidated.model_validate(payload, strict=strict)  # type: ignore[union-attr]


__all__ = [
    "V2ServerBundleValidated",
    "decode_v2_server_bundle_validated",
]
