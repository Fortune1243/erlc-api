from __future__ import annotations

from typing import Any

from . import _utility as u


class Finder:
    """Lookup helper for bundles and model lists."""

    def __init__(self, data: Any) -> None:
        self.data = data

    def player(self, query: str | int, *, partial: bool = True):
        matches = self.players(query, partial=partial)
        return matches[0] if matches else None

    def players(
        self,
        query: str | int | None = None,
        *,
        partial: bool = True,
        team: str | None = None,
        permission: str | None = None,
        callsign: str | None = None,
    ):
        out = []
        for player in u.players(self.data):
            if isinstance(query, int) and player.user_id != query:
                continue
            if isinstance(query, str):
                matched = u.contains(player.name, query) if partial else u.equals(player.name, query)
                if not matched and not u.equals(player.player, query):
                    continue
            if not u.equals(player.team, team):
                continue
            if not u.equals(player.permission, permission):
                continue
            if not u.equals(player.callsign, callsign):
                continue
            out.append(player)
        return out

    def staff_member(self, query: str | int, *, role: str | None = None):
        matches = self.staff(query, role=role)
        return matches[0] if matches else None

    def staff(self, query: str | int | None = None, *, role: str | None = None):
        out = []
        for member in u.staff(self.data):
            if isinstance(query, int) and member.user_id != query:
                continue
            if isinstance(query, str) and not (u.contains(member.name, query) or u.equals(member.role, query)):
                continue
            if not u.equals(member.role, role):
                continue
            out.append(member)
        return out

    def vehicle(self, query: str | None = None, *, plate: str | None = None, owner: str | None = None):
        matches = self.vehicles(query, plate=plate, owner=owner)
        return matches[0] if matches else None

    def vehicles(self, query: str | None = None, *, plate: str | None = None, owner: str | None = None):
        out = []
        for vehicle in u.vehicles(self.data):
            if query is not None and not (u.contains(vehicle.name, query) or u.contains(vehicle.plate, query)):
                continue
            if not u.equals(vehicle.plate, plate):
                continue
            if not u.equals(vehicle.owner, owner):
                continue
            out.append(vehicle)
        return out

    def wanted(self, *, stars: int = 1, team: str | None = None):
        out = []
        for player in u.players(self.data):
            if (player.wanted_stars or 0) < stars:
                continue
            if not u.equals(player.team, team):
                continue
            out.append(player)
        return out

    def command_logs(
        self,
        *,
        player: str | int | None = None,
        command_prefix: str | None = None,
        command_contains: str | None = None,
        after: int | None = None,
        before: int | None = None,
    ):
        out = []
        for entry in u.command_logs(self.data):
            if isinstance(player, int) and entry.user_id != player:
                continue
            if isinstance(player, str) and not (u.contains(entry.name, player) or u.equals(entry.player, player)):
                continue
            if not u.startswith(entry.command, command_prefix):
                continue
            if not u.contains(entry.command, command_contains):
                continue
            ts = entry.timestamp
            if after is not None and (ts is None or ts < after):
                continue
            if before is not None and (ts is None or ts > before):
                continue
            out.append(entry)
        return out

    def command_log(self, **kwargs: Any):
        matches = self.command_logs(**kwargs)
        return matches[0] if matches else None

    def mod_calls(self, *, caller: str | int | None = None, moderator: str | int | None = None):
        out = []
        for entry in u.mod_calls(self.data):
            if isinstance(caller, int) and entry.caller_id != caller:
                continue
            if isinstance(caller, str) and not (u.contains(entry.caller_name, caller) or u.equals(entry.caller, caller)):
                continue
            if isinstance(moderator, int) and entry.moderator_id != moderator:
                continue
            if isinstance(moderator, str) and not (
                u.contains(entry.moderator_name, moderator) or u.equals(entry.moderator, moderator)
            ):
                continue
            out.append(entry)
        return out

    def emergency_calls(self, *, team: str | None = None, caller: str | int | None = None):
        out = []
        for call in u.emergency_calls(self.data):
            if not u.equals(call.team, team):
                continue
            if caller is not None and str(call.caller) != str(caller):
                continue
            out.append(call)
        return out

    def bans(self, query: str | int | None = None):
        out = []
        for ban in u.bans(self.data):
            if query is None or str(ban.player_id) == str(query) or u.contains(ban.player, query):
                out.append(ban)
        return out


__all__ = ["Finder"]
