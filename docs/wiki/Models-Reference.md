# Models Reference

This page describes every typed dataclass that endpoint methods return. Each
model carries a `.raw` attribute with the original PRC dict, an `.extra` dict
of fields PRC sent that the wrapper did not recognize, and a `.to_dict()` helper
for serialization. Use this page when you need to know a field name, its type,
or how PRC JSON keys map to Python attributes.

Endpoint methods return frozen dataclasses by default. Use `raw=True` on an
endpoint method when you need exact PRC JSON.

All typed models inherit from `Model`.

## Model Base

Signature:

```python
Model(raw: Mapping[str, Any] = {}, extra: Mapping[str, Any] = {})
```

Purpose: preserve source payloads and unknown fields.

Public members:

| Member | Return type | Purpose |
| --- | --- | --- |
| `.raw` | `Mapping[str, Any]` | Original API object used to build the model. |
| `.extra` | `Mapping[str, Any]` | Unknown API fields not consumed by known model fields. |
| `.to_dict()` | `dict[str, Any]` | Dataclass-friendly dictionary, including nested models. |

Minimal example:

```python
player = (await api.players())[0]
print(player.raw)
print(player.extra)
print(player.to_dict())
```

Common mistake: treating `.extra` as an error. It is normal and means PRC sent
fields the wrapper preserved without blocking decode.

## Player Identifier Parsing

Signature:

```python
parse_player_identifier(value: Any) -> tuple[str | None, int | None]
```

Purpose: parse PRC `PlayerName:Id` strings.

Example:

```python
from erlc_api import parse_player_identifier

name, user_id = parse_player_identifier("Avi:123")
```

Common mistake: expecting malformed strings to raise. They return best-effort
`(name, None)` values.

## Server Models

### `ServerInfo`

Fields:

| Field | Type |
| --- | --- |
| `name` | `str | None` |
| `owner_id` | `int | None` |
| `co_owner_ids` | `list[int]` |
| `current_players` | `int | None` |
| `max_players` | `int | None` |
| `join_key` | `str | None` |
| `acc_verified_req` | `str | None` |
| `team_balance` | `bool | None` |

Returned by: `server()` when no include sections are requested, and as the base
class for `ServerBundle`.

Minimal example:

```python
info = await api.server()
print(info.name, info.current_players, info.max_players)
```

### `ServerBundle`

Extends `ServerInfo`.

Fields:

| Field | Type |
| --- | --- |
| `players` | `list[Player] | None` |
| `staff` | `StaffList | None` |
| `join_logs` | `list[JoinLogEntry] | None` |
| `queue` | `list[int] | None` |
| `kill_logs` | `list[KillLogEntry] | None` |
| `command_logs` | `list[CommandLogEntry] | None` |
| `mod_calls` | `list[ModCallEntry] | None` |
| `emergency_calls` | `list[EmergencyCall] | None` |
| `vehicles` | `list[Vehicle] | None` |

Helpers:

| Helper | Return type | Purpose |
| --- | --- | --- |
| `.server_name` | `str | None` | Alias for `.name`. |
| `.helpers` | `list[StaffMember] | None` | Helper staff entries if staff data was included. |
| `.players_list` | `list[Player]` | Empty list when players were not included. |
| `.queue_list` | `list[int]` | Empty list when queue was not included. |
| `.vehicles_list` | `list[Vehicle]` | Empty list when vehicles were not included. |
| `.join_logs_list` | `list[JoinLogEntry]` | Empty list when join logs were not included. |
| `.kill_logs_list` | `list[KillLogEntry]` | Empty list when kill logs were not included. |
| `.command_logs_list` | `list[CommandLogEntry]` | Empty list when command logs were not included. |
| `.mod_calls_list` | `list[ModCallEntry]` | Empty list when mod calls were not included. |
| `.emergency_calls_list` | `list[EmergencyCall]` | Empty list when emergency calls were not included. |
| `.staff_members` | `list[StaffMember]` | Empty list when staff was not included. |
| `.included_sections` | `frozenset[str]` | Section names present in the bundle. |
| `.has_section(name)` | `bool` | Check whether a section was included. |

