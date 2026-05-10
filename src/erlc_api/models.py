from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import IntEnum
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


def _extra(raw: Mapping[str, Any], consumed: set[str]) -> dict[str, Any]:
    return {key: value for key, value in raw.items() if key not in consumed}


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return str(value)


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
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


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "yes", "1"}:
            return True
        if text in {"false", "no", "0"}:
            return False
    return None


def _as_int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    out: list[int] = []
    for item in value:
        parsed = _as_int(item)
        if parsed is not None:
            out.append(parsed)
    return out


def _as_float_list(value: Any) -> list[float]:
    if not isinstance(value, list):
        return []
    out: list[float] = []
    for item in value:
        parsed = _as_float(item)
        if parsed is not None:
            out.append(parsed)
    return out


def _as_str_int_map(value: Any) -> dict[int, str]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[int, str] = {}
    for key, item in value.items():
        parsed_key = _as_int(key)
        parsed_value = _as_str(item)
        if parsed_key is None or parsed_value is None:
            continue
        out[parsed_key] = parsed_value
    return out


def parse_player_identifier(value: Any) -> tuple[str | None, int | None]:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return None, _as_int(value)
    text = _as_str(value)
    if text is None:
        return None, _as_int(value)
    if ":" not in text:
        return text, None
    name, raw_id = text.rsplit(":", 1)
    parsed_id = _as_int(raw_id)
    return (name.strip() or None), parsed_id


def _normalize_label(value: Any) -> str:
    return " ".join(str(value or "").replace("_", " ").replace("-", " ").casefold().split())


class PermissionLevel(IntEnum):
    NORMAL = 0
    HELPER = 1
    MOD = 2
    ADMIN = 3
    CO_OWNER = 4
    OWNER = 5

    @classmethod
    def parse(cls, value: Any) -> PermissionLevel:
        if isinstance(value, PermissionLevel):
            return value
        text = _normalize_label(value)
        aliases = {
            "": cls.NORMAL,
            "normal": cls.NORMAL,
            "server helper": cls.HELPER,
            "helper": cls.HELPER,
            "server moderator": cls.MOD,
            "moderator": cls.MOD,
            "mod": cls.MOD,
            "server administrator": cls.ADMIN,
            "administrator": cls.ADMIN,
            "admin": cls.ADMIN,
            "server co owner": cls.CO_OWNER,
            "server coowner": cls.CO_OWNER,
            "co owner": cls.CO_OWNER,
            "coowner": cls.CO_OWNER,
            "server owner": cls.OWNER,
            "owner": cls.OWNER,
        }
        return aliases.get(text, cls.NORMAL)

    @property
    def display_name(self) -> str:
        return {
            PermissionLevel.NORMAL: "Normal",
            PermissionLevel.HELPER: "Server Helper",
            PermissionLevel.MOD: "Server Moderator",
            PermissionLevel.ADMIN: "Server Administrator",
            PermissionLevel.CO_OWNER: "Server Co-Owner",
            PermissionLevel.OWNER: "Server Owner",
        }[self]

    def __str__(self) -> str:
        return self.display_name


