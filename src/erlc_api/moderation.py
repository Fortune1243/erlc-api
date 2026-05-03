from __future__ import annotations

from typing import Any

from .commands import cmd, normalize_command


class AsyncModerator:
    """Async moderation command workflow helper."""

    def __init__(self, api: Any, *, server_key: str | None = None) -> None:
        self.api = api
        self.server_key = server_key

    async def command(self, command: Any, *, dry_run: bool = False):
        return await self.api.command(command, server_key=self.server_key, dry_run=dry_run)

    async def preview(self, command: Any) -> str:
        normalize_command(command)
        return normalize_command(command)

    async def pm(self, target: str, message: str, *, dry_run: bool = False):
        return await self.command(cmd.pm(target, message), dry_run=dry_run)

    async def warn(self, target: str, reason: str, *, dry_run: bool = False):
        return await self.command(cmd.warn(target, reason), dry_run=dry_run)

    async def ban(self, target: str, reason: str, duration: str | None = None, *, dry_run: bool = False):
        command = cmd("ban", target, duration, reason) if duration else cmd.ban(target, reason)
        return await self.command(command, dry_run=dry_run)

    async def kick(self, target: str, reason: str | None = None, *, dry_run: bool = False):
        command = cmd("kick", target, reason) if reason else cmd.kick(target)
        return await self.command(command, dry_run=dry_run)

    def audit_message(self, action: str, target: str, *, moderator: str | None = None, reason: str | None = None) -> str:
        actor = f" by {moderator}" if moderator else ""
        suffix = f": {reason}" if reason else ""
        return f"{action} {target}{actor}{suffix}"


class Moderator:
    """Sync moderation command workflow helper."""

    def __init__(self, api: Any, *, server_key: str | None = None) -> None:
        self.api = api
        self.server_key = server_key

    def command(self, command: Any, *, dry_run: bool = False):
        return self.api.command(command, server_key=self.server_key, dry_run=dry_run)

    def preview(self, command: Any) -> str:
        return normalize_command(command)

    def pm(self, target: str, message: str, *, dry_run: bool = False):
        return self.command(cmd.pm(target, message), dry_run=dry_run)

    def warn(self, target: str, reason: str, *, dry_run: bool = False):
        return self.command(cmd.warn(target, reason), dry_run=dry_run)

    def ban(self, target: str, reason: str, duration: str | None = None, *, dry_run: bool = False):
        command = cmd("ban", target, duration, reason) if duration else cmd.ban(target, reason)
        return self.command(command, dry_run=dry_run)

    def kick(self, target: str, reason: str | None = None, *, dry_run: bool = False):
        command = cmd("kick", target, reason) if reason else cmd.kick(target)
        return self.command(command, dry_run=dry_run)

    def audit_message(self, action: str, target: str, *, moderator: str | None = None, reason: str | None = None) -> str:
        actor = f" by {moderator}" if moderator else ""
        suffix = f": {reason}" if reason else ""
        return f"{action} {target}{actor}{suffix}"


__all__ = ["AsyncModerator", "Moderator"]
