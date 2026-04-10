from __future__ import annotations

from typing import Any

from ..models import (
    CommandLogEntry,
    EmergencyCall,
    ModCallEntry,
    Player,
    PlayerLocation,
    QueueEntry,
    ServerInfo,
    StaffMember,
    V2ServerBundle,
    Vehicle,
    VehicleColor,
)


def location_to_dto(location: PlayerLocation) -> dict[str, Any]:
    return {
        "location_x": location.location_x,
        "location_z": location.location_z,
        "postal_code": location.postal_code,
        "street_name": location.street_name,
        "building_number": location.building_number,
        "extra": dict(location.extra),
    }


def vehicle_color_to_dto(color: VehicleColor) -> dict[str, Any]:
    return {
        "color_hex": color.color_hex,
        "color_name": color.color_name,
        "extra": dict(color.extra),
    }


def emergency_call_to_dto(call: EmergencyCall) -> dict[str, Any]:
    return {
        "team": call.team,
        "caller": call.caller,
        "position": list(call.position) if call.position is not None else None,
        "started_at": call.started_at,
        "extra": dict(call.extra),
    }


def player_to_dto(player: Player) -> dict[str, Any]:
    return {
        "name": player.name,
        "user_id": player.user_id,
        "permission": player.permission,
        "team": player.team,
        "callsign": player.callsign,
        "location": dict(player.location) if player.location is not None else None,
        "extra": dict(player.extra),
    }


def staff_to_dto(staff: StaffMember) -> dict[str, Any]:
    return {
        "name": staff.name,
        "callsign": staff.callsign,
        "permission": staff.permission,
        "extra": dict(staff.extra),
    }


def queue_entry_to_dto(entry: QueueEntry) -> dict[str, Any]:
    return {
        "player": entry.player,
        "position": entry.position,
        "timestamp": entry.timestamp,
        "extra": dict(entry.extra),
    }


def command_log_to_dto(entry: CommandLogEntry) -> dict[str, Any]:
    return {
        "player": entry.player,
        "command": entry.command,
        "timestamp": entry.timestamp,
        "extra": dict(entry.extra),
    }


def mod_call_to_dto(entry: ModCallEntry) -> dict[str, Any]:
    return {
        "player": entry.player,
        "reason": entry.reason,
        "location": entry.location,
        "timestamp": entry.timestamp,
        "extra": dict(entry.extra),
    }


def vehicle_to_dto(vehicle: Vehicle) -> dict[str, Any]:
    return {
        "owner": vehicle.owner,
        "model": vehicle.model,
        "color": vehicle.color,
        "plate": vehicle.plate,
        "team": vehicle.team,
        "extra": dict(vehicle.extra),
    }


def server_info_to_dto(server: ServerInfo) -> dict[str, Any]:
    return {
        "name": server.name,
        "owner": server.owner,
        "co_owner": server.co_owner,
        "current_players": server.current_players,
        "max_players": server.max_players,
        "join_key": server.join_key,
        "extra": dict(server.extra),
    }


def players_to_dto(players: list[Player]) -> list[dict[str, Any]]:
    return [player_to_dto(player) for player in players]


def staff_list_to_dto(staff_list: list[StaffMember]) -> list[dict[str, Any]]:
    return [staff_to_dto(staff) for staff in staff_list]


def queue_to_dto(queue: list[QueueEntry]) -> list[dict[str, Any]]:
    return [queue_entry_to_dto(entry) for entry in queue]


def vehicles_to_dto(vehicles: list[Vehicle]) -> list[dict[str, Any]]:
    return [vehicle_to_dto(vehicle) for vehicle in vehicles]


def command_logs_to_dto(entries: list[CommandLogEntry]) -> list[dict[str, Any]]:
    return [command_log_to_dto(entry) for entry in entries]


def mod_calls_to_dto(entries: list[ModCallEntry]) -> list[dict[str, Any]]:
    return [mod_call_to_dto(entry) for entry in entries]


def v2_bundle_to_dto(bundle: V2ServerBundle) -> dict[str, Any]:
    return {
        "server_name": bundle.server_name,
        "current_players": bundle.current_players,
        "max_players": bundle.max_players,
        "players": players_to_dto(bundle.players) if bundle.players is not None else None,
        "staff": staff_list_to_dto(bundle.staff) if bundle.staff is not None else None,
        "helpers": staff_list_to_dto(bundle.helpers) if bundle.helpers is not None else None,
        "join_logs": None
        if bundle.join_logs is None
        else [
            {
                "player": entry.player,
                "timestamp": entry.timestamp,
                "extra": dict(entry.extra),
            }
            for entry in bundle.join_logs
        ],
        "queue": queue_to_dto(bundle.queue) if bundle.queue is not None else None,
        "kill_logs": None
        if bundle.kill_logs is None
        else [
            {
                "killer": entry.killer,
                "victim": entry.victim,
                "weapon": entry.weapon,
                "timestamp": entry.timestamp,
                "extra": dict(entry.extra),
            }
            for entry in bundle.kill_logs
        ],
        "command_logs": command_logs_to_dto(bundle.command_logs) if bundle.command_logs is not None else None,
        "mod_calls": mod_calls_to_dto(bundle.mod_calls) if bundle.mod_calls is not None else None,
        "vehicles": vehicles_to_dto(bundle.vehicles) if bundle.vehicles is not None else None,
        "emergency_calls": None
        if bundle.emergency_calls is None
        else [emergency_call_to_dto(entry) for entry in bundle.emergency_calls],
        "extra": dict(bundle.extra),
    }


__all__ = [
    "command_log_to_dto",
    "command_logs_to_dto",
    "emergency_call_to_dto",
    "location_to_dto",
    "mod_call_to_dto",
    "mod_calls_to_dto",
    "player_to_dto",
    "players_to_dto",
    "queue_entry_to_dto",
    "queue_to_dto",
    "server_info_to_dto",
    "staff_list_to_dto",
    "staff_to_dto",
    "v2_bundle_to_dto",
    "vehicle_color_to_dto",
    "vehicle_to_dto",
    "vehicles_to_dto",
]
