# Utilities Reference

Utilities live in explicit modules. They are not imported by top-level
`import erlc_api`.

Use explicit imports:

```python
from erlc_api.find import Finder
from erlc_api.filter import Filter
```

Do not import utility classes from the package root; import their modules directly.

## Utility Loading

Pure utilities accept models, raw dictionaries, lists, `ServerBundle`, or simple
collections where possible. Client-calling utilities are split into sync and
async classes.

Optional dependencies are imported only when a method needs them:

| Extra | Method |
| --- | --- |
| `erlc-api.py[rich]` | `Formatter().rich_table(...)` |
| `erlc-api.py[export]` | `Exporter(...).xlsx(...)` |
| `erlc-api.py[time]` | `TimeTools().parse(..., enhanced=True)` |
| `erlc-api.py[location]` | `MapRenderer().render_points(...)` |

## Utility Categories

Utilities fall into three groups:

**Workflow utilities** (2.3+) are dashboard and bot helpers — location tools,
vehicle analysis, emergency calls, rules engine, multi-server aggregation,
Discord payload builders, caching, status snapshots, and command flows. Use
these when building bots, web dashboards, or multi-server operators.

**Ops utilities** (2.1+) are operational and persistence helpers — JSONL
snapshots, audit logging, idempotency dedupe, polling guidance, and custom
command routing. Use these for audit trails, restart-safe deduplication, and
conservative polling intervals.

**Core data utilities** (Finder, Filter, Sorter, Grouper, Differ, TimeTools,
SchemaInspector) work on in-memory model collections and have no extras beyond
the base install. They are described in this page below the workflow and ops
sections.

## Workflow Utilities

`erlc-api.py` 2.3 and 2.4 add workflow helpers for dashboards, bots, and multi-server
apps. They are still explicit modules and do not load from top-level
`import erlc_api`.

| Module | Import | Purpose |
| --- | --- | --- |
| Location | `from erlc_api.location import LocationTools` | Distances, radius queries, nearest players, postal/street matching, official map URLs, optional map overlays. |
| Bundle | `from erlc_api.bundle import AsyncBundle, Bundle` | Named and custom v2 `/server` include presets. |
| Rules | `from erlc_api.rules import RuleEngine, Conditions` | Evaluate alert-style rules and return `RuleMatch` objects. |
| Multi Server | `from erlc_api.multiserver import AsyncMultiServer, MultiServer` | Read multiple named servers with bounded concurrency and per-server errors. |
| Discord Tools | `from erlc_api.discord_tools import DiscordFormatter` | Build plain dict Discord message/embed payloads without a Discord dependency. |
| Diagnostics | `from erlc_api.diagnostics import diagnose_error` | Turn errors, rate limits, command results, and statuses into user-facing diagnostics. |
| Cache | `from erlc_api.cache import AsyncCachedClient, CachedClient` | Explicit memory TTL caching for read endpoints plus adapter protocols. |
| Status | `from erlc_api.status import AsyncStatus, StatusBuilder` | Typed dashboard status snapshots with `.to_dict()`. |
| Command Flows | `from erlc_api.command_flows import CommandFlowBuilder` | Preview and validate command sequences without execution. |
| Vehicle Tools | `from erlc_api.vehicles import VehicleTools` | Catalog-aware vehicle parsing, plate lookup, owner matching, and spawned-vehicle summaries. |
| Emergency Calls | `from erlc_api.emergency import EmergencyCallTools` | Active/unresponded call filters, team summaries, and nearest-call helpers. |

See [Workflow Utilities Reference](./Workflow-Utilities-Reference.md),
[Vehicle Tools](./Vehicle-Tools.md), and [Emergency Calls](./Emergency-Calls.md)
for the full workflow API.

## Ops Utilities

`erlc-api.py` 2.1 adds lightweight operational helpers. They are stdlib-only,
explicit imports, and advisory rather than a heavyweight ops stack.

| Module | Import | Purpose |
| --- | --- | --- |
| Snapshot | `from erlc_api.snapshot import SnapshotStore` | Store typed or raw server snapshots in JSONL. |
| Audit | `from erlc_api.audit import AuditEvent, AuditLog` | Create JSON-safe audit records from commands, webhooks, watchers, and moderation actions. |
| Idempotency | `from erlc_api.idempotency import MemoryDeduper, FileDeduper` | TTL dedupe for webhook deliveries and watcher restarts. |
| Limits | `from erlc_api.limits import poll_plan, safe_interval` | Conservative polling guidance without claiming official PRC limits. |
| Custom Commands | `from erlc_api.custom_commands import CustomCommandRouter` | Route PRC webhook messages starting with `;` using aliases, predicates, middleware, and unknown handlers. |

