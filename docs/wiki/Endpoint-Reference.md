# Endpoint Reference

All endpoint methods exist on both `AsyncERLC` and `ERLC`. Async examples use
`await`; sync examples remove `await`.

All endpoint methods accept:

- `server_key=` to override the client default key.
- `raw=True` to return raw PRC data instead of typed models. Section helpers
  return their named raw section; `server(raw=True)` returns the full v2 payload.

## Endpoint Version Map

| API area | PRC version | Wrapper methods |
| --- | --- | --- |
| Server status and include sections | v2 | `server`, `players`, `staff`, `queue`, logs, `vehicles`, `emergency_calls` |
| Command execution | v2 | `command` |
| Bans | v1 | `bans` |
| Custom escape hatch | caller chooses | `request` |

## Support Matrix

| Capability | Support | Notes |
| --- | --- | --- |
| Async client | Yes | `AsyncERLC` |
| Sync client | Yes | `ERLC` |
| Typed dataclasses | Yes | Default endpoint mode |
| Raw PRC data | Yes | `raw=True` |
| Default dynamic limiter | Yes | Process-local only |
| Optional global key header | Yes | `global_key=` sends `Authorization` |
| Event webhook verification | Optional extra | `erlc-api.py[webhooks]` |
| Discord library integration | No direct dependency | Use docs/templates and plain payload helpers |
| Distributed rate limiting/cache | Bring your own | Use external stores for multi-process deployments |

## Method Table

| Method | Signature suffix | PRC endpoint | Default return type |
| --- | --- | --- | --- |
| `server` | `(..., include=None, all=False, players=False, staff=False, join_logs=False, queue=False, kill_logs=False, command_logs=False, mod_calls=False, emergency_calls=False, vehicles=False)` | `GET /v2/server` | `ServerBundle` |
| `players` | `(*, server_key=None, raw=False)` | `GET /v2/server?Players=true` | `list[Player]` |
| `staff` | `(*, server_key=None, raw=False)` | `GET /v2/server?Staff=true` | `StaffList` |
| `queue` | `(*, server_key=None, raw=False)` | `GET /v2/server?Queue=true` | `list[int]` |
| `join_logs` | `(*, server_key=None, raw=False)` | `GET /v2/server?JoinLogs=true` | `list[JoinLogEntry]` |
| `kill_logs` | `(*, server_key=None, raw=False)` | `GET /v2/server?KillLogs=true` | `list[KillLogEntry]` |
| `command_logs` | `(*, server_key=None, raw=False)` | `GET /v2/server?CommandLogs=true` | `list[CommandLogEntry]` |
| `mod_calls` | `(*, server_key=None, raw=False)` | `GET /v2/server?ModCalls=true` | `list[ModCallEntry]` |
| `emergency_calls` | `(*, server_key=None, raw=False)` | `GET /v2/server?EmergencyCalls=true` | `list[EmergencyCall]` |
| `vehicles` | `(*, server_key=None, raw=False)` | `GET /v2/server?Vehicles=true` | `list[Vehicle]` |
| `bans` | `(*, server_key=None, raw=False)` | `GET /v1/server/bans` | `BanList` |
| `command` | `(command, *, server_key=None, raw=False, dry_run=False)` | `POST /v2/server/command` | `CommandResult` |
| `request` | `(method, path, *, server_key=None, params=None, json=None, headers=None)` | any | raw decoded payload |

## `server`

Signature:

```python
await api.server(
    *,
    server_key: str | None = None,
    raw: bool = False,
    include: Iterable[str] | str | None = None,
    all: bool = False,
    players: bool = False,
    staff: bool = False,
    join_logs: bool = False,
    queue: bool = False,
    kill_logs: bool = False,
    command_logs: bool = False,
    mod_calls: bool = False,
    emergency_calls: bool = False,
    vehicles: bool = False,
) -> ServerBundle
```

Purpose: fetch v2 server status and any requested v2 sections.

Minimal example:

```python
bundle = await api.server(players=True, queue=True, staff=True)
print(bundle.name, bundle.players, bundle.queue, bundle.staff)
```

Important options:

- `all=True` requests every v2 include section.
- `include="players"` or `include=["players", "vehicles"]` is equivalent to setting the matching booleans.
- Include names accept underscores or hyphens, for example `join_logs` or `join-logs`.
- `include="all"` is equivalent to `all=True`.

Common mistakes:

- Expecting `bundle.players` to be a list when `players=True` was not requested. Optional sections are `None` unless requested.
- Passing unknown include names. The client raises `ValueError` before sending HTTP.

## `players`

Signature:

```python
await api.players(*, server_key: str | None = None, raw: bool = False) -> list[Player]
```

Purpose: fetch and decode v2 players.

Minimal example:

```python
players = await api.players()
for player in players:
    print(player.name, player.user_id, player.team)
```

Common mistakes:

- Looking only at `player.player`; use `player.name` and `player.user_id` for parsed values.
- Assuming all optional PRC fields are present. Check for `None`.

## `staff`

Signature:

```python
await api.staff(*, server_key: str | None = None, raw: bool = False) -> StaffList
```

Purpose: fetch v2 staff maps.

Minimal example:

```python
staff = await api.staff()
for member in staff.members:
    print(member.role, member.name, member.user_id)
```

