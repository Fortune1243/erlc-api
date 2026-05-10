from __future__ import annotations

import builtins

import pytest

from erlc_api import CommandResult, EmergencyCall, Player, PlayerLocation, ServerBundle, StaffList, Vehicle
from erlc_api.bundle import AsyncBundle, Bundle, BundleRegistry, BundleRequest
from erlc_api.cache import READ_METHODS, AsyncCachedClient, CachedClient, MemoryCache
from erlc_api.command_flows import CommandFlowBuilder, CommandTemplate
from erlc_api.diagnostics import diagnose_command_result, diagnose_error, diagnose_status
from erlc_api.discord_tools import DiscordEmbed, DiscordFormatter, chunks, safe_text
from erlc_api.location import Coordinate, LocationTools, MapRenderer
from erlc_api.multiserver import AsyncMultiServer, MultiServer, ServerRef
from erlc_api.rules import AsyncRuleEngine, Conditions, RuleEngine
from erlc_api.status import AsyncStatus, Status, StatusBuilder


def _bundle(name: str = "Main", *, extra_player: bool = False) -> ServerBundle:
    players = [
        Player(
            name="Avi",
            player="Avi:1",
            user_id=1,
            team="Police",
            location=PlayerLocation(location_x=0, location_z=0, postal_code="100", street_name="Main Street"),
        ),
        Player(
            name="Bee",
            player="Bee:2",
            user_id=2,
            team="Sheriff",
            location=PlayerLocation(location_x=3, location_z=4, postal_code="101", street_name="Park Street"),
        ),
    ]
    if extra_player:
        players.append(Player(name="Cat", player="Cat:3", user_id=3, team="Civilian"))
    return ServerBundle(
        name=name,
        current_players=len(players),
        max_players=2 if not extra_player else 40,
        players=players,
        queue=[9, 10] if extra_player else [9],
        staff=StaffList(admins={1: "Avi"}),
        vehicles=[Vehicle(name="Falcon", owner="Avi", plate="ABC")],
        emergency_calls=[
            EmergencyCall(team="Police", caller=1, position=[0.0, 5.0], started_at=100, call_number=7),
        ],
    )


class _SyncAPI:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None, dict[str, object]]] = []
        self.commands = 0

    def server(self, *, server_key=None, raw=False, **kwargs):  # noqa: ANN001, ARG002
        self.calls.append(("server", server_key, kwargs))
        if server_key == "bad":
            raise RuntimeError("server failed")
        return _bundle(str(server_key or "default"), extra_player=bool(kwargs.get("command_logs")))

    def players(self, *, server_key=None):  # noqa: ANN001
        self.calls.append(("players", server_key, {}))
        return _bundle().players

    def command(self, command, *, server_key=None, dry_run=False):  # noqa: ANN001, ARG002
        self.commands += 1
        return CommandResult(message="Success", success=True)


class _AsyncAPI:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None, dict[str, object]]] = []
        self.commands = 0

    async def server(self, *, server_key=None, raw=False, **kwargs):  # noqa: ANN001, ARG002
        self.calls.append(("server", server_key, kwargs))
        if server_key == "bad":
            raise RuntimeError("server failed")
        return _bundle(str(server_key or "default"), extra_player=bool(kwargs.get("command_logs")))

    async def players(self, *, server_key=None):  # noqa: ANN001
        self.calls.append(("players", server_key, {}))
        return _bundle().players

    async def command(self, command, *, server_key=None, dry_run=False):  # noqa: ANN001, ARG002
        self.commands += 1
        return CommandResult(message="Success", success=True)


def test_location_geometry_queries_and_optional_render_error(monkeypatch) -> None:
    bundle = _bundle()
    tools = LocationTools(bundle)

    assert tools.distance(Coordinate(0, 0), Coordinate(3, 4)) == 5
    assert tools.nearest(Coordinate(0, 0), limit=1)[0].item.name == "Avi"
    assert [match.item.name for match in tools.within_radius(Coordinate(0, 0), 5, bundle.players)] == ["Avi", "Bee"]
    assert tools.by_postal("101")[0].item.name == "Bee"
    assert tools.by_street("main")[0].item.name == "Avi"
    assert tools.nearest_players_to_call(bundle.emergency_calls[0], limit=1)[0].item.name == "Bee"
    assert LocationTools.official_map_url(season="winter", layer="blank").endswith("snow_blank.png")

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("PIL"):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RuntimeError, match="erlc-api\\.py\\[location\\]"):
        MapRenderer().render_points("missing.png", [Coordinate(0, 0)], bounds=(-1, -1, 1, 1))


@pytest.mark.asyncio
async def test_bundle_presets_custom_registry_and_fetchers() -> None:
    registry = BundleRegistry()
    registry.register("miniops", ["players", "command_logs"])
    request = BundleRequest.preset("miniops", registry=registry).include("queue")
    assert request.server_kwargs() == {"command_logs": True, "players": True, "queue": True}

    sync_api = _SyncAPI()
    bundle = Bundle(sync_api, registry=registry).fetch(request, server_key="one")
    assert bundle.name == "one"
    assert sync_api.calls[0] == ("server", "one", {"command_logs": True, "players": True, "queue": True})

    async_api = _AsyncAPI()
    async_bundle = await AsyncBundle(async_api).dashboard(server_key="two")
    assert async_bundle.name == "two"
    assert async_api.calls[0][2]["players"] is True

    with pytest.raises(ValueError, match="Unknown bundle include"):
        BundleRequest(includes=frozenset({"missing"}))