### SnapshotStore

Signature:

```python
SnapshotStore(path: str | Path)
```

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `save(bundle)` | `Snapshot` | Append a JSON-safe snapshot. |
| `latest()` | `Snapshot | None` | Return the newest snapshot. |
| `history(limit=None)` | `list[Snapshot]` | Return snapshots in file order, optionally latest N. |
| `diff_latest(bundle)` | `SnapshotDiff` | Compare current data with latest saved data. |
| `prune(max_entries=...)` | `int` | Keep latest entries and return removed count. |

Example:

```python
from erlc_api.snapshot import SnapshotStore

store = SnapshotStore("server-snapshots.jsonl")
bundle = await api.server(all=True)

if store.diff_latest(bundle).changed:
    store.save(bundle)
```

Common mistake: expecting typed models back from `latest()`. Snapshots return
JSON-safe stored data; use endpoint methods for fresh typed objects.

### AuditEvent And AuditLog

Signatures:

```python
AuditEvent(...)
AuditLog(path: str | Path | None = None)
```

Helpers:

| Helper | Purpose |
| --- | --- |
| `AuditEvent.command_result(result, command=None, actor=None, target=None)` | Build command-result audit event. |
| `AuditEvent.webhook_event(event)` | Build webhook audit event. |
| `AuditEvent.watcher_event(event)` | Build watcher audit event. |
| `AuditEvent.moderation_action(action, target, ...)` | Build moderation audit event. |
| `AuditLog.record(event)` | Store event in memory or JSONL file. |
| `AuditLog.events(limit=None)` | Read stored events. |

Example:

```python
from erlc_api.audit import AuditLog

audit = AuditLog("audit.jsonl")
result = await api.command("warn Avi RDM")
event = audit.command_result(result, command=":warn Avi RDM", actor="Console", target="Avi")
print(event.to_console())
```

### MemoryDeduper And FileDeduper

Signatures:

```python
MemoryDeduper(ttl_s=300)
FileDeduper(path, ttl_s=300)
```

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `seen(key)` | `bool` | True when key is active. |
| `mark(key)` | `str` | Store key and return normalized key. |
| `check_and_mark(key)` | `bool` | True when already seen, false when newly marked. |
| `prune()` | `int` | Remove expired keys and return removed count. |

Example:

```python
from erlc_api.idempotency import FileDeduper

dedupe = FileDeduper("webhook-dedupe.json", ttl_s=300)
if dedupe.check_and_mark(event_id):
    return {"ignored": True}
```

### PollPlan And safe_interval

Signatures:

```python
safe_interval(server_count=1, endpoint_count=1, base_interval_s=2.0, min_interval_s=2.0) -> float
poll_plan(server_count=1, endpoint_count=1, timeout_s=60.0, base_interval_s=2.0, min_interval_s=2.0) -> PollPlan
```

Purpose: provide conservative polling guidance based on request fanout. This is
not an official PRC rate-limit implementation.

Example:

```python
from erlc_api.limits import poll_plan

plan = poll_plan(server_count=2, endpoint_count=3, timeout_s=120)
watcher = AsyncWatcher(api, interval_s=plan.interval_s)
```

## Finder

Import:

```python
from erlc_api.find import Finder
```

Signature:

```python
Finder(data: Any)
```

Purpose: look up objects inside a bundle, list, mapping, or model collection.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `player(query, *, partial=True)` | `Player | None` | First matching player by name/user ID. |
| `players(query=None, *, partial=True, team=None, permission=None, callsign=None)` | `list[Player]` | Matching players. |
| `staff_member(query, *, role=None)` | `StaffMember | None` | First matching staff member. |
| `staff(query=None, *, role=None)` | `list[StaffMember]` | Matching staff members. |
| `vehicle(query=None, *, plate=None, owner=None)` | `Vehicle | None` | First matching vehicle. |
| `vehicles(query=None, *, plate=None, owner=None)` | `list[Vehicle]` | Matching vehicles. |
| `command_logs(*, player=None, command_prefix=None, command_contains=None, after=None, before=None)` | `list[CommandLogEntry]` | Matching command logs. |
| `command_log(**kwargs)` | `CommandLogEntry | None` | First matching command log. |
| `mod_calls(*, caller=None, moderator=None)` | `list[ModCallEntry]` | Matching mod calls. |
| `emergency_calls(*, team=None, caller=None)` | `list[EmergencyCall]` | Matching emergency calls. |
| `bans(query=None)` | `list[BanEntry]` | Matching ban entries. |