Common mistakes:

- Treating `StaffList` as a plain list. Use `.members` when you want flattened staff members.

## `queue`

Signature:

```python
await api.queue(*, server_key: str | None = None, raw: bool = False) -> list[int]
```

Purpose: fetch queue user IDs in API order.

Minimal example:

```python
for position, user_id in enumerate(await api.queue(), start=1):
    print(position, user_id)
```

Common mistakes:

- Assuming queue IDs are player names. The API returns user IDs.

## `join_logs`

Signature:

```python
await api.join_logs(*, server_key: str | None = None, raw: bool = False) -> list[JoinLogEntry]
```

Purpose: fetch v2 join/leave logs.

Minimal example:

```python
logs = await api.join_logs()
latest = logs[0] if logs else None
```

Important options: pass `raw=True` if you need exact log keys from PRC.

Common mistakes:

- Treating `join=True` as always present. Unknown or missing values decode as `None`.

## `kill_logs`

Signature:

```python
await api.kill_logs(*, server_key: str | None = None, raw: bool = False) -> list[KillLogEntry]
```

Purpose: fetch v2 kill logs.

Minimal example:

```python
for entry in await api.kill_logs():
    print(entry.killer_name, "killed", entry.killed_name)
```

Common mistakes:

- Assuming `weapon` is a first-class field. Use `entry.weapon()` because PRC may expose it as extra payload data.

## `command_logs`

Signature:

```python
await api.command_logs(*, server_key: str | None = None, raw: bool = False) -> list[CommandLogEntry]
```

Purpose: fetch v2 command logs.

Minimal example:

```python
from erlc_api.filter import Filter

warns = Filter(await api.command_logs()).command(name="warn").all()
```

Common mistakes:

- Manually parsing command names everywhere. Use `Filter(...).command(...)`, `Grouper(...).command_name()`, or `Analyzer(...).command_usage()`.

## `mod_calls`

Signature:

```python
await api.mod_calls(*, server_key: str | None = None, raw: bool = False) -> list[ModCallEntry]
```

Purpose: fetch v2 mod call logs.

Minimal example:

```python
calls = await api.mod_calls()
print(calls[0].caller_name if calls else "none")
```

Common mistakes:

- Assuming every mod call has a moderator. Some calls may be unclaimed or incomplete.

## `emergency_calls`

Signature:

```python
await api.emergency_calls(*, server_key: str | None = None, raw: bool = False) -> list[EmergencyCall]
```

Purpose: fetch active v2 emergency calls.

Minimal example:

```python
for call in await api.emergency_calls():
    print(call.team, call.call_number, call.started_at_datetime())
```

Common mistakes:

- Assuming `caller` is always an integer. The model accepts `int | str | None` because PRC payloads can vary.

## `vehicles`

Signature:

```python
await api.vehicles(*, server_key: str | None = None, raw: bool = False) -> list[Vehicle]
```

Purpose: fetch v2 spawned vehicles.

Minimal example:

```python
from erlc_api.find import Finder
from erlc_api.vehicles import VehicleTools

vehicles = await api.vehicles()
vehicle = Finder(vehicles).vehicle(plate="ABC123")
summary = VehicleTools(vehicles).summary()
```

Common mistakes:

- Treating the API name as already normalized. Use `vehicle.model`,
  `vehicle.year`, `vehicle.normalized_plate`, or
  `from erlc_api.vehicles import VehicleTools` for catalog-aware lookups.

## `bans`

Signature:

```python
await api.bans(*, server_key: str | None = None, raw: bool = False) -> BanList
```

Purpose: fetch server bans from the v1 endpoint that still owns this data.

Minimal example:

```python
bans = await api.bans()
for entry in bans.entries():
    print(entry.player_id, entry.player)
```

Common mistakes:

- Expecting this to use v2. The wrapper stays v2-first, but bans remain v1 because PRC has not replaced that endpoint.

## `command`

Signature:

```python
await api.command(
    command: str | Command,
    *,
    server_key: str | None = None,
    raw: bool = False,
    dry_run: bool = False,
) -> CommandResult
```

Purpose: execute a PRC v2 command.

Minimal example:

```python
from erlc_api import cmd

result = await api.command(cmd.pm("Player", "hello"))
print(result.success, result.message, result.command_id)
```

Important options:

- `dry_run=True` normalizes and validates locally, then returns a local result without sending HTTP.
- `raw=True` returns the exact command response payload.
- `CommandResult.command_id` is populated from `commandId`, `CommandId`, or
  `command_id` when PRC includes a command tracking ID.

Common mistakes:

- Including newline characters in commands. The wrapper rejects them.
- Expecting the wrapper to maintain a hard-coded allowlist. It does not.

## `request`

See [Clients and Authentication](./Clients-and-Authentication.md#low-level-request) for the low-level request signature and behavior.

## Related Pages

- [Earlier in the guide: Clients and Authentication](./Clients-and-Authentication.md)
- [Next in the guide: Endpoint Usage Cookbook](./Endpoint-Usage-Cookbook.md)

---

[Previous Page: Clients and Authentication](./Clients-and-Authentication.md) | [Next Page: Endpoint Usage Cookbook](./Endpoint-Usage-Cookbook.md)
