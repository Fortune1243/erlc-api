# src/erlc_api/helpers.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .client import ERLCClient, ValidationResult
from .context import ERLCContext


@dataclass(frozen=True)
class ParsedLogCommand:
    player: str | None
    timestamp: int | None
    payload: str
    raw_command: str
    raw_entry: Mapping[str, Any]


def _parse_log_command(entry: Mapping[str, Any]) -> ParsedLogCommand | None:
    raw_command = entry.get("Command")
    if not isinstance(raw_command, str):
        return None

    stripped = raw_command.lstrip()
    lowered = stripped.lower()
    if not lowered.startswith(":log"):
        return None
    if len(stripped) == 4:
        return None
    if not stripped[4].isspace():
        return None

    payload = stripped[5:].strip()
    if not payload:
        return None

    player = entry.get("Player")
    if not isinstance(player, str):
        player = None

    timestamp = entry.get("Timestamp")
    if not isinstance(timestamp, int):
        timestamp = None

    return ParsedLogCommand(
        player=player,
        timestamp=timestamp,
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
    client: ERLCClient,
    ctx: ERLCContext,
    *,
    payload_prefix: str | None = None,
) -> list[ParsedLogCommand]:
    entries = await client.v1.command_logs(ctx)
    if not isinstance(entries, list):
        return []
    filtered_entries = [entry for entry in entries if isinstance(entry, Mapping)]
    return extract_log_commands(filtered_entries, payload_prefix=payload_prefix)


async def validate_server_key(client: ERLCClient, ctx: ERLCContext) -> ValidationResult:
    """Backward-compatible helper that delegates to ERLCClient.validate_key."""
    return await client.validate_key(ctx)