Minimal example:

```python
bundle = await api.bundle()
print(len(bundle.players_list), len(bundle.queue_list))
```

Common mistake: using optional fields without checking `None`. Prefer the safe
list helpers for display and counting.

## Player Models

### `PlayerLocation`

Fields:

| Field | Type |
| --- | --- |
| `location_x` | `float | None` |
| `location_z` | `float | None` |
| `postal_code` | `str | None` |
| `street_name` | `str | None` |
| `building_number` | `str | None` |

Returned inside `Player.location` when PRC includes location data.

### `Player`

Fields:

| Field | Type |
| --- | --- |
| `player` | `str | None` |
| `name` | `str | None` |
| `user_id` | `int | None` |
| `permission` | `str | None` |
| `permission_level` | `PermissionLevel` property |
| `callsign` | `str | None` |
| `team` | `str | None` |
| `location` | `PlayerLocation | None` |
| `wanted_stars` | `int | None` |

Helper:

| Helper | Return type | Purpose |
| --- | --- | --- |
| `.location_typed()` | `PlayerLocation | None` | Alias for `.location`. |

Minimal example:

```python
players = await api.players()
for player in players:
    print(player.name, player.user_id, player.team)
```

Common mistake: assuming `player.name` is always present. The parser is
best-effort and keeps original data in `player.raw`.

`permission` remains the raw PRC string. Use `permission_level` for ordered
comparisons. See [Permission Levels](./Permission-Levels.md).

## Staff Models

### `StaffMember`

Fields:

| Field | Type |
| --- | --- |
| `user_id` | `int | None` |
| `name` | `str | None` |
| `role` | `str | None` |

Helpers:

| Helper | Return type | Purpose |
| --- | --- | --- |
| `.permission()` | `str | None` | Alias for `.role`. |
| `.callsign()` | `str | None` | Always `None`; provided for player/staff compatibility. |

### `StaffList`

Fields:

| Field | Type |
| --- | --- |
| `co_owners` | `list[int]` |
| `admins` | `dict[int, str]` |
| `mods` | `dict[int, str]` |
| `helpers` | `dict[int, str]` |

Helpers:

| Helper | Return type | Purpose |
| --- | --- | --- |
| `.members` | `list[StaffMember]` | Flatten co-owner/admin/mod/helper maps into one list. |
| `.co_owner_members` | `list[StaffMember]` | Co-owner staff entries. |
| `.admin_members` | `list[StaffMember]` | Admin staff entries. |
| `.mod_members` | `list[StaffMember]` | Moderator staff entries. |
| `.helper_members` | `list[StaffMember]` | Helper staff entries. |

Minimal example:

```python
staff = await api.staff()
admins = staff.admin_members
for member in staff:
    print(member.name, member.role)
```

## Log Models

### `JoinLogEntry`

Fields: `join`, `timestamp`, `player`, `name`, `user_id`.

Helper: `.timestamp_datetime() -> datetime | None`.

### `ServerLogs`

Fields:

| Field | Type |
| --- | --- |
| `join_logs` | `list[JoinLogEntry]` |
| `kill_logs` | `list[KillLogEntry]` |
| `command_logs` | `list[CommandLogEntry]` |
| `mod_calls` | `list[ModCallEntry]` |

Returned by `api.logs("all")`.

### `KillLogEntry`

Fields: `killed`, `killed_name`, `killed_id`, `killer`, `killer_name`,
`killer_id`, `timestamp`.

Helpers:

| Helper | Return type | Purpose |
| --- | --- | --- |
| `.victim()` | `str | None` | Best available victim label. |
| `.weapon()` | `str | None` | Weapon value from extra/raw fields when available. |
| `.timestamp_datetime()` | `datetime | None` | UTC datetime from timestamp. |

### `CommandLogEntry`

