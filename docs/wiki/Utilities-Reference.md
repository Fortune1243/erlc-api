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
| `erlc-api[rich]` | `Formatter().rich_table(...)` |
| `erlc-api[export]` | `Exporter(...).xlsx(...)` |
| `erlc-api[time]` | `TimeTools().parse(..., enhanced=True)` |

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
pip install "erlc-api[time]"
```

Required only for:

```python
TimeTools().parse("last Friday 5pm", enhanced=True)
```

Common mistakes:

- Expecting enhanced natural-language parsing without installing `erlc-api[time]`.

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