def _timestamp_to_datetime(value: int | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _model_to_dict(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _model_to_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_model_to_dict(item) for item in value]
    if is_dataclass(value):
        return {key: _model_to_dict(item) for key, item in asdict(value).items()}
    return value


@dataclass(frozen=True)
class Model:
    raw: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _model_to_dict(self)


@dataclass(frozen=True)
class PlayerLocation(Model):
    location_x: float | None = None
    location_z: float | None = None
    postal_code: str | None = None
    street_name: str | None = None
    building_number: str | None = None


@dataclass(frozen=True)
class Player(Model):
    player: str | None = None
    name: str | None = None
    user_id: int | None = None
    permission: str | None = None
    callsign: str | None = None
    team: str | None = None
    location: PlayerLocation | None = None
    wanted_stars: int | None = None

    @property
    def location_typed(self) -> PlayerLocation | None:
        return self.location

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.parse(self.permission)


@dataclass(frozen=True)
class StaffMember(Model):
    user_id: int | None = None
    name: str | None = None
    role: str | None = None

    @property
    def permission(self) -> str | None:
        return self.role

    @property
    def callsign(self) -> str | None:
        return None

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.parse(self.role)


@dataclass(frozen=True)
class StaffList(Model):
    co_owners: list[int] = field(default_factory=list)
    admins: dict[int, str] = field(default_factory=dict)
    mods: dict[int, str] = field(default_factory=dict)
    helpers: dict[int, str] = field(default_factory=dict)

    @property
    def members(self) -> list[StaffMember]:
        out = [StaffMember(user_id=user_id, name=None, role="CoOwner") for user_id in self.co_owners]
        out.extend(StaffMember(user_id=user_id, name=name, role="Admin") for user_id, name in self.admins.items())
        out.extend(StaffMember(user_id=user_id, name=name, role="Mod") for user_id, name in self.mods.items())
        out.extend(StaffMember(user_id=user_id, name=name, role="Helper") for user_id, name in self.helpers.items())
        return out

    def __iter__(self):
        return iter(self.members)

    def __len__(self) -> int:
        return len(self.members)

    def __getitem__(self, index: int) -> StaffMember:
        return self.members[index]

    @property
    def co_owner_members(self) -> list[StaffMember]:
        return [StaffMember(user_id=user_id, name=None, role="CoOwner") for user_id in self.co_owners]

    @property
    def admin_members(self) -> list[StaffMember]:
        return [StaffMember(user_id=user_id, name=name, role="Admin") for user_id, name in self.admins.items()]

    @property
    def mod_members(self) -> list[StaffMember]:
        return [StaffMember(user_id=user_id, name=name, role="Mod") for user_id, name in self.mods.items()]

    @property
    def helper_members(self) -> list[StaffMember]:
        return [StaffMember(user_id=user_id, name=name, role="Helper") for user_id, name in self.helpers.items()]


@dataclass(frozen=True)
class ServerInfo(Model):
    name: str | None = None
    owner_id: int | None = None
    co_owner_ids: list[int] = field(default_factory=list)
    current_players: int | None = None
    max_players: int | None = None
    join_key: str | None = None
    acc_verified_req: str | None = None
    team_balance: bool | None = None


@dataclass(frozen=True)
class JoinLogEntry(Model):
    join: bool | None = None
    timestamp: int | None = None
    player: str | None = None
    name: str | None = None
    user_id: int | None = None

    @property
    def timestamp_datetime(self) -> datetime | None:
        return _timestamp_to_datetime(self.timestamp)


@dataclass(frozen=True)
class KillLogEntry(Model):
    killed: str | None = None
    killed_name: str | None = None
    killed_id: int | None = None
    killer: str | None = None
    killer_name: str | None = None
    killer_id: int | None = None
    timestamp: int | None = None

    @property
    def victim(self) -> str | None:
        return self.killed

    @property
    def weapon(self) -> str | None:
        return None

    @property
    def timestamp_datetime(self) -> datetime | None:
        return _timestamp_to_datetime(self.timestamp)


@dataclass(frozen=True)
class CommandLogEntry(Model):
    player: str | None = None
    name: str | None = None
    user_id: int | None = None
    timestamp: int | None = None
    command: str | None = None

    @property
    def timestamp_datetime(self) -> datetime | None:
        return _timestamp_to_datetime(self.timestamp)


@dataclass(frozen=True)
class ModCallEntry(Model):
    caller: str | None = None
    caller_name: str | None = None
    caller_id: int | None = None
    moderator: str | None = None
    moderator_name: str | None = None
    moderator_id: int | None = None
    timestamp: int | None = None

    @property
    def player(self) -> str | None:
        return self.caller

    @property
    def reason(self) -> str | None:
        return None

    @property
    def location(self) -> str | None:
        return None

    @property
    def timestamp_datetime(self) -> datetime | None:
        return _timestamp_to_datetime(self.timestamp)


@dataclass(frozen=True)
class BanEntry(Model):
    player_id: str = ""
    player: str | None = None


@dataclass(frozen=True)
class BanList(Model):
    bans: dict[str, str | None] = field(default_factory=dict)

    @property
    def entries(self) -> list[BanEntry]:
        return [BanEntry(player_id=key, player=value, raw={key: value}) for key, value in self.bans.items()]


@dataclass(frozen=True)
class Vehicle(Model):
    name: str | None = None
    owner: str | None = None
    texture: str | None = None
    plate: str | None = None
    color_hex: str | None = None
    color_name: str | None = None

    @property
    def model(self) -> str | None:
        return self.model_name

    @property
    def color(self) -> str | None:
        return self.color_name or self.color_hex

    @property
    def team(self) -> str | None:
        return None

    @property
    def full_name(self) -> str | None:
        return self.name

    @property
    def parse_result(self):
        from .vehicles import parse_vehicle_name

        return parse_vehicle_name(self.name)

    @property
    def model_name(self) -> str | None:
        return self.parse_result.model

    @property
    def year(self) -> int | None:
        return self.parse_result.year

    @property
    def owner_name(self) -> str | None:
        name, _ = parse_player_identifier(self.owner)
        return name or _as_str(self.owner)

    @property
    def owner_id(self) -> int | None:
        _, user_id = parse_player_identifier(self.owner)
        return user_id

    @property
    def normalized_plate(self) -> str | None:
        from .vehicles import normalize_plate

        return normalize_plate(self.plate)

    @property
    def is_secondary(self) -> bool:
        return self.parse_result.is_secondary

    @property
    def is_prestige(self) -> bool:
        return self.parse_result.is_prestige

    @property
    def is_custom_texture(self) -> bool:
        from .vehicles import is_custom_texture

        return is_custom_texture(self.texture)


@dataclass(frozen=True)
class VehicleColor(Model):
    color_hex: str | None = None
    color_name: str | None = None


@dataclass(frozen=True)
class EmergencyCall(Model):
    team: str | None = None
    caller: int | str | None = None
    players: list[int] = field(default_factory=list)
    position: list[float] = field(default_factory=list)
    started_at: int | None = None
    call_number: int | None = None
    description: str | None = None
    position_descriptor: str | None = None

    @property
    def started_at_datetime(self) -> datetime | None:
        return _timestamp_to_datetime(self.started_at)


@dataclass(frozen=True)
class CommandResult(Model):
    message: str | None = None
    success: bool | None = None
    command_id: str | None = None


_SECTION_KEYS = {
    "players": ("Players", "players"),
    "staff": ("Staff", "staff"),
    "join_logs": ("JoinLogs", "joinLogs", "join_logs"),
    "queue": ("Queue", "queue"),
    "kill_logs": ("KillLogs", "killLogs", "kill_logs"),
    "command_logs": ("CommandLogs", "commandLogs", "command_logs"),
    "mod_calls": ("ModCalls", "modCalls", "mod_calls"),
    "emergency_calls": ("EmergencyCalls", "emergencyCalls", "emergency_calls"),
    "vehicles": ("Vehicles", "vehicles"),
}

_SECTION_ALIASES = {
    "commands": "command_logs",
    "command": "command_logs",
    "mods": "mod_calls",
    "mod": "mod_calls",
    "emergency": "emergency_calls",
    "calls": "emergency_calls",
}


def _normalize_section_name(name: str) -> str:
    key = name.strip().lower().replace("-", "_")
    return _SECTION_ALIASES.get(key, key)


@dataclass(frozen=True)
class ServerLogs(Model):
    join_logs: list[JoinLogEntry] = field(default_factory=list)
    kill_logs: list[KillLogEntry] = field(default_factory=list)
    command_logs: list[CommandLogEntry] = field(default_factory=list)
    mod_calls: list[ModCallEntry] = field(default_factory=list)


@dataclass(frozen=True)
class ServerBundle(ServerInfo):
    players: list[Player] | None = None
    staff: StaffList | None = None
    join_logs: list[JoinLogEntry] | None = None
    queue: list[int] | None = None
    kill_logs: list[KillLogEntry] | None = None
    command_logs: list[CommandLogEntry] | None = None
    mod_calls: list[ModCallEntry] | None = None
    emergency_calls: list[EmergencyCall] | None = None
    vehicles: list[Vehicle] | None = None

    @property
    def server_name(self) -> str | None:
        return self.name

    @property
    def helpers(self) -> list[StaffMember] | None:
        if self.staff is None:
            return None
        return [member for member in self.staff.members if member.role == "Helper"]

    @property
    def player_vehicles(self):
        if self.players is None or self.vehicles is None:
            return None
        from .vehicles import PlayerVehicleBundle

        return PlayerVehicleBundle(self.players, self.vehicles)

    @property
    def included_sections(self) -> frozenset[str]:
        names: set[str] = set()
        raw_keys = set(self.raw)
        for name, keys in _SECTION_KEYS.items():
            if getattr(self, name) is not None or any(key in raw_keys for key in keys):
                names.add(name)
        return frozenset(names)

    def has_section(self, name: str) -> bool:
        return _normalize_section_name(name) in self.included_sections

    @property
    def players_list(self) -> list[Player]:
        return self.players or []

    @property
    def queue_list(self) -> list[int]:
        return self.queue or []

    @property
    def vehicles_list(self) -> list[Vehicle]:
        return self.vehicles or []

    @property
    def join_logs_list(self) -> list[JoinLogEntry]:
        return self.join_logs or []

    @property
    def kill_logs_list(self) -> list[KillLogEntry]:
        return self.kill_logs or []

    @property
    def command_logs_list(self) -> list[CommandLogEntry]:
        return self.command_logs or []

    @property
    def mod_calls_list(self) -> list[ModCallEntry]:
        return self.mod_calls or []

    @property
    def emergency_calls_list(self) -> list[EmergencyCall]:
        return self.emergency_calls or []

    @property
    def staff_members(self) -> list[StaffMember]:
        return self.staff.members if self.staff is not None else []


def _parse_location(raw: Mapping[str, Any]) -> PlayerLocation:
    consumed: set[str] = set()
    key, x_value = _pick(raw, "LocationX", "locationX", "x")
    if key:
        consumed.add(key)
    key, z_value = _pick(raw, "LocationZ", "locationZ", "z")
    if key:
        consumed.add(key)
    key, postal_value = _pick(raw, "PostalCode", "postalCode", "postal_code")
    if key:
        consumed.add(key)
    key, street_value = _pick(raw, "StreetName", "streetName", "street_name")
    if key:
        consumed.add(key)
    key, building_value = _pick(raw, "BuildingNumber", "buildingNumber", "building_number")
    if key:
        consumed.add(key)
    raw_dict = dict(raw)
    return PlayerLocation(
        location_x=_as_float(x_value),
        location_z=_as_float(z_value),
        postal_code=_as_str(postal_value),
        street_name=_as_str(street_value),
        building_number=_as_str(building_value),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_player(raw: Mapping[str, Any]) -> Player:
    consumed: set[str] = set()
    key, player_value = _pick(raw, "Player", "player", "Name", "name", "Username", "username")
    if key:
        consumed.add(key)
    key, permission_value = _pick(raw, "Permission", "permission")
    if key:
        consumed.add(key)
    key, callsign_value = _pick(raw, "Callsign", "callsign")
    if key:
        consumed.add(key)
    key, team_value = _pick(raw, "Team", "team")
    if key:
        consumed.add(key)
    key, location_value = _pick(raw, "Location", "location")
    if key:
        consumed.add(key)
    key, wanted_value = _pick(raw, "WantedStars", "wantedStars", "wanted_stars")
    if key:
        consumed.add(key)

    name, user_id = parse_player_identifier(player_value)
    location = _parse_location(location_value) if isinstance(location_value, Mapping) else None
    raw_dict = dict(raw)
    return Player(
        player=_as_str(player_value),
        name=name,
        user_id=user_id,
        permission=_as_str(permission_value),
        callsign=_as_str(callsign_value),
        team=_as_str(team_value),
        location=location,
        wanted_stars=_as_int(wanted_value),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_staff(raw: Mapping[str, Any]) -> StaffList:
    consumed: set[str] = set()
    key, co_owners = _pick(raw, "CoOwners", "coOwners", "co_owners")
    if key:
        consumed.add(key)
    key, admins = _pick(raw, "Admins", "admins")
    if key:
        consumed.add(key)
    key, mods = _pick(raw, "Mods", "mods")
    if key:
        consumed.add(key)
    key, helpers = _pick(raw, "Helpers", "helpers")
    if key:
        consumed.add(key)
    raw_dict = dict(raw)
    return StaffList(
        co_owners=_as_int_list(co_owners),
        admins=_as_str_int_map(admins),
        mods=_as_str_int_map(mods),
        helpers=_as_str_int_map(helpers),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_server_base(raw: Mapping[str, Any]) -> dict[str, Any]:
    consumed: set[str] = set()
    key, name = _pick(raw, "Name", "ServerName", "name", "serverName")
    if key:
        consumed.add(key)
    key, owner_id = _pick(raw, "OwnerId", "ownerId", "owner_id")
    if key:
        consumed.add(key)
    key, co_owner_ids = _pick(raw, "CoOwnerIds", "coOwnerIds", "co_owner_ids")
    if key:
        consumed.add(key)
    key, current_players = _pick(raw, "CurrentPlayers", "currentPlayers", "current_players")
    if key:
        consumed.add(key)
    key, max_players = _pick(raw, "MaxPlayers", "maxPlayers", "max_players")
    if key:
        consumed.add(key)
    key, join_key = _pick(raw, "JoinKey", "joinKey", "join_key")
    if key:
        consumed.add(key)
    key, acc_verified_req = _pick(raw, "AccVerifiedReq", "accVerifiedReq", "acc_verified_req")
    if key:
        consumed.add(key)
    key, team_balance = _pick(raw, "TeamBalance", "teamBalance", "team_balance")
    if key:
        consumed.add(key)
    return {
        "name": _as_str(name),
        "owner_id": _as_int(owner_id),
        "co_owner_ids": _as_int_list(co_owner_ids),
        "current_players": _as_int(current_players),
        "max_players": _as_int(max_players),
        "join_key": _as_str(join_key),
        "acc_verified_req": _as_str(acc_verified_req),
        "team_balance": _as_bool(team_balance),
        "_consumed": consumed,
    }


def _parse_join_log(raw: Mapping[str, Any]) -> JoinLogEntry:
    consumed: set[str] = set()
    key, join = _pick(raw, "Join", "join")
    if key:
        consumed.add(key)
    key, timestamp = _pick(raw, "Timestamp", "timestamp")
    if key:
        consumed.add(key)
    key, player = _pick(raw, "Player", "player")
    if key:
        consumed.add(key)
    name, user_id = parse_player_identifier(player)
    raw_dict = dict(raw)
    return JoinLogEntry(
        join=_as_bool(join),
        timestamp=_as_int(timestamp),
        player=_as_str(player),
        name=name,
        user_id=user_id,
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_kill_log(raw: Mapping[str, Any]) -> KillLogEntry:
    consumed: set[str] = set()
    key, killed = _pick(raw, "Killed", "killed", "Victim", "victim")
    if key:
        consumed.add(key)
    key, killer = _pick(raw, "Killer", "killer")
    if key:
        consumed.add(key)
    key, timestamp = _pick(raw, "Timestamp", "timestamp")
    if key:
        consumed.add(key)
    killed_name, killed_id = parse_player_identifier(killed)
    killer_name, killer_id = parse_player_identifier(killer)
    raw_dict = dict(raw)
    return KillLogEntry(
        killed=_as_str(killed),
        killed_name=killed_name,
        killed_id=killed_id,
        killer=_as_str(killer),
        killer_name=killer_name,
        killer_id=killer_id,
        timestamp=_as_int(timestamp),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_command_log(raw: Mapping[str, Any]) -> CommandLogEntry:
    consumed: set[str] = set()
    key, player = _pick(raw, "Player", "player")
    if key:
        consumed.add(key)
    key, timestamp = _pick(raw, "Timestamp", "timestamp")
    if key:
        consumed.add(key)
    key, command = _pick(raw, "Command", "command")
    if key:
        consumed.add(key)
    name, user_id = parse_player_identifier(player)
    raw_dict = dict(raw)
    return CommandLogEntry(
        player=_as_str(player),
        name=name,
        user_id=user_id,
        timestamp=_as_int(timestamp),
        command=_as_str(command),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_mod_call(raw: Mapping[str, Any]) -> ModCallEntry:
    consumed: set[str] = set()
    key, caller = _pick(raw, "Caller", "caller", "Player", "player")
    if key:
        consumed.add(key)
    key, moderator = _pick(raw, "Moderator", "moderator")
    if key:
        consumed.add(key)
    key, timestamp = _pick(raw, "Timestamp", "timestamp")
    if key:
        consumed.add(key)
    caller_name, caller_id = parse_player_identifier(caller)
    moderator_name, moderator_id = parse_player_identifier(moderator)
    raw_dict = dict(raw)
    return ModCallEntry(
        caller=_as_str(caller),
        caller_name=caller_name,
        caller_id=caller_id,
        moderator=_as_str(moderator),
        moderator_name=moderator_name,
        moderator_id=moderator_id,
        timestamp=_as_int(timestamp),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_vehicle(raw: Mapping[str, Any]) -> Vehicle:
    consumed: set[str] = set()
    key, name = _pick(raw, "Name", "name", "Vehicle", "vehicle", "Model", "model")
    if key:
        consumed.add(key)
    key, owner = _pick(raw, "Owner", "owner")
    if key:
        consumed.add(key)
    key, texture = _pick(raw, "Texture", "texture")
    if key:
        consumed.add(key)
    key, plate = _pick(raw, "Plate", "plate")
    if key:
        consumed.add(key)
    key, color_hex = _pick(raw, "ColorHex", "colorHex", "color_hex")
    if key:
        consumed.add(key)
    key, color_name = _pick(raw, "ColorName", "colorName", "color_name")
    if key:
        consumed.add(key)
    raw_dict = dict(raw)
    return Vehicle(
        name=_as_str(name),
        owner=_as_str(owner),
        texture=_as_str(texture),
        plate=_as_str(plate),
        color_hex=_as_str(color_hex),
        color_name=_as_str(color_name),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def _parse_emergency_call(raw: Mapping[str, Any]) -> EmergencyCall:
    consumed: set[str] = set()
    key, team = _pick(raw, "Team", "team")
    if key:
        consumed.add(key)
    key, caller = _pick(raw, "Caller", "caller")
    if key:
        consumed.add(key)
    key, players = _pick(raw, "Players", "players")
    if key:
        consumed.add(key)
    key, position = _pick(raw, "Position", "position")
    if key:
        consumed.add(key)
    key, started_at = _pick(raw, "StartedAt", "startedAt", "started_at", "Timestamp", "timestamp")
    if key:
        consumed.add(key)
    key, call_number = _pick(raw, "CallNumber", "callNumber", "call_number")
    if key:
        consumed.add(key)
    key, description = _pick(raw, "Description", "description")
    if key:
        consumed.add(key)
    key, position_descriptor = _pick(raw, "PositionDescriptor", "positionDescriptor", "position_descriptor")
    if key:
        consumed.add(key)
    raw_dict = dict(raw)
    parsed_caller = _as_int(caller)
    return EmergencyCall(
        team=_as_str(team),
        caller=parsed_caller if parsed_caller is not None else _as_str(caller),
        players=_as_int_list(players),
        position=_as_float_list(position),
        started_at=_as_int(started_at),
        call_number=_as_int(call_number),
        description=_as_str(description),
        position_descriptor=_as_str(position_descriptor),
        raw=raw_dict,
        extra=_extra(raw_dict, consumed),
    )


def decode_server_info(payload: Any, *, endpoint: str = "/v2/server") -> ServerInfo:
    raw = _expect_mapping(payload, endpoint=endpoint)
    base = _parse_server_base(raw)
    consumed = base.pop("_consumed")
    return ServerInfo(raw=dict(raw), extra=_extra(raw, consumed), **base)


def decode_players(payload: Any, *, endpoint: str = "/v2/server?Players=true") -> list[Player]:
    return [_parse_player(item) for item in _expect_list(payload, endpoint=endpoint) if isinstance(item, Mapping)]


def decode_staff(payload: Any, *, endpoint: str = "/v2/server?Staff=true") -> StaffList:
    return _parse_staff(_expect_mapping(payload, endpoint=endpoint))


def decode_queue(payload: Any, *, endpoint: str = "/v2/server?Queue=true") -> list[int]:
    return _as_int_list(_expect_list(payload, endpoint=endpoint))


def decode_join_logs(payload: Any, *, endpoint: str = "/v2/server?JoinLogs=true") -> list[JoinLogEntry]:
    return [_parse_join_log(item) for item in _expect_list(payload, endpoint=endpoint) if isinstance(item, Mapping)]


def decode_kill_logs(payload: Any, *, endpoint: str = "/v2/server?KillLogs=true") -> list[KillLogEntry]:
    return [_parse_kill_log(item) for item in _expect_list(payload, endpoint=endpoint) if isinstance(item, Mapping)]


def decode_command_logs(payload: Any, *, endpoint: str = "/v2/server?CommandLogs=true") -> list[CommandLogEntry]:
    return [_parse_command_log(item) for item in _expect_list(payload, endpoint=endpoint) if isinstance(item, Mapping)]


def decode_mod_calls(payload: Any, *, endpoint: str = "/v2/server?ModCalls=true") -> list[ModCallEntry]:
    return [_parse_mod_call(item) for item in _expect_list(payload, endpoint=endpoint) if isinstance(item, Mapping)]


def decode_bans(payload: Any, *, endpoint: str = "/v1/server/bans") -> BanList:
    raw = _expect_mapping(payload, endpoint=endpoint)
    return BanList(bans={str(key): _as_str(value) for key, value in raw.items()}, raw=dict(raw), extra={})


def decode_vehicles(payload: Any, *, endpoint: str = "/v2/server?Vehicles=true") -> list[Vehicle]:
    return [_parse_vehicle(item) for item in _expect_list(payload, endpoint=endpoint) if isinstance(item, Mapping)]


def decode_emergency_calls(payload: Any, *, endpoint: str = "/v2/server?EmergencyCalls=true") -> list[EmergencyCall]:
    return [_parse_emergency_call(item) for item in _expect_list(payload, endpoint=endpoint) if isinstance(item, Mapping)]


def decode_command_result(payload: Any, *, endpoint: str = "/v2/server/command") -> CommandResult:
    if payload is None or payload == "":
        return CommandResult(message=None, success=None, raw={}, extra={})
    raw = _expect_mapping(payload, endpoint=endpoint)
    consumed: set[str] = set()
    key, message = _pick(raw, "message", "Message")
    if key:
        consumed.add(key)
    key, success = _pick(raw, "success", "Success", "ok")
    if key:
        consumed.add(key)
    key, command_id = _pick(raw, "commandId", "CommandId", "command_id")
    if key:
        consumed.add(key)
    message_text = _as_str(message)
    success_value = _as_bool(success)
    if success_value is None and message_text is not None and message_text.lower() == "success":
        success_value = True
    return CommandResult(
        message=message_text,
        success=success_value,
        command_id=_as_str(command_id),
        raw=dict(raw),
        extra=_extra(raw, consumed),
    )


def decode_server_logs(payload: Any, *, endpoint: str = "/v2/server") -> ServerLogs:
    raw = _expect_mapping(payload, endpoint=endpoint)
    consumed: set[str] = set()

    def field_value(*keys: str) -> Any:
        key, value = _pick(raw, *keys)
        if key:
            consumed.add(key)
        return value

    join_logs_raw = field_value("JoinLogs", "joinLogs", "join_logs")
    kill_logs_raw = field_value("KillLogs", "killLogs", "kill_logs")
    command_logs_raw = field_value("CommandLogs", "commandLogs", "command_logs")
    mod_calls_raw = field_value("ModCalls", "modCalls", "mod_calls")

    return ServerLogs(
        join_logs=decode_join_logs(join_logs_raw, endpoint=endpoint) if isinstance(join_logs_raw, list) else [],
        kill_logs=decode_kill_logs(kill_logs_raw, endpoint=endpoint) if isinstance(kill_logs_raw, list) else [],
        command_logs=decode_command_logs(command_logs_raw, endpoint=endpoint)
        if isinstance(command_logs_raw, list)
        else [],
        mod_calls=decode_mod_calls(mod_calls_raw, endpoint=endpoint) if isinstance(mod_calls_raw, list) else [],
        raw=dict(raw),
        extra=_extra(raw, consumed),
    )


def decode_server_bundle(payload: Any, *, endpoint: str = "/v2/server") -> ServerBundle:
    raw = _expect_mapping(payload, endpoint=endpoint)
    base = _parse_server_base(raw)
    consumed: set[str] = set(base.pop("_consumed"))

    def field_value(*keys: str) -> Any:
        key, value = _pick(raw, *keys)
        if key:
            consumed.add(key)
        return value

    players_raw = field_value("Players", "players")
    staff_raw = field_value("Staff", "staff")
    join_logs_raw = field_value("JoinLogs", "joinLogs", "join_logs")
    queue_raw = field_value("Queue", "queue")
    kill_logs_raw = field_value("KillLogs", "killLogs", "kill_logs")
    command_logs_raw = field_value("CommandLogs", "commandLogs", "command_logs")
    mod_calls_raw = field_value("ModCalls", "modCalls", "mod_calls")
    emergency_calls_raw = field_value("EmergencyCalls", "emergencyCalls", "emergency_calls")
    vehicles_raw = field_value("Vehicles", "vehicles")

    return ServerBundle(
        **base,
        players=decode_players(players_raw, endpoint=endpoint) if isinstance(players_raw, list) else None,
        staff=decode_staff(staff_raw, endpoint=endpoint) if isinstance(staff_raw, Mapping) else None,
        join_logs=decode_join_logs(join_logs_raw, endpoint=endpoint) if isinstance(join_logs_raw, list) else None,
        queue=decode_queue(queue_raw, endpoint=endpoint) if isinstance(queue_raw, list) else None,
        kill_logs=decode_kill_logs(kill_logs_raw, endpoint=endpoint) if isinstance(kill_logs_raw, list) else None,
        command_logs=decode_command_logs(command_logs_raw, endpoint=endpoint)
        if isinstance(command_logs_raw, list)
        else None,
        mod_calls=decode_mod_calls(mod_calls_raw, endpoint=endpoint) if isinstance(mod_calls_raw, list) else None,
        emergency_calls=decode_emergency_calls(emergency_calls_raw, endpoint=endpoint)
        if isinstance(emergency_calls_raw, list)
        else None,
        vehicles=decode_vehicles(vehicles_raw, endpoint=endpoint) if isinstance(vehicles_raw, list) else None,
        raw=dict(raw),
        extra=_extra(raw, consumed),
    )


CommandResponse = CommandResult
V2ServerBundle = ServerBundle
QueueEntry = int

decode_v2_server_bundle = decode_server_bundle


__all__ = [
    "BanEntry",
    "BanList",
    "CommandLogEntry",
    "CommandResponse",
    "CommandResult",
    "EmergencyCall",
    "JoinLogEntry",
    "KillLogEntry",
    "ModCallEntry",
    "Model",
    "PermissionLevel",
    "Player",
    "PlayerLocation",
    "QueueEntry",
    "ServerBundle",
    "ServerInfo",
    "ServerLogs",
    "StaffList",
    "StaffMember",
    "V2ServerBundle",
    "Vehicle",
    "VehicleColor",
    "decode_bans",
    "decode_command_logs",
    "decode_command_result",
    "decode_command_response",
    "decode_emergency_calls",
    "decode_join_logs",
    "decode_kill_logs",
    "decode_mod_calls",
    "decode_players",
    "decode_queue",
    "decode_server_bundle",
    "decode_server_info",
    "decode_server_logs",
    "decode_staff",
    "decode_v2_server_bundle",
    "decode_vehicles",
    "parse_player_identifier",
]


decode_command_response = decode_command_result
