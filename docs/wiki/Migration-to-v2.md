# Migration to v2

Version 2 is a breaking lightweight release. The public API is smaller, flatter,
and v2-first.

## Why v2 Is Breaking

The old package surface had multiple nested clients, optional ops systems, and
rigid command helpers. v2 focuses on:

- `AsyncERLC` and `ERLC`.
- Flat endpoint methods.
- Typed dataclasses by default.
- `raw=True` for exact JSON.
- Explicit utility modules.
- Minimal HTTP retry behavior.

## Install

```bash
pip install --upgrade erlc-api.py
```

Optional features are extras:

```bash
pip install "erlc-api.py[webhooks,utils]"
```

## Import Changes

| v1-style code | v2 code |
| --- | --- |
| nested client groups | `from erlc_api import AsyncERLC, ERLC` |
| top-level utility imports | `from erlc_api.find import Finder` |
| webhook helpers from top-level | `from erlc_api.webhooks import EventWebhookRouter` |
| custom command builder classes | `from erlc_api import cmd` |

v2 top-level exports are intentionally limited to clients, models, errors,
`cmd`, and command normalization helpers.

## Client Changes

Async:

```python
from erlc_api import AsyncERLC

async with AsyncERLC("server-key") as api:
    players = await api.players()
```

Sync:

```python
from erlc_api import ERLC

with ERLC("server-key") as api:
    players = api.players()
```

Multi-server:

```python
api = AsyncERLC("main-key")
main = await api.players()
other = await api.players(server_key="other-key")
```

Global key:

```python
api = AsyncERLC("server-key", global_key="global-api-key")
```

## Endpoint Changes

| Old concept | v2 replacement |
| --- | --- |
| grouped v1/v2 clients | flat methods on `AsyncERLC` and `ERLC` |
| server info | `api.server()` |
| players | `api.players()` |
| staff | `api.staff()` |
| queue | `api.queue()` |
| logs | `api.join_logs()`, `api.kill_logs()`, `api.command_logs()`, `api.mod_calls()` |
| vehicles | `api.vehicles()` |
| emergency calls | `api.emergency_calls()` |
| bans | `api.bans()` |
| command execution | `api.command(...)` |
| unknown/new endpoint | `api.request(method, path, ...)` |

Typed return example:

```python
players = await api.players()
print(players[0].name, players[0].user_id)
```

Raw return example:

```python
payload = await api.players(raw=True)
print(payload[0])
```

## Command Changes

v2 command syntax is flexible:

```python
from erlc_api import cmd

await api.command(":h hi")
await api.command("h hi")
await api.command(cmd.h("hi"))
await api.command(cmd.pm("Player", "hello"))
await api.command(cmd("pm", "Player", "hello"))
```

The wrapper validates only:

- non-empty command
- no newline characters
- command name exists

It does not hard-block `:log`.

## Utility Changes

Utilities are explicit modules:

```python
from erlc_api.find import Finder
from erlc_api.filter import Filter
from erlc_api.wait import AsyncWaiter
from erlc_api.export import Exporter
```

Examples:

```python
bundle = await api.server(all=True)
player = Finder(bundle).player("Avi")
police = Filter(bundle.players or []).team("Police").all()
csv_text = Exporter(police).csv()
```

Common mistake: importing utilities from `erlc_api` top-level. That is not part
of the v2 public API.

## Removed Public Features

These were removed from the public v2 surface to keep the package lightweight:

- nested `v1` and `v2` client objects
- public context/config objects
- pydantic validation
- Redis/cache layers
- metrics sinks
- request replay
- tracing
- structlog integration
- circuit breaker
- request coalescing
- retry policy machinery

If an application needs those systems, compose them outside the wrapper.

## Compatibility Notes

Some legacy grouped helpers remain under names like `erlc_api.utils`,
`erlc_api.web`, and `erlc_api.discord`, but the v2 primary API is the flat
client plus explicit utility modules.

`bans()` still uses `GET /v1/server/bans` because PRC has not replaced that
endpoint in v2.

`CircuitOpenError` is retained internally only to make old imports fail less
abruptly; the circuit breaker behavior is gone.

## Migration Checklist

1. Replace nested/grouped clients with `AsyncERLC` or `ERLC`.
2. Replace endpoint calls with flat methods.
3. Add `raw=True` where old code expected dictionaries.
4. Replace command builders with strings or `cmd`.
5. Move utilities to explicit submodule imports.
6. Install only the extras you use.
7. Run your tests against typed model fields.

## Before And After

Before, conceptually:

```python
# old grouped style
old_api = ...
players = await old_api.version_group.server.players()
```

After:

```python
from erlc_api import AsyncERLC

async with AsyncERLC("server-key") as api:
    players = await api.players()
```

Before, raw dictionaries everywhere:

```python
payload = ...
name = payload[0]["Player"]
```

After, typed by default:

```python
players = await api.players()
name = players[0].name
```

Use raw only when you need exact JSON:

```python
payload = await api.players(raw=True)
```

## Related Pages

- [Earlier in the guide: Testing and Mocking](./Testing-and-Mocking.md)
- [Next in the guide: Comparison and Why erlc-api](./Comparison-and-Why-erlc-api.md)

---

[Previous Page: Testing and Mocking](./Testing-and-Mocking.md) | [Next Page: Comparison and Why erlc-api](./Comparison-and-Why-erlc-api.md)
