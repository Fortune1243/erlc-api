from __future__ import annotations

import json

import pytest

from erlc_api import CommandResult, Player, ServerBundle
from erlc_api.audit import AuditEvent, AuditLog
from erlc_api.idempotency import FileDeduper, MemoryDeduper
from erlc_api.limits import PollPlan, poll_plan, safe_interval
from erlc_api.snapshot import SnapshotStore
from erlc_api.watch import WatchEvent


def _bundle(name: str = "Server", *, player_name: str = "Avi") -> ServerBundle:
    return ServerBundle(name=name, players=[Player(name=player_name, user_id=1)])


def test_snapshot_store_save_latest_history_diff_and_prune(tmp_path) -> None:
    store = SnapshotStore(tmp_path / "snapshots.jsonl")

    assert store.latest() is None
    first = store.save(_bundle())
    second = store.save({"name": "Server", "players": [{"name": "Bee"}]})

    assert store.latest() == second
    assert [item.saved_at for item in store.history()] == [first.saved_at, second.saved_at]
    assert store.history(limit=1) == [second]
    assert store.diff_latest({"name": "Server", "players": [{"name": "Bee"}]}).changed is False
    assert store.diff_latest(_bundle(player_name="Cat")).changed is True

    assert store.prune(max_entries=1) == 1
    assert store.history() == [second]


def test_audit_event_and_log_helpers(tmp_path) -> None:
    result = CommandResult(message="Success", success=True)
    event = AuditEvent.command_result(result, command=":warn Avi RDM", actor="Console", target="Avi")

    assert event.type == "command_result"
    assert event.success is True
    assert event.to_dict()["data"]["command"] == ":warn Avi RDM"
    assert "@\u200beveryone" in AuditEvent.moderation_action("pm", "@everyone").to_discord()

    memory_log = AuditLog()
    memory_log.record(event)
    memory_log.moderation_action("warn", "Avi", actor="Console", reason="RDM", success=True)
    assert len(memory_log.events()) == 2
    assert memory_log.events(limit=1)[0].action == "warn"

    file_log = AuditLog(tmp_path / "audit.jsonl")
    file_log.command_result(result, command=":h hi")
    file_log.watcher_event(WatchEvent("player_join", item=Player(name="Avi", user_id=1)))
    assert [item.type for item in file_log.events()] == ["command_result", "watcher_event"]


def test_audit_webhook_event_helper() -> None:
    raw = {
        "type": "CustomCommand",
        "command": {
            "command_text": "ping",
        },
    }
    event = AuditEvent.webhook_event(raw)
    assert event.type == "webhook_event"
    assert "CustomCommand" in event.message
    assert event.action == "ping"


def test_memory_deduper_ttl_behavior() -> None:
    now = 1000.0

    def clock() -> float:
        return now

    deduper = MemoryDeduper(ttl_s=10, now=clock)

    assert deduper.check_and_mark("event-1") is False
    assert deduper.seen("event-1") is True
    assert deduper.check_and_mark("event-1") is True

    now = 1011.0
    assert deduper.prune() == 1
    assert deduper.seen("event-1") is False

    with pytest.raises(ValueError, match="blank"):
        deduper.mark(" ")


def test_file_deduper_persists_and_prunes(tmp_path) -> None:
    now = 1000.0

    def clock() -> float:
        return now

    path = tmp_path / "dedupe.json"
    first = FileDeduper(path, ttl_s=5, now=clock)
    assert first.check_and_mark("webhook-1") is False
    assert json.loads(path.read_text(encoding="utf-8"))["webhook-1"] == 1005.0

    second = FileDeduper(path, ttl_s=5, now=clock)
    assert second.check_and_mark("webhook-1") is True

    now = 1006.0
    assert second.prune() == 1
    assert second.seen("webhook-1") is False


def test_poll_limits_are_conservative_and_validate_inputs() -> None:
    assert safe_interval(server_count=2, endpoint_count=3, base_interval_s=2) == 12

    plan = poll_plan(server_count=2, endpoint_count=2, timeout_s=30, base_interval_s=2)
    assert plan == PollPlan(interval_s=8, timeout_s=30, server_count=2, endpoint_count=2)
    assert plan.polls == 4
    assert plan.estimated_requests == 16
    assert plan.to_dict()["estimated_requests"] == 16
    assert "estimated requests" in plan.describe()

    with pytest.raises(ValueError, match="server_count"):
        safe_interval(server_count=0)
    with pytest.raises(ValueError, match="timeout_s"):
        PollPlan(interval_s=1, timeout_s=0)
