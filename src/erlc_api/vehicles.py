from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re
from typing import Any, Iterable, Literal

from . import _utility as u
from .models import Player, Vehicle, parse_player_identifier

VehicleName = Literal[
    "1977 Arrow Phoenix Nationals",
    "2024 Averon Anodic",
    "2023 Averon Bremen VS Garde",
    "2020 Averon LM R",
    "2020 Averon LM",
    "2022 Averon Q8",
    "2020 Averon RS3",
    "2010 Averon S5",
    "2020 BKM Munich",
    "2020 BKM Risen Roadster",
    "2009 Bullhorn BH15",
    "2022 Bullhorn Determinator SFP Fury Blackjack Widebody",
    "2022 Bullhorn Determinator SFP Fury",
    "2022 Bullhorn Determinator C/T",
    "2008 Bullhorn Determinator",
    "1988 Bullhorn Foreman",
    "1969 Bullhorn Prancer Colonel Fields",
    "2020 Bullhorn Prancer C/T",
    "2020 Bullhorn Prancer Fury Widebody",
    "2011 Bullhorn Prancer S",
    "1969 Bullhorn Prancer Talladega",
    "1969 Bullhorn Prancer",
    "2022 Bullhorn Pueblo V6",
    "2022 Bullhorn Pueblo SFP Fury",
    "2024 Celestial Truckatron",
    "2022 Celestial Type-5",
    "2024 Celestial Type-6",
    "2022 Celestial Type-7",
    "2016 Chevlon Amigo LZR",
    "2016 Chevlon Amigo S",
    "2011 Chevlon Amigo ZL1",
    "2011 Chevlon Amigo S",
    "1994 Chevlon Antelope",
    "2002 Chevlon Camion GMT 800 LTS",
    "2002 Chevlon Camion GMT 800 LT",
    "2002 Chevlon Camion GMT 800 S",
    "2008 Chevlon Camion",
    "2018 Chevlon Camion",
    "2021 Chevlon Camion",
    "1992 Chevlon Captain",
    "2009 Chevlon Captain",
    "1994 Chevlon Captain LTZ",
    "2006 Chevlon Commuter Van",
    "2014 Chevlon Corbeta 1M Edition",
    "2023 Chevlon Corbeta 8",
    "1967 Chevlon Corbeta C2",
    "2014 Chevlon Corbeta RZR",
    "2014 Chevlon Corbeta X08",
    "1981 Chevlon Inferno",
    "2007 Chevlon Landslide",
    "1981 Chevlon L/15",
    "1981 Chevlon L/15 Side Step",
    "1981 Chevlon L/35 Extended",
    "2019 Chevlon Platoro",
    "2005 Chevlon Revver",
    "2005 Chryslus Champion",
    "2014 Elysion Slick",
    "1956 Falcon Advance 100 Holiday Edition",
    "1956 Falcon Advance 100",
    "2020 Falcon Advance 350 Royal Ranch",
    "2020 Falcon Advance 350",
    "2020 Falcon Advance 450 Royal Ranch",
    "2020 Falcon Advance 450",
    "2017 Falcon Aquarius STP",
    "1934 Falcon Coupe",
    "1934 Falcon Coupe Hotrod",
    "2024 Falcon eStallion",
    "2021 Falcon Heritage",
    "2022 Falcon Heritage Track",
    "2003 Falcon Prime Eques",
    "2021 Falcon Rampage Beast",
    "2021 Falcon Rampage Bigfoot 2-Door",
    "2021 Falcon Rampage Prairie",
    "2024 Falcon Scavenger Royal Ranch",
    "2013 Falcon Scavenger",
    "2016 Falcon Scavenger",
    "1969 Falcon Stallion 350",
    "2015 Falcon Stallion 350",
    "2003 Falcon Traveller",
    "2022 Ferdinand Jalapeno Turbo",
    "2020 Ferrari F8 Tributo",
    "2023 Kovac Heladera",
    "1995 Leland Birchwood Hearse",
    "2010 Leland LTS",
    "2023 Leland LTS5-V Blackwing",
    "1959 Leland Series 67 Skyview",
    "2020 Leland Vault",
    "Lawn Mower",
    "2022 Navara Boundary",
    "2013 Navara Horizon",
    "2020 Navara Imperium",
    "2020 Overland Apache SFP",
    "1995 Overland Apache",
    "2011 Overland Apache",
    "2018 Overland Buckaroo",
    "2025 Pea Car",
    "1968 Sentinel Platinum",
    "2011 Silhouette Carbon",
    "2020 Strugatti Ettore",
    "2021 Stuttgart Executive",
    "2022 Stuttgart Landschaft",
    "2021 Stuttgart Vierturig",
    "2022 Sumo Reflexion",
    "2016 Surrey 650S",
    "2021 Takeo Experience",
    "2022 Terrain Traveller",
    "2023 Vellfire Everest VRD Max",
    "1995 Vellfire Evertt Extended Cab",
    "2019 Vellfire Pioneer Targa",
    "2019 Vellfire Pioneer",
    "2022 Vellfire Prairie",
    "2009 Vellfire Prima",
    "2020 Vellfire Riptide",
    "1984 Vellfire Runabout",
    "Bank Truck",
    "2003 Falcon Prime Eques Taxi",
    "2013 Falcon Scavenger Security",
    "2024 Falcon Scavenger Taxi",
    "Farm Tractor 5100M",
    "Front-Loader Garbage Truck",
    "Fuel Tanker",
    "Garbage Truck",
    "La Mesa Food Truck",
    "2018 Leland Limo",
    "Mail Truck",
    "Mail Van",
    "Metro Transit Bus",
    "News Van",
    "Shuttle Bus",
    "Three Guys Food Truck",
    "4-Wheeler",
    "Canyon Descender",
    "1956 Falcon Advance 600 Pumper",
    "1969 Bullhorn Prancer HotRod",
    "1981 Chevlon L/35 Flatbed Tow Truck",
    "1981 Chevlon L15 Brush Truck",
    "1994 Chevlon Antelope SS",
    "2000 Chevlon Camion PPV",
    "2002 Falcon Traveller",
    "2003 Falcon Prime Eques Interceptor",
    "2005 Mobile Command",
    "2008 Chevlon Camion PPV",
    "2009 Bullhorn BH15 SSV",
    "2009 Chevlon Captain PPV",
    "2011 Bullhorn Prancer Pursuit",
    "2011 Chevlon Amigo LZR",
    "2013 Falcon Interceptor Utility",
    "2015 Bullhorn Prancer Pursuit",
    "2017 Falcon Interceptor Sedan",
    "2018 Chevlon Camion PPV",
    "2018 Falcon Global 450 Ambulance",
    "2018 Falcon Global 450 Utility",
    "2019 Chevlon Platoro PPV",
    "2019 Falcon Interceptor Utility",
    "2020 Brush Falcon Advance+",
    "2020 Bullhorn Prancer Fury Widebody Pursuit",
    "2020 Emergency Services Falcon Advance+",
    "2020 Falcon Advance 450 Ambulance",
    "2020 Falcon Advance 450 Bucket Truck",
    "2020 Falcon Advance 450 Roadside Assist",
    "2020 Falcon Advance 450 Tow Truck",
    "2020 Squad Falcon Advance+",
    "2020 Stuttgart Runner Prisoner Transport",
    "2021 Chevlon Camion PPV",
    "2021 Falcon Rampage Interceptor",
    "2022 Bullhorn Pueblo Pursuit",
    "2024 Falcon Interceptor Utility",
    "Prisoner Transport Bus",
    "2011 SWAT Armored Truck",
    "Heavy Rescue",
    "Medical Bus",
    "Mobile Command Center",
    "Redline Fire Engine",
    "2014 Redline Heavy Tanker",
    "Redline Midmount Ladder",
    "Redline Rearmount Ladder",
    "2014 Redline Tanker",
    "2014 Redline Type 3 Brush Truck",
    "Special Operations Unit",
    "2010 Aikawa Street Sweeper",
    "2015 Explorer Dump Truck",
    "2015 Explorer Flatbed Tow Truck",
    "2015 Explorer Salt Truck",
    "2015 Explorer Transport Truck",
    "Front Loader Tractor",
    "Forklift",
    "1995 Vellfire Evertt Crew Cab",
    "2013 Vinnimade Heavy Wrecker",
]

