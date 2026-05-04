from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


VALID_INCLUDES = frozenset(
    {
        "players",
        "staff",
        "join_logs",
        "queue",
        "kill_logs",
        "command_logs",
        "mod_calls",
        "emergency_calls",
        "vehicles",
    }
)


def _normalize_include(value: str) -> str:
    key = value.strip().lower().replace("-", "_")
    if key not in VALID_INCLUDES:
        raise ValueError(f"Unknown bundle include: {value}")
    return key


@dataclass(frozen=True)
class BundlePreset:
    name: str
    includes: frozenset[str] = field(default_factory=frozenset)
    description: str | None = None

    def __post_init__(self) -> None:
        name = self.name.strip().lower()
        if not name:
            raise ValueError("preset name cannot be blank.")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "includes", frozenset(_normalize_include(item) for item in self.includes))

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "includes": sorted(self.includes), "description": self.description}


class BundleRegistry:
    def __init__(self, presets: Iterable[BundlePreset] | None = None) -> None:
        self._presets: dict[str, BundlePreset] = {}
        for preset in presets or ():
            self.register(preset.name, preset.includes, description=preset.description)

    def register(self, name: str, includes: Iterable[str], *, description: str | None = None) -> BundlePreset:
        preset = BundlePreset(name=name, includes=frozenset(includes), description=description)
        self._presets[preset.name] = preset
        return preset

    def get(self, name: str) -> BundlePreset:
        key = name.strip().lower()
        try:
            return self._presets[key]
        except KeyError as exc:
            raise ValueError(f"Unknown bundle preset: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._presets)

    def presets(self) -> list[BundlePreset]:
        return [self._presets[name] for name in self.names()]


def default_registry() -> BundleRegistry:
    registry = BundleRegistry()
    registry.register("minimal", (), description="Server info only.")
    registry.register("players", ("players", "queue"), description="Player list and queue.")
    registry.register("dashboard", ("players", "staff", "queue", "vehicles", "emergency_calls"), description="Dashboard-ready server state.")
    registry.register("logs", ("join_logs", "kill_logs", "command_logs", "mod_calls"), description="Recent log sections.")
    registry.register(
        "ops",
        ("players", "staff", "queue", "command_logs", "mod_calls", "emergency_calls", "vehicles"),
        description="Operational bot and moderation state.",
    )
    registry.register("all", VALID_INCLUDES, description="Every v2 bundle include.")
    return registry


_REGISTRY = default_registry()


def register_preset(name: str, includes: Iterable[str], *, description: str | None = None) -> BundlePreset:
    return _REGISTRY.register(name, includes, description=description)


@dataclass(frozen=True)
class BundleRequest:
    includes: frozenset[str] = field(default_factory=frozenset)
    preset_name: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "includes", frozenset(_normalize_include(item) for item in self.includes))

    @classmethod
    def preset(cls, name: str, *, registry: BundleRegistry | None = None) -> BundleRequest:
        preset = (registry or _REGISTRY).get(name)
        return cls(includes=preset.includes, preset_name=preset.name)

    @classmethod
    def all(cls) -> BundleRequest:
        return cls.preset("all")

    def include(self, *names: str) -> BundleRequest:
        return BundleRequest(includes=self.includes | frozenset(_normalize_include(name) for name in names), preset_name=self.preset_name)

    def exclude(self, *names: str) -> BundleRequest:
        return BundleRequest(includes=self.includes - frozenset(_normalize_include(name) for name in names), preset_name=self.preset_name)

    def server_kwargs(self) -> dict[str, bool]:
        return {name: True for name in self.includes}

    def to_dict(self) -> dict[str, Any]:
        return {"preset_name": self.preset_name, "includes": sorted(self.includes)}


def resolve_request(request: str | Iterable[str] | BundleRequest | None = None, *, registry: BundleRegistry | None = None) -> BundleRequest:
    if request is None:
        return BundleRequest.preset("dashboard", registry=registry)
    if isinstance(request, BundleRequest):
        return request
    if isinstance(request, str):
        return BundleRequest.preset(request, registry=registry)
    return BundleRequest(includes=frozenset(request))


class AsyncBundle:
    def __init__(self, api: Any, *, registry: BundleRegistry | None = None, server_key: str | None = None) -> None:
        self.api = api
        self.registry = registry or _REGISTRY
        self.server_key = server_key

    async def fetch(
        self,
        request: str | Iterable[str] | BundleRequest | None = None,
        *,
        server_key: str | None = None,
        raw: bool = False,
    ) -> Any:
        bundle_request = resolve_request(request, registry=self.registry)
        return await self.api.server(server_key=server_key or self.server_key, raw=raw, **bundle_request.server_kwargs())

    async def __call__(self, request: str | Iterable[str] | BundleRequest | None = None, **kwargs: Any) -> Any:
        return await self.fetch(request, **kwargs)

    async def dashboard(self, **kwargs: Any) -> Any:
        return await self.fetch("dashboard", **kwargs)

    async def all(self, **kwargs: Any) -> Any:
        return await self.fetch("all", **kwargs)


class Bundle:
    def __init__(self, api: Any, *, registry: BundleRegistry | None = None, server_key: str | None = None) -> None:
        self.api = api
        self.registry = registry or _REGISTRY
        self.server_key = server_key

    def fetch(
        self,
        request: str | Iterable[str] | BundleRequest | None = None,
        *,
        server_key: str | None = None,
        raw: bool = False,
    ) -> Any:
        bundle_request = resolve_request(request, registry=self.registry)
        return self.api.server(server_key=server_key or self.server_key, raw=raw, **bundle_request.server_kwargs())

    def __call__(self, request: str | Iterable[str] | BundleRequest | None = None, **kwargs: Any) -> Any:
        return self.fetch(request, **kwargs)

    def dashboard(self, **kwargs: Any) -> Any:
        return self.fetch("dashboard", **kwargs)

    def all(self, **kwargs: Any) -> Any:
        return self.fetch("all", **kwargs)


__all__ = [
    "AsyncBundle",
    "Bundle",
    "BundlePreset",
    "BundleRegistry",
    "BundleRequest",
    "VALID_INCLUDES",
    "default_registry",
    "register_preset",
    "resolve_request",
]
