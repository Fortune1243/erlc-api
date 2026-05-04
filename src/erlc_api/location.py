from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from . import _utility as u
from .models import EmergencyCall, Player, PlayerLocation


_MAP_URLS = {
    ("fall", "blank"): "https://api.policeroleplay.community/maps/fall_blank.png",
    ("fall", "postals"): "https://api.policeroleplay.community/maps/fall_postals.png",
    ("winter", "blank"): "https://api.policeroleplay.community/maps/snow_blank.png",
    ("winter", "postals"): "https://api.policeroleplay.community/maps/snow_postals.png",
    ("snow", "blank"): "https://api.policeroleplay.community/maps/snow_blank.png",
    ("snow", "postals"): "https://api.policeroleplay.community/maps/snow_postals.png",
}


@dataclass(frozen=True)
class Coordinate:
    x: float
    z: float
    postal_code: str | None = None
    street_name: str | None = None
    building_number: str | None = None

    @property
    def location_x(self) -> float:
        return self.x

    @property
    def location_z(self) -> float:
        return self.z

    def to_dict(self) -> dict[str, Any]:
        return {
            "x": self.x,
            "z": self.z,
            "postal_code": self.postal_code,
            "street_name": self.street_name,
            "building_number": self.building_number,
        }


@dataclass(frozen=True)
class LocationQuery:
    postal_code: str | None = None
    street_name: str | None = None
    center: Coordinate | None = None
    radius: float | None = None


@dataclass(frozen=True)
class LocationMatch:
    item: Any
    coordinate: Coordinate
    distance: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "item": u.model_dict(self.item),
            "coordinate": self.coordinate.to_dict(),
            "distance": self.distance,
        }


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _coordinate_from_mapping(value: Mapping[str, Any]) -> Coordinate | None:
    x = _as_float(value.get("LocationX", value.get("location_x", value.get("x"))))
    z = _as_float(value.get("LocationZ", value.get("location_z", value.get("z"))))
    if x is None or z is None:
        return None
    return Coordinate(
        x=x,
        z=z,
        postal_code=u.as_text(value.get("PostalCode", value.get("postal_code"))),
        street_name=u.as_text(value.get("StreetName", value.get("street_name"))),
        building_number=u.as_text(value.get("BuildingNumber", value.get("building_number"))),
    )


def _coordinate_from_position(value: Any) -> Coordinate | None:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, bytearray, Mapping)):
        return None
    items = list(value)
    if len(items) < 2:
        return None
    x = _as_float(items[0])
    z = _as_float(items[1])
    if x is None or z is None:
        return None
    return Coordinate(x=x, z=z)


def as_coordinate(value: Any, z: Any = None, **metadata: Any) -> Coordinate | None:
    if isinstance(value, Coordinate):
        return value
    if z is not None:
        x_value = _as_float(value)
        z_value = _as_float(z)
        if x_value is None or z_value is None:
            return None
        return Coordinate(
            x=x_value,
            z=z_value,
            postal_code=u.as_text(metadata.get("postal_code")),
            street_name=u.as_text(metadata.get("street_name")),
            building_number=u.as_text(metadata.get("building_number")),
        )
    if isinstance(value, PlayerLocation):
        if value.location_x is None or value.location_z is None:
            return None
        return Coordinate(
            x=value.location_x,
            z=value.location_z,
            postal_code=value.postal_code,
            street_name=value.street_name,
            building_number=value.building_number,
        )
    if isinstance(value, Player):
        return as_coordinate(value.location)
    if isinstance(value, EmergencyCall):
        return _coordinate_from_position(value.position)
    if isinstance(value, Mapping):
        location = value.get("Location", value.get("location"))
        if location is not None:
            from_location = as_coordinate(location)
            if from_location is not None:
                return from_location
        position = value.get("Position", value.get("position"))
        if position is not None:
            from_position = _coordinate_from_position(position)
            if from_position is not None:
                return from_position
        return _coordinate_from_mapping(value)
    location = getattr(value, "location", None)
    if location is not None:
        return as_coordinate(location)
    position = getattr(value, "position", None)
    if position is not None:
        return _coordinate_from_position(position)
    return None


def _items_from(data: Any) -> list[Any]:
    if data is None:
        return []
    items: list[Any] = []
    items.extend(u.players(data))
    items.extend(u.emergency_calls(data))
    if items:
        return items
    return u.rows(data)


