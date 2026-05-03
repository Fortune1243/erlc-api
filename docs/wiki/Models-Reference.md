# Models Reference

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
| `.server_name()` | `str | None` | Alias for `.name`. |
| `.helpers()` | `list[StaffMember] | None` | Helper staff entries if staff data was included. |

Minimal example:

```python
bundle = await api.server(all=True)
print(len(bundle.players or []), len(bundle.queue or []))
```

Common mistake: not checking optional sections for `None`.

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

Helper:

| Helper | Return type | Purpose |
| --- | --- | --- |
| `.members()` | `list[StaffMember]` | Flatten co-owner/admin/mod/helper maps into one list. |

Minimal example:

```python
staff = await api.staff()
admins = [member for member in staff.members() if member.role == "Admin"]
```

## Log Models

### `JoinLogEntry`

Fields: `join`, `timestamp`, `player`, `name`, `user_id`.

Helper: `.timestamp_datetime() -> datetime | None`.

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

Helpers:

| Helper | Return type | Purpose |
| --- | --- | --- |
| `.model()` | `str | None` | Alias for `.name`. |
| `.color()` | `str | None` | `color_name` or `color_hex`. |
| `.team()` | `str | None` | Team value from extra/raw fields when available. |

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

Returned by `command()`.

Minimal example:

```python
result = await api.command("h hello")
if result.success is False:
    print(result.message)
```

Common mistake: treating `success=None` as failure. Some PRC responses may only
include a message, so `None` means unknown.

## Related Pages

- [Earlier in the guide: Endpoint Usage Cookbook](./Endpoint-Usage-Cookbook.md)
- [Next in the guide: Typed vs Raw Responses](./Typed-vs-Raw-Responses.md)

---

[Previous Page: Endpoint Usage Cookbook](./Endpoint-Usage-Cookbook.md) | [Next Page: Typed vs Raw Responses](./Typed-vs-Raw-Responses.md)