Fields: `player`, `name`, `user_id`, `timestamp`, `command`.

Helper: `.timestamp_datetime() -> datetime | None`.

### `ModCallEntry`

Fields: `caller`, `caller_name`, `caller_id`, `moderator`,
`moderator_name`, `moderator_id`, `timestamp`.

Helpers:

| Helper | Return type | Purpose |
| --- | --- | --- |
| `.player()` | `str | None` | Best available caller label. |
| `.reason()` | `str | None` | Reason from extra/raw fields when available. |
| `.location()` | `str | None` | Location from extra/raw fields when available. |
| `.timestamp_datetime()` | `datetime | None` | UTC datetime from timestamp. |

Minimal example:

```python
logs = await api.command_logs()
print(logs[0].command if logs else "no commands")
```

## Ban Models

### `BanEntry`

Fields:

| Field | Type |
| --- | --- |
| `player_id` | `str` |
| `player` | `str | None` |

### `BanList`

Fields:

| Field | Type |
| --- | --- |
| `bans` | `dict[str, str | None]` |

Helper:

| Helper | Return type | Purpose |
| --- | --- | --- |
| `.entries()` | `list[BanEntry]` | Convert the ban mapping into entries. |

## Vehicle Models

### `Vehicle`

Fields:

| Field | Type |
| --- | --- |
| `name` | `str | None` |
| `owner` | `str | None` |
| `texture` | `str | None` |
| `plate` | `str | None` |
| `color_hex` | `str | None` |
| `color_name` | `str | None` |
| `model_name` | `str | None` property |
| `year` | `int | None` property |
| `owner_name` | `str | None` property |
| `owner_id` | `int | None` property |
| `normalized_plate` | `str | None` property |

Helpers:

| Helper | Return type | Purpose |
| --- | --- | --- |
| `.model()` | `str | None` | Alias for `.name`. |
| `.color()` | `str | None` | `color_name` or `color_hex`. |
| `.team()` | `str | None` | Team value from extra/raw fields when available. |

Vehicle catalog helpers are documented in [Vehicle Tools](./Vehicle-Tools.md).

### `VehicleColor`

Fields: `color_hex`, `color_name`.

## Emergency Call Model

### `EmergencyCall`

Fields:

| Field | Type |
| --- | --- |
| `team` | `str | None` |
| `caller` | `int | str | None` |
| `players` | `list[int]` |
| `position` | `list[float]` |
| `started_at` | `int | None` |
| `call_number` | `int | None` |
| `description` | `str | None` |
| `position_descriptor` | `str | None` |

Helper:

| Helper | Return type | Purpose |
| --- | --- | --- |
| `.started_at_datetime()` | `datetime | None` | UTC datetime from `started_at`. |

## Command Result

### `CommandResult`

Fields:

| Field | Type |
| --- | --- |
| `message` | `str | None` |
| `success` | `bool | None` |
| `command_id` | `str | None` |

Returned by `command()`.

Minimal example:

```python
from erlc_api import CommandPolicy

policy = CommandPolicy(allowed={"h"}, max_length=120)
result = await api.command(policy.validate("h hello"), dry_run=True)
if result.success is False:
    print(result.message)
```

Common mistake: treating `success=None` as failure. Some PRC responses may only
include a message, so `None` means unknown.

### `CommandPreview`

Fields:

| Field | Type |
| --- | --- |
| `command` | `str` |
| `name` | `str` |
| `allowed` | `bool` |
| `code` | `str | None` |
| `reason` | `str | None` |
| `metadata` | `CommandMetadata | None` |

Returned by `preview_command(...)`. It is local only and never represents a PRC
response.

## Related Pages

- [Earlier in the guide: Endpoint Reference](./Endpoint-Reference.md)
- [Next in the guide: Typed vs Raw Responses](./Typed-vs-Raw-Responses.md)

---

[Previous Page: Endpoint Reference](./Endpoint-Reference.md) | [Next Page: Typed vs Raw Responses](./Typed-vs-Raw-Responses.md)
