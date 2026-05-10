# Migration to v3

Version 3 keeps the v2 feature set and makes the common path easier to read:
client aliases, environment constructors, dashboard bundles, log shortcuts,
command previews, and model helpers for common list-shaped data.

## Install

```bash
pip install --upgrade erlc-api.py
```

Python import name is unchanged:

```python
import erlc_api
```

## Client Names

`ERLC` and `AsyncERLC` still work. v3 also documents simpler aliases:

```python
from erlc_api import Client, AsyncClient

api = Client.from_env()
async_api = AsyncClient.from_env()
```

`from_env()` reads `ERLC_SERVER_KEY` and optional `ERLC_GLOBAL_KEY`.

## Server Data

v2 often taught include flags:

```python
bundle = await api.server(players=True, staff=True, queue=True, vehicles=True, emergency_calls=True)
players = bundle.players or []
```

v3 teaches `bundle()`:

```python
bundle = await api.bundle()
players = bundle.players_list
staff = bundle.staff_members
```

Use `api.bundle("all")` when you want every supported v2 section. The old
`server(... include flags ...)` form remains available for exact control.

## Logs

Before:

```python
commands = await api.command_logs()
mods = await api.mod_calls()
```

After:

```python
commands = await api.logs("command")
all_logs = await api.logs("all")
```

`logs("all")` returns `ServerLogs` with `join_logs`, `kill_logs`,
`command_logs`, and `mod_calls`.

## Commands

Before:

```python
safe = policy.validate(cmd.h("Hello"))
await api.command(safe)
```

After:

```python
preview = await api.preview_command(cmd.h("Hello"), policy=policy)
if preview.allowed:
    await api.command(preview.command, policy=policy)
```

`preview_command(...)` never sends HTTP. `command(..., policy=policy)` validates
before sending.

## Models

`StaffList` is now list-like over `.members`:

```python
staff = await api.staff()
for member in staff:
    print(member.name, member.permission_level)
```

`ServerBundle` keeps optional sections as `None` when not requested, but v3 adds
safe helpers:

```python
bundle.players_list
bundle.queue_list
bundle.staff_members
bundle.included_sections
bundle.has_section("players")
```

## Checklist

1. Optionally replace `ERLC` with `Client` and `AsyncERLC` with `AsyncClient`.
2. Use `from_env()` in examples, bots, and scripts that read environment keys.
3. Prefer `bundle()` over long `server(... flags ...)` calls for dashboards.
4. Prefer `logs("command")` and `logs("all")` for log workflows.
5. Use `preview_command(...)` and `command(..., policy=...)` for user-triggered commands.
6. Replace `bundle.players or []` with `bundle.players_list` where that reads better.

## Related Pages

- [Earlier in the guide: Endpoint Usage Cookbook](./Endpoint-Usage-Cookbook.md)
- [Next in the guide: Migration to v2](./Migration-to-v2.md)

---

[Previous Page: Endpoint Usage Cookbook](./Endpoint-Usage-Cookbook.md) | [Next Page: Migration to v2](./Migration-to-v2.md)