Minimal example:

```python
bundle = await api.server(all=True)
finder = Finder(bundle)

player = finder.player("Avi")
police = finder.players(team="Police")
warns = finder.command_logs(command_prefix=":warn")
```

Important options:

- String matching is case-insensitive where practical.
- Integer player queries match parsed user IDs.
- `after` and `before` are Unix timestamps.

Common mistakes:

- Passing a bundle that did not include the section you want to search.
- Expecting `player("Avi")` to return all matches. Use `.players("Avi")`.

## Filter

Import:

```python
from erlc_api.filter import Filter
```

Signature:

```python
Filter(items: Any)
```

Purpose: chain predicates without mutating the original collection.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `team(value)` | `Filter` | Keep items with matching `team`. |
| `permission(value)` | `Filter` | Keep items with matching `permission` or `role`. |
| `role(value)` | `Filter` | Keep items with matching `role`. |
| `name_contains(value)` | `Filter` | Keep items whose `name` or `player` contains text. |
| `after(timestamp)` | `Filter` | Keep items at or after timestamp. |
| `before(timestamp)` | `Filter` | Keep items at or before timestamp. |
| `command(prefix=None, contains=None, name=None)` | `Filter` | Keep command log entries matching command filters. |
| `vehicle_owner(owner)` | `Filter` | Keep vehicles with matching owner. |
| `where(predicate)` | `Filter` | Add a custom predicate. |
| `all()` | `list[Any]` | Return all matches. |
| `first()` | `Any | None` | Return first match. |
| `count()` | `int` | Count matches. |
| `group_by(field)` | `dict[Any, list[Any]]` | Group filtered matches by field. |

Minimal example:

```python
police = Filter(await api.players()).team("Police").all()
recent_warns = Filter(await api.command_logs()).after(1710000000).command(name="warn").all()
```

Common mistakes:

- Forgetting the terminal method. `Filter(players).team("Police")` is a filter
  object; call `.all()`, `.first()`, or `.count()`.

## Sorter

Import:

```python
from erlc_api.sort import Sorter
```

Signature:

```python
Sorter(items: Any)
```

Purpose: sort model lists and simple collections.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `by(field, *, reverse=False)` | `Sorter` | Sort by any model/dict field. |
| `name(*, reverse=False)` | `Sorter` | Sort by `name` or `player`. |
| `timestamp(*, reverse=False)` | `Sorter` | Sort by timestamp. |
| `newest()` | `Sorter` | Timestamp descending. |
| `oldest()` | `Sorter` | Timestamp ascending. |
| `team(*, reverse=False)` | `Sorter` | Sort by team. |
| `permission(*, reverse=False)` | `Sorter` | Sort by permission or role. |
| `wanted_stars(*, reverse=True)` | `Sorter` | Sort by wanted stars, high first by default. |
| `vehicle_owner(*, reverse=False)` | `Sorter` | Sort by owner. |
| `vehicle_model(*, reverse=False)` | `Sorter` | Sort by vehicle name/model. |
| `queue_position(*, reverse=False)` | `Sorter` | Keep queue/list order or reverse it. |
| `all()` | `list[Any]` | Sorted list. |
| `first()` | `Any | None` | First sorted item. |

Minimal example:

```python
latest = Sorter(await api.command_logs()).newest().first()
by_name = Sorter(await api.players()).name().all()
```

Common mistakes:

- Expecting chained sort keys. Each sorter method creates a new single-key sort.

## Grouper

Import:

```python
from erlc_api.group import Grouper
```

Signature:

```python
Grouper(items: Any)
```

Purpose: group collections by common ER:LC dimensions.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `by(key)` | `dict[Any, list[Any]]` | Group by field name or callable. |
| `team()` | `dict[Any, list[Any]]` | Group by team. |
| `permission()` | `dict[Any, list[Any]]` | Group by permission or role. |
| `staff_role()` | `dict[Any, list[Any]]` | Group staff by role. |
| `vehicle_owner()` | `dict[Any, list[Any]]` | Group vehicles by owner. |
| `command_name()` | `dict[Any, list[Any]]` | Group command logs by command name. |
| `day()` | `dict[str | None, list[Any]]` | Group timestamped items by UTC day. |
| `hour()` | `dict[str | None, list[Any]]` | Group timestamped items by UTC hour. |
| `emergency_team()` | `dict[Any, list[Any]]` | Group emergency calls by team. |