VehicleModel = str

# Catalog inspired by TychoTeam/prc.api-py's MIT-licensed vehicle typing work:
# https://github.com/TychoTeam/prc.api-py
VEHICLE_NAMES: tuple[str, ...] = tuple(VehicleName.__args__)  # type: ignore[attr-defined]
SECONDARY_VEHICLES = frozenset({"4-Wheeler", "Canyon Descender", "Forklift", "Lawn Mower"})
PRESTIGE_MODELS = frozenset(
    {
        "Averon LM R",
        "Averon LM",
        "Averon Q8",
        "Averon RS3",
        "Averon S5",
        "BKM Munich",
        "Chevlon Corbeta 1M Edition",
        "Chevlon Corbeta 8",
        "Chevlon Corbeta RZR",
        "Chevlon Corbeta X08",
        "Falcon Heritage Track",
        "Falcon Heritage",
        "Ferdinand Jalapeno Turbo",
        "Ferrari F8 Tributo",
        "Leland LTS5-V Blackwing",
        "Leland Vault",
        "Silhouette Carbon",
        "Strugatti Ettore",
        "Stuttgart Vierturig",
        "Surrey 650S",
        "Takeo Experience",
        "Terrain Traveller",
    }
)
FICTIONAL_TEXTURES = frozenset({"Standard", "Ghost", "SWAT", "Supervisor"})
DEFAULT_TEXTURES = frozenset({*FICTIONAL_TEXTURES, "Undercover"})
_YEAR_RE = re.compile(r"^(?P<prefix>\d{4})\s+(?P<rest>.+)$|^(?P<rest2>.+?)\s+(?P<suffix>\d{4})$")


