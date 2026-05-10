from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .models import PermissionLevel


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


@dataclass(frozen=True)
class CommandPolicyResult:
    """Result from checking a command against a local application policy."""

    command: str
    name: str
    allowed: bool
    code: str | None = None
    reason: str | None = None

    def __bool__(self) -> bool:
        return self.allowed


class CommandPolicyError(ValueError):
    """Raised when `CommandPolicy.validate(...)` rejects a command."""

    def __init__(self, result: CommandPolicyResult) -> None:
        message = result.reason or "Command is not allowed by policy."
        super().__init__(message)
        self.result = result


@dataclass(frozen=True)
class CommandMetadata:
    name: str
    display_name: str
    category: str
    minimum_permission: PermissionLevel = PermissionLevel.MOD
    supports_target: bool = False
    supports_multiple_targets: bool = False
    supports_text: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "category": self.category,
            "minimum_permission": self.minimum_permission.name,
            "minimum_permission_display": self.minimum_permission.display_name,
            "supports_target": self.supports_target,
            "supports_multiple_targets": self.supports_multiple_targets,
            "supports_text": self.supports_text,
        }


@dataclass(frozen=True)
class CommandPreview:
    """Local command preview produced without sending HTTP."""

    command: str
    name: str
    allowed: bool
    code: str | None = None
    reason: str | None = None
    metadata: CommandMetadata | None = None

    def __bool__(self) -> bool:
        return self.allowed

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "name": self.name,
            "allowed": self.allowed,
            "code": self.code,
            "reason": self.reason,
            "metadata": self.metadata.to_dict() if self.metadata is not None else None,
        }


def _metadata(
    name: str,
    display_name: str,
    category: str,
    minimum_permission: PermissionLevel = PermissionLevel.MOD,
    *,
    supports_target: bool = False,
    supports_multiple_targets: bool = False,
    supports_text: bool = False,
) -> CommandMetadata:
    return CommandMetadata(
        name=name,
        display_name=display_name,
        category=category,
        minimum_permission=minimum_permission,
        supports_target=supports_target,
        supports_multiple_targets=supports_multiple_targets,
        supports_text=supports_text,
    )


COMMAND_METADATA: dict[str, CommandMetadata] = {
    "h": _metadata("h", "Hint", "communication", PermissionLevel.MOD, supports_text=True),
    "hint": _metadata("hint", "Hint", "communication", PermissionLevel.MOD, supports_text=True),
    "m": _metadata("m", "Message", "communication", PermissionLevel.MOD, supports_text=True),
    "message": _metadata("message", "Message", "communication", PermissionLevel.MOD, supports_text=True),
    "pm": _metadata("pm", "Private Message", "communication", PermissionLevel.MOD, supports_target=True, supports_multiple_targets=True, supports_text=True),
    "privatemessage": _metadata("privatemessage", "Private Message", "communication", PermissionLevel.MOD, supports_target=True, supports_multiple_targets=True, supports_text=True),
    "kick": _metadata("kick", "Kick Player", "moderation", PermissionLevel.MOD, supports_target=True, supports_multiple_targets=True, supports_text=True),
    "ban": _metadata("ban", "Ban Player", "moderation", PermissionLevel.ADMIN, supports_target=True, supports_multiple_targets=True, supports_text=True),
    "unban": _metadata("unban", "Unban Player", "moderation", PermissionLevel.ADMIN, supports_target=True),
    "wanted": _metadata("wanted", "Mark Wanted", "roleplay", PermissionLevel.MOD, supports_target=True, supports_multiple_targets=True),
    "unwanted": _metadata("unwanted", "Clear Wanted", "roleplay", PermissionLevel.MOD, supports_target=True, supports_multiple_targets=True),
    "jail": _metadata("jail", "Jail Player", "moderation", PermissionLevel.MOD, supports_target=True, supports_multiple_targets=True),
    "unjail": _metadata("unjail", "Unjail Player", "moderation", PermissionLevel.MOD, supports_target=True, supports_multiple_targets=True),
    "kill": _metadata("kill", "Kill Player", "admin", PermissionLevel.ADMIN, supports_target=True, supports_multiple_targets=True),
    "heal": _metadata("heal", "Heal Player", "admin", PermissionLevel.MOD, supports_target=True, supports_multiple_targets=True),
    "refresh": _metadata("refresh", "Refresh Player", "admin", PermissionLevel.MOD, supports_target=True, supports_multiple_targets=True),
    "respawn": _metadata("respawn", "Respawn Player", "admin", PermissionLevel.MOD, supports_target=True, supports_multiple_targets=True),
    "bring": _metadata("bring", "Bring Player", "admin", PermissionLevel.MOD, supports_target=True, supports_multiple_targets=True),
    "tp": _metadata("tp", "Teleport", "admin", PermissionLevel.MOD, supports_target=True),
    "teleport": _metadata("teleport", "Teleport", "admin", PermissionLevel.MOD, supports_target=True),
    "admin": _metadata("admin", "Grant Admin", "permissions", PermissionLevel.ADMIN, supports_target=True, supports_multiple_targets=True),
    "unadmin": _metadata("unadmin", "Remove Admin", "permissions", PermissionLevel.ADMIN, supports_target=True, supports_multiple_targets=True),
    "mod": _metadata("mod", "Grant Moderator", "permissions", PermissionLevel.ADMIN, supports_target=True, supports_multiple_targets=True),
    "unmod": _metadata("unmod", "Remove Moderator", "permissions", PermissionLevel.ADMIN, supports_target=True, supports_multiple_targets=True),
    "helper": _metadata("helper", "Grant Helper", "permissions", PermissionLevel.ADMIN, supports_target=True, supports_multiple_targets=True),
    "unhelper": _metadata("unhelper", "Remove Helper", "permissions", PermissionLevel.ADMIN, supports_target=True, supports_multiple_targets=True),
    "log": _metadata("log", "Log Note", "utility", PermissionLevel.MOD, supports_text=True),
    "weather": _metadata("weather", "Set Weather", "server", PermissionLevel.ADMIN),
    "time": _metadata("time", "Set Time", "server", PermissionLevel.ADMIN),
    "shutdown": _metadata("shutdown", "Shutdown Server", "server", PermissionLevel.OWNER),
}