class LocationTools:
    """Geometry helpers for v2 player locations and emergency call positions."""

    def __init__(self, data: Any = None) -> None:
        self.data = data

    def point(self, value: Any, z: Any = None, **metadata: Any) -> Coordinate:
        coordinate = as_coordinate(value, z, **metadata)
        if coordinate is None:
            raise ValueError("Could not read a coordinate from the provided value.")
        return coordinate

    def distance(self, a: Any, b: Any) -> float:
        first = self.point(a)
        second = self.point(b)
        return hypot(first.x - second.x, first.z - second.z)

    def matches(self, items: Any = None) -> list[LocationMatch]:
        out: list[LocationMatch] = []
        for item in _items_from(self.data if items is None else items):
            coordinate = as_coordinate(item)
            if coordinate is not None:
                out.append(LocationMatch(item=item, coordinate=coordinate))
        return out

    def nearest(
        self,
        origin: Any,
        items: Any = None,
        *,
        limit: int = 1,
        max_distance: float | None = None,
    ) -> list[LocationMatch]:
        if limit <= 0:
            raise ValueError("limit must be greater than zero.")
        center = self.point(origin)
        matches: list[LocationMatch] = []
        for match in self.matches(items):
            distance = self.distance(center, match.coordinate)
            if max_distance is not None and distance > max_distance:
                continue
            matches.append(LocationMatch(item=match.item, coordinate=match.coordinate, distance=distance))
        matches.sort(key=lambda item: item.distance if item.distance is not None else float("inf"))
        return matches[:limit]

    def within_radius(self, origin: Any, radius: float, items: Any = None) -> list[LocationMatch]:
        if radius < 0:
            raise ValueError("radius cannot be negative.")
        return self.nearest(origin, items, limit=max(1, len(_items_from(self.data if items is None else items))), max_distance=radius)

    def by_postal(self, postal_code: str, items: Any = None, *, exact: bool = True) -> list[LocationMatch]:
        wanted = u.normalize_text(postal_code)
        out = []
        for match in self.matches(items):
            candidate = u.normalize_text(match.coordinate.postal_code)
            ok = candidate == wanted if exact else wanted in candidate
            if ok:
                out.append(match)
        return out

    def by_street(self, street_name: str, items: Any = None, *, contains: bool = True) -> list[LocationMatch]:
        wanted = u.normalize_text(street_name)
        out = []
        for match in self.matches(items):
            candidate = u.normalize_text(match.coordinate.street_name)
            ok = wanted in candidate if contains else candidate == wanted
            if ok:
                out.append(match)
        return out

    def nearest_players_to_call(
        self,
        call: Any,
        players: Any = None,
        *,
        limit: int = 5,
        max_distance: float | None = None,
    ) -> list[LocationMatch]:
        player_items = u.players(self.data if players is None else players)
        return self.nearest(call, player_items, limit=limit, max_distance=max_distance)

    @staticmethod
    def official_map_url(*, season: str = "fall", layer: str = "postals") -> str:
        key = (season.strip().lower(), layer.strip().lower())
        try:
            return _MAP_URLS[key]
        except KeyError as exc:
            raise ValueError("Unknown map season/layer. Use fall|winter|snow and blank|postals.") from exc


@dataclass(frozen=True)
class MapPoint:
    coordinate: Coordinate
    label: str | None = None
    color: tuple[int, int, int] = (255, 64, 64)


class MapRenderer:
    """Optional Pillow-backed map overlay renderer."""

    def _load_pillow(self) -> Any:
        try:
            from PIL import Image, ImageDraw
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("Map rendering requires `pip install erlc-api.py[location]`.") from exc
        return Image, ImageDraw

    def render_points(
        self,
        image_path: str | Path,
        points: Iterable[Any],
        *,
        output_path: str | Path | None = None,
        bounds: tuple[float, float, float, float] | None = None,
        transform: Callable[[Coordinate, tuple[int, int]], tuple[float, float]] | None = None,
        marker_radius: int = 6,
    ) -> Any:
        if marker_radius <= 0:
            raise ValueError("marker_radius must be greater than zero.")
        if bounds is None and transform is None:
            raise ValueError("Pass bounds=... or transform=... so game coordinates can be mapped to image pixels.")

        Image, ImageDraw = self._load_pillow()
        image = Image.open(image_path).convert("RGBA")
        draw = ImageDraw.Draw(image)
        size = image.size

        def to_pixel(coordinate: Coordinate) -> tuple[float, float]:
            if transform is not None:
                return transform(coordinate, size)
            assert bounds is not None
            min_x, min_z, max_x, max_z = bounds
            if max_x == min_x or max_z == min_z:
                raise ValueError("bounds cannot have zero width or height.")
            px = (coordinate.x - min_x) / (max_x - min_x) * size[0]
            py = size[1] - ((coordinate.z - min_z) / (max_z - min_z) * size[1])
            return px, py

        for point in points:
            map_point = point if isinstance(point, MapPoint) else MapPoint(coordinate=LocationTools().point(point))
            x, y = to_pixel(map_point.coordinate)
            r = marker_radius
            draw.ellipse((x - r, y - r, x + r, y + r), fill=map_point.color + (220,))
            if map_point.label:
                draw.text((x + r + 2, y - r), map_point.label, fill=map_point.color + (255,))

        if output_path is not None:
            image.save(output_path)
        return image


__all__ = [
    "Coordinate",
    "LocationMatch",
    "LocationQuery",
    "LocationTools",
    "MapPoint",
    "MapRenderer",
    "as_coordinate",
]
