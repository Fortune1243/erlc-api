from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .client import AsyncERLC, ValidationResult


@dataclass(frozen=True)
class ParsedLogCommand:
    player: str | None
    timestamp: int | None
    payload: str
    raw_command: str
    raw_entry: Mapping[str, Any]


def _parse_log_command(entry: Mapping[str, Any]) -> ParsedLogCommand | None:
    raw_command = entry.get("Command") or entry.get("command")
    if not isinstance(raw_command, str):
        return None
    stripped = raw_command.lstrip()
    lowered = stripped.lower()
    if not lowered.startswith(":log"):
        return None
    if len(stripped) == 4 or not stripped[4].isspace():
        return None
    payload = stripped[5:].strip()
    if not payload:
        return None
    player = entry.get("Player") or entry.get("player")
    timestamp = entry.get("Timestamp") or entry.get("timestamp")
    return ParsedLogCommand(
        player=player if isinstance(player, str) else None,
        timestamp=timestamp if isinstance(timestamp, int) else None,
        payload=payload,
        raw_command=raw_command,
        raw_entry=entry,
    )


def extract_log_commands(
    entries: Iterable[Mapping[str, Any]],
    *,
    payload_prefix: str | None = None,
) -> list[ParsedLogCommand]:
    parsed: list[ParsedLogCommand] = []
    for entry in entries:
        item = _parse_log_command(entry)
        if item is None:
            continue
        if payload_prefix is not None and not item.payload.startswith(payload_prefix):
            continue
        parsed.append(item)
    return parsed


async def fetch_log_commands(
    client: AsyncERLC,
    *,
    server_key: str | None = None,
    payload_prefix: str | None = None,
) -> list[ParsedLogCommand]:
    entries = await client.command_logs(server_key=server_key, raw=True)
    if not isinstance(entries, list):
        return []
    filtered = [entry for entry in entries if isinstance(entry, Mapping)]
    return extract_log_commands(filtered, payload_prefix=payload_prefix)


async def validate_server_key(client: AsyncERLC, *, server_key: str | None = None) -> ValidationResult:
    return await client.validate_key(server_key=server_key)

