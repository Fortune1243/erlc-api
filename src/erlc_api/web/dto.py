from __future__ import annotations

from typing import Any

from ..models import (
    CommandLogEntry,
    EmergencyCall,
    ModCallEntry,
    Player,
    PlayerLocation,
    ServerBundle,
    ServerInfo,
    StaffList,
    StaffMember,
    Vehicle,
    VehicleColor,
)


def location_to_dto(location: PlayerLocation) -> dict[str, Any]:
    return location.to_dict()


def vehicle_color_to_dto(color: VehicleColor) -> dict[str, Any]:
    return color.to_dict()


def emergency_call_to_dto(call: EmergencyCall) -> dict[str, Any]:
    return call.to_dict()


def player_to_dto(player: Player) -> dict[str, Any]:
    return player.to_dict()


def staff_to_dto(staff: StaffMember) -> dict[str, Any]:
    return staff.to_dict()


def staff_list_to_dto(staff: StaffList | list[StaffMember]) -> list[dict[str, Any]]:
    members = staff.members if isinstance(staff, StaffList) else staff
    return [staff_to_dto(member) for member in members]


def queue_entry_to_dto(entry: int) -> dict[str, Any]:
    return {"user_id": entry}


def queue_to_dto(queue: list[int]) -> list[dict[str, Any]]:
    return [queue_entry_to_dto(entry) for entry in queue]


def command_log_to_dto(entry: CommandLogEntry) -> dict[str, Any]:
    return entry.to_dict()


def command_logs_to_dto(entries: list[CommandLogEntry]) -> list[dict[str, Any]]:
    return [command_log_to_dto(entry) for entry in entries]


def mod_call_to_dto(entry: ModCallEntry) -> dict[str, Any]:
    return entry.to_dict()


def mod_calls_to_dto(entries: list[ModCallEntry]) -> list[dict[str, Any]]:
    return [mod_call_to_dto(entry) for entry in entries]


def vehicle_to_dto(vehicle: Vehicle) -> dict[str, Any]:
    return vehicle.to_dict()


def vehicles_to_dto(vehicles: list[Vehicle]) -> list[dict[str, Any]]:
    return [vehicle_to_dto(vehicle) for vehicle in vehicles]


def server_info_to_dto(server: ServerInfo) -> dict[str, Any]:
    return server.to_dict()


def players_to_dto(players: list[Player]) -> list[dict[str, Any]]:
    return [player_to_dto(player) for player in players]


def v2_bundle_to_dto(bundle: ServerBundle) -> dict[str, Any]:
    return bundle.to_dict()


server_bundle_to_dto = v2_bundle_to_dto


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
    "server_bundle_to_dto",
    "server_info_to_dto",
    "staff_list_to_dto",
    "staff_to_dto",
    "v2_bundle_to_dto",
    "vehicle_color_to_dto",
    "vehicle_to_dto",
    "vehicles_to_dto",
]