Minimal example:

```python
players_by_team = Grouper(await api.players()).team()
commands_by_name = Grouper(await api.command_logs()).command_name()
```

Common mistakes:

- Grouping logs without timestamps by day/hour. Those entries land under `None`.

## Differ

Import:

```python
from erlc_api.diff import Differ
```

Signatures:

```python
Differ(previous: Any, current: Any)
CollectionDiff(added=list, removed=list, unchanged=list, previous_count=0, current_count=0)
BundleDiff(players, queue, staff, vehicles, command_logs, mod_calls, emergency_calls)
```

Purpose: compare two model collections or two server bundles.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `collection(key=...)` | `CollectionDiff` | Diff arbitrary collections. |
| `players()` | `CollectionDiff` | Diff players by user ID/name. |
| `queue()` | `CollectionDiff` | Diff queue user IDs. |
| `staff()` | `CollectionDiff` | Diff staff members. |
| `vehicles()` | `CollectionDiff` | Diff vehicles. |
| `command_logs()` | `CollectionDiff` | Diff command logs. |
| `mod_calls()` | `CollectionDiff` | Diff mod calls. |
| `emergency_calls()` | `CollectionDiff` | Diff emergency calls. |
| `bundle()` | `BundleDiff` | Diff every supported bundle section. |

Minimal example:

```python
before = await api.server(all=True)
after = await api.server(all=True)

diff = Differ(before, after).bundle()
if diff.players.added:
    print("joined", diff.players.added)
```

Important options:

- `CollectionDiff.changed` is true when anything was added or removed.
- `BundleDiff.changed` is true when any section changed.

Common mistakes:

- Expecting value-level mutation diffs. v2 reports added/removed/unchanged
  collection members, not field-by-field changes.

## TimeTools

Import:

```python
from erlc_api.time import TimeTools
```

Signature:

```python
TimeTools()
```

Purpose: parse, format, and compare timestamps.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `now()` | `int` | Current UTC Unix timestamp. |
| `parse(value, *, enhanced=False)` | `int | None` | Parse int, float, numeric string, or ISO datetime. |
| `format(timestamp, *, tz=timezone.utc)` | `str | None` | Format timestamp as ISO string. |
| `age(timestamp, *, now=None)` | `str` | Compact age like `42s`, `5m`, `2h`, `3d`. |
| `last(seconds=0, minutes=0, hours=0, days=0, now=None)` | `TimeWindow` | Build recent time window. |
| `between(start, end)` | `TimeWindow` | Build window from parseable values. |
| `TimeWindow.contains(timestamp)` | `bool` | Check timestamp is inside window. |

Minimal example:

```python
from erlc_api.time import TimeTools

time = TimeTools()
window = time.last(minutes=5)
recent = [entry for entry in await api.command_logs() if window.contains(entry.timestamp)]
```

Optional extra:

```bash
pip install "erlc-api.py[time]"
```

Required only for:

```python
TimeTools().parse("last Friday 5pm", enhanced=True)
```

Common mistakes:

- Expecting enhanced natural-language parsing without installing `erlc-api.py[time]`.

## SchemaInspector

Import:

```python
from erlc_api.schema import SchemaInspector
```

Signature:

```python
SchemaInspector(value: Any)
```

Purpose: inspect model fields, raw payloads, unknown extras, and missing fields.

Methods:

| Method | Return type | Purpose |
| --- | --- | --- |
| `fields()` | `list[str]` | Dataclass fields, dict keys, or first list item fields. |
| `raw()` | `Any` | `.raw` for models, converted data otherwise. |
| `extra()` | `dict[str, Any]` | `.extra` for models, empty dict otherwise. |
| `missing(*names)` | `list[str]` | Required names absent from `.fields()`. |
| `diagnostics(*required)` | `dict[str, Any]` | Type, fields, missing fields, extra keys, raw presence. |

Minimal example:

```python
from erlc_api.schema import SchemaInspector

player = (await api.players())[0]
print(SchemaInspector(player).diagnostics("name", "user_id", "team"))
```

Common mistakes:

- Using schema diagnostics as validation for PRC permissions. It only inspects payload shape.

## Related Pages

- [Earlier in the guide: Function List](./Function-List.md)
- [Next in the guide: Vehicle Tools](./Vehicle-Tools.md)

---

[Previous Page: Permission Levels](./Permission-Levels.md) | [Next Page: Vehicle Tools](./Vehicle-Tools.md)