def get_command_metadata(command: str | Command) -> CommandMetadata | None:
    name = _command_name(normalize_command(command)).casefold()
    return COMMAND_METADATA.get(name)


def preview_command(command: str | Command, *, policy: CommandPolicy | None = None) -> CommandPreview:
    if policy is not None:
        result = policy.check(command)
        metadata = COMMAND_METADATA.get(result.name.casefold()) if result.name else None
        return CommandPreview(
            command=result.command,
            name=result.name,
            allowed=result.allowed,
            code=result.code,
            reason=result.reason,
            metadata=metadata,
        )

    try:
        normalized = normalize_command(command)
    except (TypeError, ValueError) as exc:
        return CommandPreview(
            command=str(command),
            name="",
            allowed=False,
            code="invalid_command",
            reason=str(exc),
        )

    name = _command_name(normalized)
    return CommandPreview(
        command=normalized,
        name=name,
        allowed=True,
        metadata=COMMAND_METADATA.get(name.casefold()),
    )


def _command_label(name: str) -> str:
    metadata = COMMAND_METADATA.get(name.casefold())
    if metadata is None:
        return f"'{name}'"
    return f"'{name}' ({metadata.display_name}, recommended {metadata.minimum_permission.display_name}+)"


def _command_name(command: str) -> str:
    return command[1:].split(maxsplit=1)[0]


def _normalize_policy_names(names: Iterable[str] | str | None, *, case_sensitive: bool) -> frozenset[str]:
    if names is None:
        return frozenset()

    normalized: set[str] = set()
    values = (names,) if isinstance(names, str) else names
    for value in values:
        if not isinstance(value, str):
            raise TypeError("policy command names must be strings.")
        text = value.strip()
        if not text:
            raise ValueError("policy command names cannot be blank.")
        if "\n" in text or "\r" in text:
            raise ValueError("policy command names cannot contain newlines.")
        if text.startswith(":"):
            text = text[1:]
        name = text.split(maxsplit=1)[0].strip()
        if not name:
            raise ValueError("policy command names cannot be blank.")
        normalized.add(name if case_sensitive else name.casefold())
    return frozenset(normalized)


class CommandPolicy:
    """Local allowlist-first command guard for bots, web routes, and previews."""

    def __init__(
        self,
        *,
        allowed: Iterable[str] | str | None = None,
        blocked: Iterable[str] | str | None = None,
        max_length: int | None = 120,
        case_sensitive: bool = False,
    ) -> None:
        if max_length is not None and max_length <= 0:
            raise ValueError("max_length must be positive or None.")
        self.case_sensitive = case_sensitive
        self.max_length = max_length
        self.allowed = _normalize_policy_names(allowed, case_sensitive=case_sensitive)
        self.blocked = _normalize_policy_names(blocked, case_sensitive=case_sensitive)

    def check(self, command: str | Command) -> CommandPolicyResult:
        try:
            normalized = normalize_command(command)
        except (TypeError, ValueError) as exc:
            return CommandPolicyResult(
                command=str(command),
                name="",
                allowed=False,
                code="invalid_command",
                reason=str(exc),
            )

        name = _command_name(normalized)
        key = name if self.case_sensitive else name.casefold()

        if self.max_length is not None and len(normalized) > self.max_length:
            return CommandPolicyResult(
                command=normalized,
                name=name,
                allowed=False,
                code="max_length",
                reason=f"Command is longer than {self.max_length} characters.",
            )

        if key in self.blocked:
            return CommandPolicyResult(
                command=normalized,
                name=name,
                allowed=False,
                code="blocked",
                reason=f"Command {_command_label(name)} is blocked by policy.",
            )

        if key not in self.allowed:
            return CommandPolicyResult(
                command=normalized,
                name=name,
                allowed=False,
                code="not_allowed",
                reason=f"Command {_command_label(name)} is not in the allowed command set.",
            )

        return CommandPolicyResult(command=normalized, name=name, allowed=True)

    def validate(self, command: str | Command) -> str:
        result = self.check(command)
        if not result:
            raise CommandPolicyError(result)
        return result.command


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
    "CommandMetadata",
    "CommandPreview",
    "CommandPolicy",
    "CommandPolicyError",
    "CommandPolicyResult",
    "COMMAND_METADATA",
    "cmd",
    "get_command_metadata",
    "infer_command_success",
    "normalize_command",
    "preview_command",
    "validate_command",
    "validate_command_syntax",
]