@dataclass(frozen=True)
class VehicleCatalogEntry:
    full_name: str
    model: str
    year: int | None = None
    is_secondary: bool = False
    is_prestige: bool = False


@dataclass(frozen=True)
class VehicleParseResult:
    raw_name: str | None
    full_name: str | None
    model: str | None
    year: int | None = None
    catalog_entry: VehicleCatalogEntry | None = None
    is_known: bool = False
    is_secondary: bool = False
    is_prestige: bool = False


@dataclass(frozen=True)
class VehicleSummary:
    total: int
    by_model: dict[str, int]
    by_color: dict[str, int]
    by_owner: dict[str, int]
    primary: int
    secondary: int
    prestige: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "by_model": self.by_model,
            "by_color": self.by_color,
            "by_owner": self.by_owner,
            "primary": self.primary,
            "secondary": self.secondary,
            "prestige": self.prestige,
        }


def _clean(text: Any) -> str:
    return " ".join(str(text or "").strip().split())


def _norm(text: Any) -> str:
    return _clean(text).casefold()


def _split_year(name: str | None) -> tuple[str | None, int | None]:
    text = _clean(name)
    if not text:
        return None, None
    match = _YEAR_RE.match(text)
    if match is None:
        return text, None
    year_text = match.group("prefix") or match.group("suffix")
    rest = match.group("rest") or match.group("rest2")
    year = int(year_text) if year_text and 1900 <= int(year_text) <= 2100 else None
    return _clean(rest), year


def _entry(name: str) -> VehicleCatalogEntry:
    model, year = _split_year(name)
    model = model or name
    return VehicleCatalogEntry(
        full_name=name,
        model=model,
        year=year,
        is_secondary=name in SECONDARY_VEHICLES,
        is_prestige=model in PRESTIGE_MODELS,
    )


