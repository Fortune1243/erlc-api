from __future__ import annotations

from dataclasses import dataclass


def validate_command_syntax(command: str) -> None:
    if not isinstance(command, str):
        raise TypeError("command must be a string.")
    stripped = command.strip()
    if not stripped:
        raise ValueError("command cannot be empty.")
    if "\n" in stripped or "\r" in stripped:
        raise ValueError("command cannot contain newline characters.")
    if not stripped.startswith(":"):
        raise ValueError("command must start with ':'.")
    parts = stripped.split(maxsplit=1)
    command_name = parts[0][1:]
    if not command_name:
        raise ValueError("command name cannot be empty.")


@dataclass(frozen=True)
class BuiltCommand:
    text: str

    def __post_init__(self) -> None:
        validate_command_syntax(self.text)

    def __str__(self) -> str:
        return self.text


def _require_value(name: str, value: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError(f"{name} cannot be blank.")
    return text


class CommandBuilder:
    @staticmethod
    def raw(command: str) -> BuiltCommand:
        return BuiltCommand(command.strip())

    @staticmethod
    def pm(*, target: str, message: str) -> BuiltCommand:
        target_value = _require_value("target", target)
        message_value = _require_value("message", message)
        return BuiltCommand(f":pm {target_value} {message_value}")

    @staticmethod
    def rank(*, target: str, rank: str) -> BuiltCommand:
        target_value = _require_value("target", target)
        rank_value = _require_value("rank", rank)
        return BuiltCommand(f":rank {target_value} {rank_value}")

    @staticmethod
    def warn(*, target: str, reason: str) -> BuiltCommand:
        target_value = _require_value("target", target)
        reason_value = _require_value("reason", reason)
        return BuiltCommand(f":warn {target_value} {reason_value}")

    @staticmethod
    def ban(*, target: str, reason: str, duration: str | None = None) -> BuiltCommand:
        target_value = _require_value("target", target)
        reason_value = _require_value("reason", reason)
        if duration is None:
            return BuiltCommand(f":ban {target_value} {reason_value}")
        duration_value = _require_value("duration", duration)
        return BuiltCommand(f":ban {target_value} {duration_value} {reason_value}")


def infer_command_success(*, success: bool | None, message: str | None) -> bool | None:
    if success is not None:
        return success
    if not message:
        return None
    text = message.lower()
    failure_terms = ("invalid", "failed", "error", "denied", "not found", "unable")
    if any(term in text for term in failure_terms):
        return False
    success_terms = ("success", "sent", "executed", "completed", "ranked", "warned", "banned", "done")
    if any(term in text for term in success_terms):
        return True
    return None


__all__ = [
    "BuiltCommand",
    "CommandBuilder",
    "infer_command_success",
    "validate_command_syntax",
]
