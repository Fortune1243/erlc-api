from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from . import _utility as u


CONTENT_LIMIT = 2000
EMBED_TITLE_LIMIT = 256
EMBED_DESCRIPTION_LIMIT = 4096
EMBED_FIELD_NAME_LIMIT = 256
EMBED_FIELD_VALUE_LIMIT = 1024
EMBED_FIELD_LIMIT = 25


def safe_text(value: Any, *, limit: int | None = None) -> str:
    text = "" if value is None else str(value)
    text = text.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
    if limit is not None and len(text) > limit:
        return f"{text[: max(0, limit - 3)]}..."
    return text


def chunks(text: str, *, limit: int = CONTENT_LIMIT) -> list[str]:
    if limit <= 0:
        raise ValueError("limit must be greater than zero.")
    cleaned = safe_text(text)
    if not cleaned:
        return [""]
    return [cleaned[index : index + limit] for index in range(0, len(cleaned), limit)]


@dataclass(frozen=True)
class DiscordField:
    name: str
    value: str
    inline: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": safe_text(self.name, limit=EMBED_FIELD_NAME_LIMIT) or "\u200b",
            "value": safe_text(self.value, limit=EMBED_FIELD_VALUE_LIMIT) or "\u200b",
            "inline": self.inline,
        }


@dataclass(frozen=True)
class DiscordEmbed:
    title: str | None = None
    description: str | None = None
    color: int | None = None
    fields: tuple[DiscordField, ...] = field(default_factory=tuple)
    footer: str | None = None

    def add_field(self, name: str, value: Any, *, inline: bool = False) -> DiscordEmbed:
        if len(self.fields) >= EMBED_FIELD_LIMIT:
            raise ValueError("Discord embeds can contain at most 25 fields.")
        return DiscordEmbed(
            title=self.title,
            description=self.description,
            color=self.color,
            fields=(*self.fields, DiscordField(name=name, value=str(value), inline=inline)),
            footer=self.footer,
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.title is not None:
            payload["title"] = safe_text(self.title, limit=EMBED_TITLE_LIMIT)
        if self.description is not None:
            payload["description"] = safe_text(self.description, limit=EMBED_DESCRIPTION_LIMIT)
        if self.color is not None:
            payload["color"] = self.color
        if self.fields:
            payload["fields"] = [field.to_dict() for field in self.fields[:EMBED_FIELD_LIMIT]]
        if self.footer is not None:
            payload["footer"] = {"text": safe_text(self.footer, limit=2048)}
        return payload


@dataclass(frozen=True)
class DiscordMessage:
    content: str | None = None
    embeds: tuple[DiscordEmbed, ...] = field(default_factory=tuple)
    ephemeral: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.content is not None:
            payload["content"] = safe_text(self.content, limit=CONTENT_LIMIT)
        if self.embeds:
            payload["embeds"] = [embed.to_dict() for embed in self.embeds[:10]]
        if self.ephemeral:
            payload["ephemeral"] = True
        return payload


class DiscordFormatter:
    def server_status(self, status: Any, *, color: int = 0x2ECC71) -> DiscordMessage:
        title = getattr(status, "server_name", None) or "Server Status"
        health = getattr(status, "health", "unknown")
        embed = DiscordEmbed(title=title, description=f"Health: {health}", color=color)
        for name, value in (
            ("Players", f"{getattr(status, 'current_players', None) or getattr(status, 'player_count', 0)}/{getattr(status, 'max_players', '?')}"),
            ("Queue", getattr(status, "queue_count", 0)),
            ("Staff", getattr(status, "staff_count", 0)),
            ("Vehicles", getattr(status, "vehicle_count", 0)),
            ("Emergency Calls", getattr(status, "emergency_call_count", 0)),
        ):
            embed = embed.add_field(name, value, inline=True)
        issues = getattr(status, "issues", []) or []
        if issues:
            embed = embed.add_field("Issues", "\n".join(getattr(issue, "message", str(issue)) for issue in issues[:5]))
        return DiscordMessage(embeds=(embed,))

    def players(self, players: Iterable[Any], *, title: str = "Players") -> DiscordMessage:
        items = list(players)
        description = "No players" if not items else "\n".join(
            f"{u.get_value(player, 'name', u.get_value(player, 'player', 'unknown'))} - {u.get_value(player, 'team', 'Unknown')}"
            for player in items[:40]
        )
        return DiscordMessage(embeds=(DiscordEmbed(title=title, description=description, color=0x3498DB),))

    def queue(self, queue: Iterable[int]) -> DiscordMessage:
        items = list(queue)
        description = "Queue is empty" if not items else "\n".join(f"{index}. {user_id}" for index, user_id in enumerate(items, 1))
        return DiscordMessage(embeds=(DiscordEmbed(title="Queue", description=description, color=0xF1C40F),))

    def diagnostics(self, diagnostics: Any) -> DiscordMessage:
        items = getattr(diagnostics, "items", diagnostics) or []
        description = "No diagnostics" if not items else "\n".join(
            f"[{getattr(item, 'severity', 'info')}] {getattr(item, 'message', item)}" for item in list(items)[:10]
        )
        return DiscordMessage(embeds=(DiscordEmbed(title="Diagnostics", description=description, color=0xE67E22),))

    def error(self, error: Exception) -> DiscordMessage:
        return DiscordMessage(embeds=(DiscordEmbed(title=type(error).__name__, description=str(error), color=0xE74C3C),))

    def command_result(self, result: Any) -> DiscordMessage:
        success = getattr(result, "success", None)
        title = "Command Result"
        color = 0x2ECC71 if success is True else 0xE74C3C if success is False else 0x95A5A6
        return DiscordMessage(embeds=(DiscordEmbed(title=title, description=getattr(result, "message", None) or "No message", color=color),))


__all__ = [
    "DiscordEmbed",
    "DiscordField",
    "DiscordFormatter",
    "DiscordMessage",
    "chunks",
    "safe_text",
]