VEHICLE_CATALOG: tuple[VehicleCatalogEntry, ...] = tuple(_entry(name) for name in VEHICLE_NAMES)
_BY_FULL_NAME = {_norm(entry.full_name): entry for entry in VEHICLE_CATALOG}
_BY_MODEL = {_norm(entry.model): entry for entry in VEHICLE_CATALOG}


def parse_vehicle_name(name: str | None) -> VehicleParseResult:
    text = _clean(name)
    if not text:
        return VehicleParseResult(raw_name=name, full_name=None, model=None)
    entry = _BY_FULL_NAME.get(_norm(text))
    model, year = _split_year(text)
    if entry is None and model is not None:
        entry = _BY_MODEL.get(_norm(model))
    if entry is not None:
        return VehicleParseResult(
            raw_name=name,
            full_name=entry.full_name,
            model=entry.model,
            year=entry.year if entry.year is not None else year,
            catalog_entry=entry,
            is_known=True,
            is_secondary=entry.is_secondary,
            is_prestige=entry.is_prestige,
        )
    return VehicleParseResult(
        raw_name=name,
        full_name=text,
        model=model,
        year=year,
        is_known=False,
        is_secondary=text in SECONDARY_VEHICLES,
        is_prestige=(model or text) in PRESTIGE_MODELS,
    )


def normalize_plate(plate: Any) -> str | None:
    text = _clean(plate)
    return text.upper() if text else None


def is_default_texture(texture: Any) -> bool:
    text = _clean(texture) or "Standard"
    return text in DEFAULT_TEXTURES


def is_fictional_texture(texture: Any) -> bool:
    text = _clean(texture) or "Standard"
    return text in FICTIONAL_TEXTURES


def is_custom_texture(texture: Any) -> bool:
    return not is_default_texture(texture)


def _vehicle_owner_key(vehicle: Vehicle) -> str:
    name, user_id = parse_player_identifier(vehicle.owner)
    return str(user_id or name or vehicle.owner or "").casefold()


def _player_key(player: Player) -> str:
    return str(player.user_id or player.name or player.player or "").casefold()


class VehicleTools:
    def __init__(self, data: Any) -> None:
        self.vehicles = u.vehicles(data)

    def all(self) -> list[Vehicle]:
        return list(self.vehicles)

    def by_owner(self, owner: str | int) -> list[Vehicle]:
        key = str(owner).casefold()
        return [
            vehicle
            for vehicle in self.vehicles
            if key in {_vehicle_owner_key(vehicle), _norm(vehicle.owner_name), _norm(vehicle.owner)}
        ]

    def by_team(self, team: str, *, players: Iterable[Player] | None = None) -> list[Vehicle]:
        if players is None:
            return [vehicle for vehicle in self.vehicles if u.equals(vehicle.team, team)]
        player_by_key = {_player_key(player): player for player in players}
        return [
            vehicle
            for vehicle in self.vehicles
            if (player := player_by_key.get(_vehicle_owner_key(vehicle))) is not None and u.equals(player.team, team)
        ]

    def by_color(self, color_name: str) -> list[Vehicle]:
        return [vehicle for vehicle in self.vehicles if u.equals(vehicle.color_name, color_name) or u.equals(vehicle.color_hex, color_name)]

    def by_model(self, name: str) -> list[Vehicle]:
        return [vehicle for vehicle in self.vehicles if u.equals(vehicle.model_name, name)]

    def by_name(self, name: str) -> list[Vehicle]:
        return [vehicle for vehicle in self.vehicles if u.equals(vehicle.full_name, name)]

    def by_texture(self, texture: str) -> list[Vehicle]:
        return [vehicle for vehicle in self.vehicles if u.equals(vehicle.texture or "Standard", texture)]

    def find_plate(self, plate: str) -> list[Vehicle]:
        needle = normalize_plate(plate)
        return [vehicle for vehicle in self.vehicles if needle is not None and needle in (vehicle.normalized_plate or "")]

    def duplicate_plates(self) -> dict[str, list[Vehicle]]:
        groups: dict[str, list[Vehicle]] = {}
        for vehicle in self.vehicles:
            plate = vehicle.normalized_plate
            if plate:
                groups.setdefault(plate, []).append(vehicle)
        return {plate: items for plate, items in groups.items() if len(items) > 1}

    def abandoned(self, online_players: Iterable[Player]) -> list[Vehicle]:
        online = {_player_key(player) for player in online_players}
        return [vehicle for vehicle in self.vehicles if _vehicle_owner_key(vehicle) not in online]

    def primary(self) -> list[Vehicle]:
        return [vehicle for vehicle in self.vehicles if not vehicle.is_secondary]

    def secondary(self) -> list[Vehicle]:
        return [vehicle for vehicle in self.vehicles if vehicle.is_secondary]

    def prestige(self) -> list[Vehicle]:
        return [vehicle for vehicle in self.vehicles if vehicle.is_prestige]

    def summary(self) -> VehicleSummary:
        by_model = Counter(vehicle.model_name or "Unknown" for vehicle in self.vehicles)
        by_color = Counter(vehicle.color or "Unknown" for vehicle in self.vehicles)
        by_owner = Counter(vehicle.owner_name or "Unknown" for vehicle in self.vehicles)
        return VehicleSummary(
            total=len(self.vehicles),
            by_model=dict(by_model),
            by_color=dict(by_color),
            by_owner=dict(by_owner),
            primary=len(self.primary()),
            secondary=len(self.secondary()),
            prestige=len(self.prestige()),
        )


