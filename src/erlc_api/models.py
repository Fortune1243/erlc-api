from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from ._errors import ModelDecodeError


def _expect_mapping(payload: Any, *, endpoint: str) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise ModelDecodeError(
            f"Expected object payload for {endpoint}.",
            endpoint=endpoint,
            expected="object",
            payload=payload,
        )
    return payload


def _expect_list(payload: Any, *, endpoint: str) -> list[Any]:
    if not isinstance(payload, list):
        raise ModelDecodeError(
            f"Expected list payload for {endpoint}.",
            endpoint=endpoint,
            expected="list",
            payload=payload,
        )
    return payload


def _pick(raw: Mapping[str, Any], *keys: str) -> tuple[str | None, Any]:
    for key in keys:
        if key in raw:
            return key, raw[key]
    return None, None


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None
    return None


def _as_str(value: Any) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return None


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value
    return None


def _extra(raw: Mapping[str, Any], consumed: set[str]) -> dict[str, Any]:
    return {k: v for k, v in raw.items() if k not in consumed}


def _parse_list_items(
    payload: list[Any],
    parser: Any,
) -> list[Any]:
    parsed: list[Any] = []
    for item in payload:
        if isinstance(item, Mapping):
            parsed.append(parser(item))
    return parsed


def _epoch_to_datetime(value: int | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc)


@dataclass(frozen=True)
class CommandResponse:
    success: bool | None
    message: str | None
    raw: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ServerInfo:
    name: str | None
    owner: str | None
    co_owner: str | None
    current_players: int | None
    max_players: int | None
    join_key: str | None
    raw: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Player:
    name: str | None
    user_id: int | None
    permission: str | None
    team: str | None
    callsign: str | None
    location: Mapping[str, Any] | None
    raw: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StaffMember:
    name: str | None
    callsign: str | None
    permission: str | None
    raw: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QueueEntry:
    player: str | None
    position: int | None
    timestamp: int | None
    raw: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)

    @property
    def timestamp_datetime(self) -> datetime | None:
        return _epoch_to_datetime(self.timestamp)


@dataclass(frozen=True)
class JoinLogEntry:
    player: str | None
    timestamp: int | None
    raw: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)

    @property
    def timestamp_datetime(self) -> datetime | None:
        return _epoch_to_datetime(self.timestamp)


@dataclass(frozen=True)
class KillLogEntry:
    killer: str | None
    victim: str | None
    weapon: str | None
    timestamp: int | None
    raw: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)

    @property
    def timestamp_datetime(self) -> datetime | None:
        return _epoch_to_datetime(self.timestamp)


@dataclass(frozen=True)
class CommandLogEntry:
    player: str | None
    command: str | None
    timestamp: int | None
    raw: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)

    @property
    def timestamp_datetime(self) -> datetime | None:
        return _epoch_to_datetime(self.timestamp)


@dataclass(frozen=True)
class ModCallEntry:
    player: str | None
    reason: str | None
    location: str | None
    timestamp: int | None
    raw: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)

    @property
    def timestamp_datetime(self) -> datetime | None:
        return _epoch_to_datetime(self.timestamp)


@dataclass(frozen=True)
class Vehicle:
    owner: str | None
    model: str | None
    color: str | None
    plate: str | None
    team: str | None
    raw: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BanEntry:
    player: str | None
    reason: str | None
    banned_by: str | None
    timestamp: int | None
    expires_timestamp: int | None
    raw: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)

    @property
    def timestamp_datetime(self) -> datetime | None:
        return _epoch_to_datetime(self.timestamp)

    @property
    def expires_datetime(self) -> datetime | None:
        return _epoch_to_datetime(self.expires_timestamp)


@dataclass(frozen=True)
class V2ServerBundle:
    players: list[Player] | None
    staff: list[StaffMember] | None
    join_logs: list[JoinLogEntry] | None
    queue: list[QueueEntry] | None
    kill_logs: list[KillLogEntry] | None
    command_logs: list[CommandLogEntry] | None
    mod_calls: list[ModCallEntry] | None
    vehicles: list[Vehicle] | None
    server_name: str | None
    current_players: int | None
    max_players: int | None
    raw: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)


