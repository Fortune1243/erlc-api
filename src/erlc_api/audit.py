from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import time
from typing import Any, Mapping

from . import _utility as u


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(u.model_dict(value), ensure_ascii=False, default=str))


def _value(value: Any, field: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(field, default)
    return getattr(value, field, default)


def _event_type(value: Any) -> str:
    event_type = _value(value, "event_type", _value(value, "type", "unknown"))
    return str(getattr(event_type, "value", event_type))


def _discord_safe(text: str) -> str:
    return text.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")


@dataclass(frozen=True)
class AuditEvent:
    type: str
    message: str
    created_at: float = field(default_factory=time.time)
    actor: str | None = None
    target: str | None = None
    action: str | None = None
    success: bool | None = None
    source: str | None = None
    data: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "message": self.message,
            "created_at": self.created_at,
            "actor": self.actor,
            "target": self.target,
            "action": self.action,
            "success": self.success,
            "source": self.source,
            "data": _json_safe(dict(self.data)),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"))

    def to_console(self) -> str:
        status = "ok" if self.success is True else "failed" if self.success is False else "info"
        actor = f" actor={self.actor}" if self.actor else ""
        target = f" target={self.target}" if self.target else ""
        return f"[{status}] {self.type}: {self.message}{actor}{target}"

    def to_discord(self) -> str:
        return _discord_safe(self.to_console())

    @classmethod
    def command_result(cls, result: Any, *, command: Any = None, actor: str | None = None, target: str | None = None) -> AuditEvent:
        message = str(_value(result, "message", "") or "Command completed")
        success = _value(result, "success")
        return cls(
            type="command_result",
            message=message,
            actor=actor,
            target=target,
            action=str(command) if command is not None else None,
            success=success if isinstance(success, bool) else None,
            source="command",
            data={"command": str(command) if command is not None else None, "result": _json_safe(result)},
        )

    @classmethod
    def webhook_event(cls, event: Any) -> AuditEvent:
        kind = _event_type(event)
        command = _value(event, "command")
        command_text = _value(command, "command_text") if command is not None else None
        message = f"Webhook event received: {kind}"
        if command_text:
            message = f"{message} ({command_text})"
        return cls(
            type="webhook_event",
            message=message,
            action=command_text,
            source="webhook",
            data=_json_safe(event),
        )

    @classmethod
    def watcher_event(cls, event: Any) -> AuditEvent:
        kind = str(_value(event, "type", "unknown"))
        item = _value(event, "item")
        return cls(
            type="watcher_event",
            message=f"Watcher event: {kind}",
            action=kind,
            source="watcher",
            data={"item": _json_safe(item), "event": _json_safe(event)},
        )

    @classmethod
    def moderation_action(
        cls,
        action: str,
        target: str,
        *,
        actor: str | None = None,
        reason: str | None = None,
        success: bool | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> AuditEvent:
        suffix = f": {reason}" if reason else ""
        return cls(
            type="moderation_action",
            message=f"{action} {target}{suffix}",
            actor=actor,
            target=target,
            action=action,
            success=success,
            source="moderation",
            data=data or {},
        )


class AuditLog:
    """Optional JSONL audit log with in-memory fallback."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self._events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> AuditEvent:
        if self.path is None:
            self._events.append(event)
            return event
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(event.to_json())
            stream.write("\n")
        return event

    def events(self, limit: int | None = None) -> list[AuditEvent]:
        if limit is not None and limit < 0:
            raise ValueError("limit must be greater than or equal to zero.")
        if limit == 0:
            return []
        events = self._read_file() if self.path is not None else list(self._events)
        return events[-limit:] if limit is not None else events

    def command_result(self, result: Any, *, command: Any = None, actor: str | None = None, target: str | None = None) -> AuditEvent:
        return self.record(AuditEvent.command_result(result, command=command, actor=actor, target=target))

    def webhook_event(self, event: Any) -> AuditEvent:
        return self.record(AuditEvent.webhook_event(event))

    def watcher_event(self, event: Any) -> AuditEvent:
        return self.record(AuditEvent.watcher_event(event))

    def moderation_action(
        self,
        action: str,
        target: str,
        *,
        actor: str | None = None,
        reason: str | None = None,
        success: bool | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> AuditEvent:
        return self.record(
            AuditEvent.moderation_action(
                action,
                target,
                actor=actor,
                reason=reason,
                success=success,
                data=data,
            )
        )

    def _read_file(self) -> list[AuditEvent]:
        if self.path is None or not self.path.exists():
            return []
        out: list[AuditEvent] = []
        with self.path.open("r", encoding="utf-8") as stream:
            for line in stream:
                text = line.strip()
                if not text:
                    continue
                try:
                    raw = json.loads(text)
                    out.append(
                        AuditEvent(
                            type=str(raw["type"]),
                            message=str(raw["message"]),
                            created_at=float(raw.get("created_at", 0)),
                            actor=raw.get("actor"),
                            target=raw.get("target"),
                            action=raw.get("action"),
                            success=raw.get("success") if isinstance(raw.get("success"), bool) else None,
                            source=raw.get("source"),
                            data=raw.get("data") if isinstance(raw.get("data"), Mapping) else {},
                        )
                    )
                except (TypeError, ValueError, KeyError, json.JSONDecodeError):
                    continue
        return out


__all__ = ["AuditEvent", "AuditLog"]
