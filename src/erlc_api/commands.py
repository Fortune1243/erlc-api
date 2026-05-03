from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def normalize_command(command: str | Command) -> str:
    """Return a PRC command string, accepting either `:cmd ...` or `cmd ...`."""
    if isinstance(command, Command):
        command = command.text
    if not isinstance(command, str):
        raise TypeError("command must be a string or Command.")

    text = command.strip()
    if not text:
        raise ValueError("command cannot be empty.")
    if "\n" in text or "\r" in text:
        raise ValueError("command cannot contain newline characters.")
    if not text.startswith(":"):
        text = f":{text}"

    name = text[1:].split(maxsplit=1)[0].strip()
    if not name:
        raise ValueError("command name cannot be empty.")
    return text


def validate_command(command: str | Command) -> None:
    normalize_command(command)


@dataclass(frozen=True)
class Command:
    """Small immutable command value accepted by `ERLC.command`."""

    text: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "text", normalize_command(self.text))

    def __str__(self) -> str:
        return self.text


def _stringify_part(value: Any) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError("command parts cannot be blank.")
    return text


class CommandFactory:
    """Flexible command builder: `cmd.pm("Avi", "hi")` or `cmd("pm", "Avi", "hi")`."""

    def __call__(self, name: str, *parts: Any) -> Command:
        bits = [_stringify_part(name), *[_stringify_part(part) for part in parts]]
        return Command(" ".join(bits))

    def raw(self, command: str) -> Command:
        return Command(command)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)

        def build(*parts: Any) -> Command:
            return self(name, *parts)

        return build


cmd = CommandFactory()


BuiltCommand = Command
validate_command_syntax = validate_command


def infer_command_success(*, success: bool | None, message: str | None) -> bool | None:
    if success is not None:
        return success
    if not message:
        return None
    lowered = message.lower()
    if any(term in lowered for term in ("invalid", "failed", "error", "denied", "not found", "unable")):
        return False
    if any(term in lowered for term in ("success", "sent", "executed", "completed", "done")):
        return True
    return None


__all__ = [
    "BuiltCommand",
    "Command",
    "CommandFactory",
    "cmd",
    "infer_command_success",
    "normalize_command",
    "validate_command",
    "validate_command_syntax",
]