def _parse_command_response_item(raw: Mapping[str, Any]) -> CommandResponse:
    consumed: set[str] = set()
    key, success_value = _pick(raw, "Success", "success", "ok")
    if key:
        consumed.add(key)
    key, message_value = _pick(raw, "Message", "message", "error")
    if key:
        consumed.add(key)

    success: bool | None = success_value if isinstance(success_value, bool) else None
    message = _as_str(message_value)

    raw_dict = dict(raw)
    return CommandResponse(
        success=success,
        message=message,
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_server_info_item(raw: Mapping[str, Any]) -> ServerInfo:
    consumed: set[str] = set()

    key, name_value = _pick(raw, "Name", "ServerName", "name", "serverName")
    if key:
        consumed.add(key)
    key, owner_value = _pick(raw, "Owner", "owner")
    if key:
        consumed.add(key)
    key, co_owner_value = _pick(raw, "CoOwner", "Co-Owner", "coOwner", "co_owner")
    if key:
        consumed.add(key)
    key, current_players_value = _pick(
        raw,
        "CurrentPlayers",
        "Players",
        "playerCount",
        "current_players",
    )
    if key:
        consumed.add(key)
    key, max_players_value = _pick(raw, "MaxPlayers", "maxPlayers", "max_players")
    if key:
        consumed.add(key)
    key, join_key_value = _pick(raw, "JoinKey", "joinKey", "join_key")
    if key:
        consumed.add(key)

    raw_dict = dict(raw)
    return ServerInfo(
        name=_as_str(name_value),
        owner=_as_str(owner_value),
        co_owner=_as_str(co_owner_value),
        current_players=_as_int(current_players_value),
        max_players=_as_int(max_players_value),
        join_key=_as_str(join_key_value),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_player_item(raw: Mapping[str, Any]) -> Player:
    consumed: set[str] = set()

    key, name_value = _pick(raw, "Player", "Name", "Username", "player", "name", "username")
    if key:
        consumed.add(key)
    key, user_id_value = _pick(raw, "UserId", "PlayerId", "Id", "userId", "id")
    if key:
        consumed.add(key)
    key, permission_value = _pick(raw, "Permission", "permission", "Rank", "rank")
    if key:
        consumed.add(key)
    key, team_value = _pick(raw, "Team", "team")
    if key:
        consumed.add(key)
    key, callsign_value = _pick(raw, "Callsign", "callsign")
    if key:
        consumed.add(key)
    key, location_value = _pick(raw, "Location", "location")
    if key:
        consumed.add(key)

    raw_dict = dict(raw)
    return Player(
        name=_as_str(name_value),
        user_id=_as_int(user_id_value),
        permission=_as_str(permission_value),
        team=_as_str(team_value),
        callsign=_as_str(callsign_value),
        location=_as_mapping(location_value),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_staff_item(raw: Mapping[str, Any]) -> StaffMember:
    consumed: set[str] = set()
    key, name_value = _pick(raw, "Player", "Name", "Username", "player", "name", "username")
    if key:
        consumed.add(key)
    key, callsign_value = _pick(raw, "Callsign", "callsign")
    if key:
        consumed.add(key)
    key, permission_value = _pick(raw, "Permission", "permission", "Rank", "rank")
    if key:
        consumed.add(key)

    raw_dict = dict(raw)
    return StaffMember(
        name=_as_str(name_value),
        callsign=_as_str(callsign_value),
        permission=_as_str(permission_value),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_queue_item(raw: Mapping[str, Any]) -> QueueEntry:
    consumed: set[str] = set()
    key, player_value = _pick(raw, "Player", "player", "Name", "name")
    if key:
        consumed.add(key)
    key, position_value = _pick(raw, "Position", "QueuePosition", "position")
    if key:
        consumed.add(key)
    key, timestamp_value = _pick(raw, "Timestamp", "timestamp")
    if key:
        consumed.add(key)

    raw_dict = dict(raw)
    return QueueEntry(
        player=_as_str(player_value),
        position=_as_int(position_value),
        timestamp=_as_int(timestamp_value),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_join_log_item(raw: Mapping[str, Any]) -> JoinLogEntry:
    consumed: set[str] = set()
    key, player_value = _pick(raw, "Player", "player", "Name", "name")
    if key:
        consumed.add(key)
    key, timestamp_value = _pick(raw, "Timestamp", "timestamp")
    if key:
        consumed.add(key)

    raw_dict = dict(raw)
    return JoinLogEntry(
        player=_as_str(player_value),
        timestamp=_as_int(timestamp_value),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_kill_log_item(raw: Mapping[str, Any]) -> KillLogEntry:
    consumed: set[str] = set()
    key, killer_value = _pick(raw, "Killer", "killer")
    if key:
        consumed.add(key)
    key, victim_value = _pick(raw, "Victim", "victim")
    if key:
        consumed.add(key)
    key, weapon_value = _pick(raw, "Weapon", "weapon")
    if key:
        consumed.add(key)
    key, timestamp_value = _pick(raw, "Timestamp", "timestamp")
    if key:
        consumed.add(key)

    raw_dict = dict(raw)
    return KillLogEntry(
        killer=_as_str(killer_value),
        victim=_as_str(victim_value),
        weapon=_as_str(weapon_value),
        timestamp=_as_int(timestamp_value),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_command_log_item(raw: Mapping[str, Any]) -> CommandLogEntry:
    consumed: set[str] = set()
    key, player_value = _pick(raw, "Player", "player", "Name", "name")
    if key:
        consumed.add(key)
    key, command_value = _pick(raw, "Command", "command")
    if key:
        consumed.add(key)
    key, timestamp_value = _pick(raw, "Timestamp", "timestamp")
    if key:
        consumed.add(key)

    raw_dict = dict(raw)
    return CommandLogEntry(
        player=_as_str(player_value),
        command=_as_str(command_value),
        timestamp=_as_int(timestamp_value),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_mod_call_item(raw: Mapping[str, Any]) -> ModCallEntry:
    consumed: set[str] = set()
    key, player_value = _pick(raw, "Player", "Caller", "player", "caller")
    if key:
        consumed.add(key)
    key, reason_value = _pick(raw, "Reason", "reason")
    if key:
        consumed.add(key)
    key, location_value = _pick(raw, "Location", "location")
    if key:
        consumed.add(key)
    key, timestamp_value = _pick(raw, "Timestamp", "timestamp")
    if key:
        consumed.add(key)

    raw_dict = dict(raw)
    return ModCallEntry(
        player=_as_str(player_value),
        reason=_as_str(reason_value),
        location=_as_str(location_value),
        timestamp=_as_int(timestamp_value),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_vehicle_item(raw: Mapping[str, Any]) -> Vehicle:
    consumed: set[str] = set()
    key, owner_value = _pick(raw, "Owner", "owner", "Player", "player")
    if key:
        consumed.add(key)
    key, model_value = _pick(raw, "Model", "Vehicle", "model", "vehicle")
    if key:
        consumed.add(key)
    key, color_value = _pick(raw, "Color", "Colour", "color", "colour")
    if key:
        consumed.add(key)
    key, plate_value = _pick(raw, "Plate", "plate", "LicensePlate", "licensePlate")
    if key:
        consumed.add(key)
    key, team_value = _pick(raw, "Team", "team")
    if key:
        consumed.add(key)

    raw_dict = dict(raw)
    return Vehicle(
        owner=_as_str(owner_value),
        model=_as_str(model_value),
        color=_as_str(color_value),
        plate=_as_str(plate_value),
        team=_as_str(team_value),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_ban_item(raw: Mapping[str, Any]) -> BanEntry:
    consumed: set[str] = set()
    key, player_value = _pick(raw, "Player", "player", "Name", "name")
    if key:
        consumed.add(key)
    key, reason_value = _pick(raw, "Reason", "reason")
    if key:
        consumed.add(key)
    key, banned_by_value = _pick(raw, "BannedBy", "Moderator", "bannedBy", "moderator")
    if key:
        consumed.add(key)
    key, timestamp_value = _pick(raw, "Timestamp", "timestamp", "IssuedAt", "issuedAt")
    if key:
        consumed.add(key)
    key, expires_value = _pick(raw, "Expires", "ExpiresAt", "expires", "expiresAt")
    if key:
        consumed.add(key)

    raw_dict = dict(raw)
    return BanEntry(
        player=_as_str(player_value),
        reason=_as_str(reason_value),
        banned_by=_as_str(banned_by_value),
        timestamp=_as_int(timestamp_value),
        expires_timestamp=_as_int(expires_value),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def decode_command_response(payload: Any, *, endpoint: str = "/v1/server/command") -> CommandResponse:
    raw = _expect_mapping(payload, endpoint=endpoint)
    return _parse_command_response_item(raw)


def decode_server_info(payload: Any, *, endpoint: str = "/v1/server") -> ServerInfo:
    raw = _expect_mapping(payload, endpoint=endpoint)
    return _parse_server_info_item(raw)


def decode_players(payload: Any, *, endpoint: str = "/v1/server/players") -> list[Player]:
    raw_list = _expect_list(payload, endpoint=endpoint)
    return _parse_list_items(raw_list, _parse_player_item)


def decode_staff(payload: Any, *, endpoint: str = "/v1/server/staff") -> list[StaffMember]:
    raw_list = _expect_list(payload, endpoint=endpoint)
    return _parse_list_items(raw_list, _parse_staff_item)


def decode_queue(payload: Any, *, endpoint: str = "/v1/server/queue") -> list[QueueEntry]:
    raw_list = _expect_list(payload, endpoint=endpoint)
    return _parse_list_items(raw_list, _parse_queue_item)


def decode_join_logs(payload: Any, *, endpoint: str = "/v1/server/joinlogs") -> list[JoinLogEntry]:
    raw_list = _expect_list(payload, endpoint=endpoint)
    return _parse_list_items(raw_list, _parse_join_log_item)


def decode_kill_logs(payload: Any, *, endpoint: str = "/v1/server/killlogs") -> list[KillLogEntry]:
    raw_list = _expect_list(payload, endpoint=endpoint)
    return _parse_list_items(raw_list, _parse_kill_log_item)


def decode_command_logs(payload: Any, *, endpoint: str = "/v1/server/commandlogs") -> list[CommandLogEntry]:
    raw_list = _expect_list(payload, endpoint=endpoint)
    return _parse_list_items(raw_list, _parse_command_log_item)


def decode_mod_calls(payload: Any, *, endpoint: str = "/v1/server/modcalls") -> list[ModCallEntry]:
    raw_list = _expect_list(payload, endpoint=endpoint)
    return _parse_list_items(raw_list, _parse_mod_call_item)


def decode_vehicles(payload: Any, *, endpoint: str = "/v1/server/vehicles") -> list[Vehicle]:
    raw_list = _expect_list(payload, endpoint=endpoint)
    return _parse_list_items(raw_list, _parse_vehicle_item)


def decode_bans(payload: Any, *, endpoint: str = "/v1/server/bans") -> list[BanEntry]:
    raw_list = _expect_list(payload, endpoint=endpoint)
    return _parse_list_items(raw_list, _parse_ban_item)


def _extract_list_field(raw: Mapping[str, Any], consumed: set[str], *aliases: str) -> list[Any] | None:
    for alias in aliases:
        if alias in raw:
            consumed.add(alias)
            value = raw.get(alias)
            if isinstance(value, list):
                return value
            return None
    return None


def decode_v2_server_bundle(payload: Any, *, endpoint: str = "/v2/server") -> V2ServerBundle:
    raw = _expect_mapping(payload, endpoint=endpoint)
    consumed: set[str] = set()

    players_raw = _extract_list_field(raw, consumed, "Players", "players")
    staff_raw = _extract_list_field(raw, consumed, "Staff", "staff")
    join_logs_raw = _extract_list_field(raw, consumed, "JoinLogs", "join_logs", "joinLogs")
    queue_raw = _extract_list_field(raw, consumed, "Queue", "queue")
    kill_logs_raw = _extract_list_field(raw, consumed, "KillLogs", "kill_logs", "killLogs")
    command_logs_raw = _extract_list_field(raw, consumed, "CommandLogs", "command_logs", "commandLogs")
    mod_calls_raw = _extract_list_field(raw, consumed, "ModCalls", "mod_calls", "modCalls")
    vehicles_raw = _extract_list_field(raw, consumed, "Vehicles", "vehicles")

    key, server_name_value = _pick(raw, "ServerName", "Name", "serverName", "name")
    if key:
        consumed.add(key)
    key, current_players_value = _pick(raw, "CurrentPlayers", "currentPlayers")
    if key:
        consumed.add(key)
    key, max_players_value = _pick(raw, "MaxPlayers", "maxPlayers")
    if key:
        consumed.add(key)

    raw_dict = dict(raw)
    return V2ServerBundle(
        players=_parse_list_items(players_raw, _parse_player_item) if players_raw is not None else None,
        staff=_parse_list_items(staff_raw, _parse_staff_item) if staff_raw is not None else None,
        join_logs=_parse_list_items(join_logs_raw, _parse_join_log_item) if join_logs_raw is not None else None,
        queue=_parse_list_items(queue_raw, _parse_queue_item) if queue_raw is not None else None,
        kill_logs=_parse_list_items(kill_logs_raw, _parse_kill_log_item) if kill_logs_raw is not None else None,
        command_logs=_parse_list_items(command_logs_raw, _parse_command_log_item) if command_logs_raw is not None else None,
        mod_calls=_parse_list_items(mod_calls_raw, _parse_mod_call_item) if mod_calls_raw is not None else None,
        vehicles=_parse_list_items(vehicles_raw, _parse_vehicle_item) if vehicles_raw is not None else None,
        server_name=_as_str(server_name_value),
        current_players=_as_int(current_players_value),
        max_players=_as_int(max_players_value),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


__all__ = [
    "BanEntry",
    "CommandLogEntry",
    "CommandResponse",
    "JoinLogEntry",
    "KillLogEntry",
    "ModCallEntry",
    "Player",
    "QueueEntry",
    "ServerInfo",
    "StaffMember",
    "V2ServerBundle",
    "Vehicle",
    "decode_bans",
    "decode_command_logs",
    "decode_command_response",
    "decode_join_logs",
    "decode_kill_logs",
    "decode_mod_calls",
    "decode_players",
    "decode_queue",
    "decode_server_info",
    "decode_staff",
    "decode_v2_server_bundle",
    "decode_vehicles",
]