@pytest.mark.asyncio
async def test_rules_sync_async_and_no_command_side_effects() -> None:
    matches: list[str] = []
    engine = RuleEngine()
    engine.add(
        "queue",
        Conditions.queue_length(at_least=1),
        severity="warning",
        message="Queue is active",
        callback=lambda match: matches.append(match.rule_name),
    )
    result = engine.evaluate(_bundle())
    assert result[0].message == "Queue is active"
    assert matches == ["queue"]

    async_matches: list[str] = []

    async def async_callback(match):
        async_matches.append(match.rule_name)

    async_engine = AsyncRuleEngine()
    async_engine.add("players", Conditions.player_count(at_least=2), callback=async_callback)
    assert (await async_engine.evaluate(_bundle()))[0].rule_name == "players"
    assert async_matches == ["players"]

    api = _SyncAPI()
    engine.evaluate(_bundle())
    assert api.commands == 0


@pytest.mark.asyncio
async def test_multiserver_collects_errors_and_aggregates() -> None:
    sync_api = _SyncAPI()
    manager = MultiServer(
        sync_api,
        [ServerRef("main", "one"), ServerRef("broken", "bad")],
        concurrency=1,
    )
    results = manager.server(preset="players")
    assert [result.ok for result in results] == [True, False]
    assert "server failed" in str(results[1].error)
    assert manager.aggregate()["errors"] == 1
    with pytest.raises(ValueError, match="read-only"):
        manager.call("command")

    async_api = _AsyncAPI()
    async_manager = AsyncMultiServer(async_api, [("main", "one"), ("broken", "bad")], concurrency=2)
    async_results = await async_manager.status()
    assert [result.ok for result in async_results] == [True, False]
    assert (await async_manager.aggregate())["ok"] == 1


@pytest.mark.asyncio
async def test_status_diagnostics_and_discord_payloads() -> None:
    status = StatusBuilder(_bundle()).build()
    assert status.health == "warning"
    assert status.to_dict()["queue_count"] == 1

    sync_status = Status(_SyncAPI()).get(server_key="one")
    assert sync_status.server_name == "one"
    async_status = await AsyncStatus(_AsyncAPI()).get(server_key="two")
    assert async_status.server_name == "two"

    diagnostics = diagnose_status(status)
    assert diagnostics.highest_severity == "warning"
    assert diagnose_command_result(CommandResult(message="invalid command", success=None)).ok is False
    assert diagnose_error(RuntimeError("boom")).highest_severity == "error"

    formatter = DiscordFormatter()
    payload = formatter.server_status(status).to_dict()
    assert payload["embeds"][0]["title"] == "Main"
    assert safe_text("@everyone hi") == "@\u200beveryone hi"
    assert chunks("abc", limit=2) == ["ab", "c"]
    assert DiscordEmbed(title="T").add_field("A", "B").to_dict()["fields"][0]["value"] == "B"


@pytest.mark.asyncio
async def test_cache_sync_async_ttl_and_non_cached_commands() -> None:
    now = 100.0
    cache = MemoryCache(now=lambda: now)
    cache.set("x", 1, ttl_s=5)
    assert cache.get("x") == 1
    now = 106.0
    assert cache.get("x") is None
    assert cache.stats().evictions == 1

    sync_api = _SyncAPI()
    cached = CachedClient(sync_api, ttl_s=5)
    assert len(cached.players()) == 2
    assert len(cached.players()) == 2
    assert [call[0] for call in sync_api.calls].count("players") == 1
    cached.command("h hi")
    cached.command("h hi")
    assert sync_api.commands == 2

    async_api = _AsyncAPI()
    async_cached = AsyncCachedClient(async_api, ttl_s=5)
    assert len(await async_cached.players()) == 2
    assert len(await async_cached.players()) == 2
    assert [call[0] for call in async_api.calls].count("players") == 1
    await async_cached.command("h hi")
    await async_cached.command("h hi")
    assert async_api.commands == 2
    assert {"bundle", "logs"} <= READ_METHODS


def test_command_flows_preview_templates_and_missing_values() -> None:
    template = CommandTemplate("warn", "warn {target} {reason}", description="Warn a player")
    flow = (
        CommandFlowBuilder("moderation")
        .template(template, target="Avi", reason="Rules")
        .step("pm Avi Please read the rules", name="pm")
        .build()
    )

    assert flow.preview() == [":warn Avi Rules", ":pm Avi Please read the rules"]
    assert flow.to_dict()["steps"][0]["name"] == "warn"
    assert str(flow.to_commands()[0]) == ":warn Avi Rules"
    with pytest.raises(KeyError, match="reason"):
        template.bind(target="Avi")
