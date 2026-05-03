from __future__ import annotations

from dataclasses import is_dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .models import (
    BanEntry,
    BanList,
    CommandLogEntry,
    EmergencyCall,
    JoinLogEntry,
    KillLogEntry,
    ModCallEntry,
    Model,
    Player,
    ServerBundle,
    StaffList,
    StaffMember,
    Vehicle,
)


def as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_text(value: Any) -> str:
    text = as_text(value)
    return text.lower() if text else ""


def contains(value: Any, needle: Any) -> bool:
    if needle is None:
        return True
    return normalize_text(needle) in normalize_text(value)


def equals(value: Any, expected: Any) -> bool:
    if expected is None:
        return True
    return normalize_text(value) == normalize_text(expected)


def startswith(value: Any, prefix: Any) -> bool:
    if prefix is None:
        return True
    return normalize_text(value).startswith(normalize_text(prefix))


def get_value(item: Any, field: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(field, default)
    return getattr(item, field, default)


def timestamp_of(item: Any) -> int | None:
    value = get_value(item, "timestamp", None)
    if value is None:
        value = get_value(item, "started_at", None)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def datetime_from_timestamp(value: int | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc)


def command_name(command: str | None) -> str | None:
    if not command:
        return None
    text = command.strip()
    if text.startswith(":"):
        text = text[1:]
    if not text:
        return None
    return text.split(maxsplit=1)[0].lower()


def model_dict(value: Any) -> Any:
    if isinstance(value, Model):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return {key: model_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [model_dict(item) for item in value]
    return value


def rows(data: Any) -> list[Any]:
    if data is None:
        return []
    if isinstance(data, ServerBundle):
        return [data]
    if isinstance(data, StaffList):
        return data.members
    if isinstance(data, BanList):
        return data.entries
    if isinstance(data, Mapping):
        return [data]
    if isinstance(data, Iterable) and not isinstance(data, (str, bytes, bytearray)):
        return list(data)
    return [data]


def players(data: Any) -> list[Player]:
    if isinstance(data, ServerBundle):
        return list(data.players or [])
    return [item for item in rows(data) if isinstance(item, Player)]


def staff(data: Any) -> list[StaffMember]:
    if isinstance(data, ServerBundle):
        return data.staff.members if data.staff is not None else []
    if isinstance(data, StaffList):
        return data.members
    return [item for item in rows(data) if isinstance(item, StaffMember)]


def vehicles(data: Any) -> list[Vehicle]:
    if isinstance(data, ServerBundle):
        return list(data.vehicles or [])
    return [item for item in rows(data) if isinstance(item, Vehicle)]


def queue(data: Any) -> list[int]:
    if isinstance(data, ServerBundle):
        return list(data.queue or [])
    return [item for item in rows(data) if isinstance(item, int) and not isinstance(item, bool)]


def join_logs(data: Any) -> list[JoinLogEntry]:
    if isinstance(data, ServerBundle):
        return list(data.join_logs or [])
    return [item for item in rows(data) if isinstance(item, JoinLogEntry)]


def kill_logs(data: Any) -> list[KillLogEntry]:
    if isinstance(data, ServerBundle):
        return list(data.kill_logs or [])
    return [item for item in rows(data) if isinstance(item, KillLogEntry)]


def command_logs(data: Any) -> list[CommandLogEntry]:
    if isinstance(data, ServerBundle):
        return list(data.command_logs or [])
    return [item for item in rows(data) if isinstance(item, CommandLogEntry)]


def mod_calls(data: Any) -> list[ModCallEntry]:
    if isinstance(data, ServerBundle):
        return list(data.mod_calls or [])
    return [item for item in rows(data) if isinstance(item, ModCallEntry)]


def emergency_calls(data: Any) -> list[EmergencyCall]:
    if isinstance(data, ServerBundle):
        return list(data.emergency_calls or [])
    return [item for item in rows(data) if isinstance(item, EmergencyCall)]


def bans(data: Any) -> list[BanEntry]:
    if isinstance(data, BanList):
        return data.entries
    return [item for item in rows(data) if isinstance(item, BanEntry)]


def server_bundles(data: Any) -> list[ServerBundle]:
    return [item for item in rows(data) if isinstance(item, ServerBundle)]


def all_known_items(data: Any) -> list[Any]:
    if not isinstance(data, ServerBundle):
        return rows(data)
    out: list[Any] = [data]
    out.extend(data.players or [])
    out.extend(data.staff.members if data.staff is not None else [])
    out.extend(data.vehicles or [])
    out.extend(data.queue or [])
    out.extend(data.join_logs or [])
    out.extend(data.kill_logs or [])
    out.extend(data.command_logs or [])
    out.extend(data.mod_calls or [])
    out.extend(data.emergency_calls or [])
    return out