@dataclass(frozen=True)
class PlayerVehicleView:
    player: Player
    vehicles: list[Vehicle]


@dataclass(frozen=True)
class VehicleOwnerView:
    vehicle: Vehicle
    owner_player: Player | None


class PlayerVehicleBundle:
    def __init__(self, players: Iterable[Player], vehicles: Iterable[Vehicle]) -> None:
        self.players = list(players)
        self.vehicles = list(vehicles)

    def _find_player(self, query: str | int) -> Player | None:
        text = str(query).casefold()
        for player in self.players:
            if str(player.user_id) == text or _norm(player.name) == text or _norm(player.player) == text:
                return player
        return None

    def player(self, query: str | int) -> PlayerVehicleView | None:
        player = self._find_player(query)
        if player is None:
            return None
        return PlayerVehicleView(player=player, vehicles=self.vehicles_for(player))

    def vehicle(self, plate_or_name: str) -> VehicleOwnerView | None:
        for vehicle in self.vehicles:
            if u.contains(vehicle.plate, plate_or_name) or u.contains(vehicle.name, plate_or_name):
                return VehicleOwnerView(vehicle=vehicle, owner_player=self.owner_for(vehicle))
        return None

    def vehicles_for(self, player: Player | str | int) -> list[Vehicle]:
        key = _player_key(player) if isinstance(player, Player) else str(player).casefold()
        return [vehicle for vehicle in self.vehicles if key in {_vehicle_owner_key(vehicle), _norm(vehicle.owner_name)}]

    def owner_for(self, vehicle: Vehicle | str) -> Player | None:
        if isinstance(vehicle, str):
            view = self.vehicle(vehicle)
            return view.owner_player if view else None
        wanted = _vehicle_owner_key(vehicle)
        return next((player for player in self.players if _player_key(player) == wanted), None)


__all__ = [
    "DEFAULT_TEXTURES",
    "FICTIONAL_TEXTURES",
    "PRESTIGE_MODELS",
    "PlayerVehicleBundle",
    "PlayerVehicleView",
    "SECONDARY_VEHICLES",
    "VehicleCatalogEntry",
    "VehicleModel",
    "VehicleName",
    "VehicleOwnerView",
    "VehicleParseResult",
    "VehicleSummary",
    "VehicleTools",
    "VEHICLE_CATALOG",
    "VEHICLE_NAMES",
    "is_custom_texture",
    "is_default_texture",
    "is_fictional_texture",
    "normalize_plate",
    "parse_vehicle_name",
]
