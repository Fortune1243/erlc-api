from __future__ import annotations

import builtins

import pytest

from erlc_api import CommandLogEntry, CommandResult, Player, ServerBundle, StaffList, Vehicle
from erlc_api.analytics import Analyzer
from erlc_api.diff import Differ
from erlc_api.export import Exporter
from erlc_api.filter import Filter
from erlc_api.find import Finder
from erlc_api.format import Formatter
from erlc_api.group import Grouper
from erlc_api.moderation import AsyncModerator, Moderator
from erlc_api.schema import SchemaInspector
from erlc_api.sort import Sorter
from erlc_api.time import TimeTools
from erlc_api.wait import AsyncWaiter, Waiter
from erlc_api.watch import AsyncWatcher, Watcher


def _bundle(*, extra_player: bool = False) -> ServerBundle:
    players = [
        Player(name="Avi", player="Avi:1", user_id=1, team="Police", permission="Admin", wanted_stars=2),
    ]
    if extra_player:
        players.append(Player(name="Bee", player="Bee:2", user_id=2, team="Sheriff", permission="Normal"))
    return ServerBundle(
        name="Server",
        current_players=len(players),
        max_players=40,
        players=players,
        queue=[1, 2] if extra_player else [1],
        staff=StaffList(admins={1: "Avi"}, helpers={2: "Bee"} if extra_player else {}),
        vehicles=[Vehicle(name="Falcon", owner="Avi:1", plate="ABC123")],
        command_logs=[CommandLogEntry(name="Avi", player="Avi:1", user_id=1, command=":h hi", timestamp=10)],
    )


def test_find_filter_sort_group_tool_objects() -> None:
    bundle = _bundle(extra_player=True)

    assert Finder(bundle).player("bee").user_id == 2  # type: ignore[union-attr]
    assert Finder(bundle).staff_member(1).role == "Admin"  # type: ignore[union-attr]
    assert Finder(bundle).vehicle(plate="ABC123").name == "Falcon"  # type: ignore[union-attr]
    assert Filter(bundle.players).team("sheriff").first().name == "Bee"  # type: ignore[union-attr]
    assert Sorter(bundle.players).wanted_stars().first().name == "Avi"  # type: ignore[union-attr]
    assert list(Grouper(bundle.players).team()) == ["Police", "Sheriff"]


def test_differ_analyzer_formatter_exporter_schema_and_time() -> None:
    previous = _bundle()
    current = _bundle(extra_player=True)

    diff = Differ(previous, current).bundle()
    assert diff.players.added[0].name == "Bee"

    summary = Analyzer(current).dashboard()
    assert summary.player_count == 2
    assert summary.players_by_team["Sheriff"] == 1
    assert Analyzer(current).command_usage() == {"h": 1}

    formatter = Formatter()
    assert "Server" in formatter.server(current)
    assert "Avi" in formatter.players(current.players)
    assert "ok" in formatter.command_result(CommandResult(message="Success", success=True))

    assert '"name": "Server"' in Exporter(current).json()
    exported_csv = Exporter([current]).csv()
    assert exported_csv.startswith("name,")
    assert "current_players" in exported_csv
    assert "| name |" in Exporter([current]).markdown()
    assert "<table>" in Exporter([current]).html()

    inspector = SchemaInspector(current)
    assert "players" in inspector.fields()
    assert inspector.missing("players", "missing") == ["missing"]

    time_tools = TimeTools()
    assert time_tools.parse(100) == 100
    assert time_tools.last(minutes=5, now=1000).contains(900)


class _AsyncAPI:
    def __init__(self) -> None:
        self.player_calls = 0
        self.server_calls = 0
        self.commands: list[object] = []

    async def players(self, *, server_key=None):  # noqa: ARG002
        self.player_calls += 1
        if self.player_calls == 1:
            return [Player(name="Avi", user_id=1)]
        return [Player(name="Avi", user_id=1), Player(name="Bee", user_id=2)]

    async def queue(self, *, server_key=None):  # noqa: ARG002
        return [1]

    async def staff(self, *, server_key=None):  # noqa: ARG002
        return StaffList(admins={1: "Avi"})

    async def command_logs(self, *, server_key=None):  # noqa: ARG002
        return [CommandLogEntry(name="Avi", command=":h hi", timestamp=1)]

    async def server(self, *, server_key=None, all=False):  # noqa: A002, ARG002
        self.server_calls += 1
        return _bundle(extra_player=self.server_calls > 1)

    async def command(self, command, *, server_key=None, dry_run=False):  # noqa: ARG002
        self.commands.append(command)
        return CommandResult(message="Success", success=True)


class _SyncAPI:
    def __init__(self) -> None:
        self.player_calls = 0
        self.server_calls = 0
        self.commands: list[object] = []

    def players(self, *, server_key=None):  # noqa: ARG002
        self.player_calls += 1
        if self.player_calls == 1:
            return [Player(name="Avi", user_id=1)]
        return [Player(name="Avi", user_id=1), Player(name="Bee", user_id=2)]

    def queue(self, *, server_key=None):  # noqa: ARG002
        return [1]

    def staff(self, *, server_key=None):  # noqa: ARG002
        return StaffList(admins={1: "Avi"})

    def command_logs(self, *, server_key=None):  # noqa: ARG002
        return [CommandLogEntry(name="Avi", command=":h hi", timestamp=1)]

    def server(self, *, server_key=None, all=False):  # noqa: A002, ARG002
        self.server_calls += 1
        return _bundle(extra_player=self.server_calls > 1)

    def command(self, command, *, server_key=None, dry_run=False):  # noqa: ARG002
        self.commands.append(command)
        return CommandResult(message="Success", success=True)


@pytest.mark.asyncio
async def test_async_waiter_watcher_and_moderator() -> None:
    api = _AsyncAPI()
    joined = await AsyncWaiter(api, interval_s=0.001).player_join("Bee", timeout_s=1, interval_s=0.001)
    assert joined.name == "Bee"

    event_types = []
    async for event in AsyncWatcher(api, interval_s=0).events(limit=3):
        event_types.append(event.type)
    assert "player_join" in event_types

    result = await AsyncModerator(api).warn("Bee", "rules")
    assert result.success is True
    assert str(api.commands[-1]) == ":warn Bee rules"


def test_sync_waiter_watcher_and_moderator() -> None:
    api = _SyncAPI()
    joined = Waiter(api, interval_s=0.001).player_join("Bee", timeout_s=1, interval_s=0.001)
    assert joined.name == "Bee"

    event_types = [event.type for event in Watcher(api, interval_s=0).events(limit=3)]
    assert "player_join" in event_types

    result = Moderator(api).kick("Bee", "rules")
    assert result.success is True
    assert str(api.commands[-1]) == ":kick Bee rules"


def test_optional_dependency_errors_are_helpful(monkeypatch, tmp_path) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("openpyxl") or name.startswith("rich"):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match="erlc-api\\.py\\[export\\]"):
        Exporter([]).xlsx(tmp_path / "out.xlsx")
    with pytest.raises(RuntimeError, match="erlc-api\\.py\\[rich\\]"):
        Formatter().rich_table([])
