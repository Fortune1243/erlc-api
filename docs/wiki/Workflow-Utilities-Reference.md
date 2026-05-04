# Workflow Utilities Reference

`erlc-api.py` 2.3 adds workflow helpers for dashboards, Discord bots, and
multi-server tools. These modules are still lazy: import them explicitly only
when needed.

## Location

Import:

```python
from erlc_api.location import LocationTools, MapRenderer
```

Use `LocationTools(data)` with players, emergency calls, raw dictionaries, or a
`ServerBundle`.

```python
bundle = await api.server(players=True, emergency_calls=True)
tools = LocationTools(bundle)

nearest = tools.nearest_players_to_call(bundle.emergency_calls[0], limit=3)
near_postal = tools.by_postal("218")
map_url = tools.official_map_url(season="fall", layer="postals")
```

Core methods:

| Method | Purpose |
| --- | --- |
| `point(value, z=None)` | Convert a model, mapping, position list, or x/z pair into `Coordinate`. |
| `distance(a, b)` | Euclidean distance between two coordinates. |
| `nearest(origin, items=None, limit=1, max_distance=None)` | Sorted `LocationMatch` results. |
| `within_radius(origin, radius, items=None)` | All location-capable items inside a radius. |
| `by_postal(postal_code)` / `by_street(street_name)` | Match v2 player location labels. |
| `official_map_url(season="fall", layer="postals")` | PRC official map image URL. |

Map overlays require Pillow:

```bash
pip install "erlc-api.py[location]"
```

`MapRenderer().render_points(...)` requires either `bounds=` or `transform=`
because the official API gives game X/Z coordinates, not a universal pixel
calibration.

## Bundle Presets

Import:

```python
from erlc_api.bundle import AsyncBundle, Bundle, BundleRequest, register_preset
```

Built-in presets:

| Preset | Includes |
| --- | --- |
| `minimal` | Server info only. |
| `players` | Players and queue. |
| `dashboard` | Players, staff, queue, vehicles, emergency calls. |
| `logs` | Join, kill, command, and mod logs. |
| `ops` | Operational bot state. |
| `all` | Every v2 include. |

Examples:

```python
bundle = await AsyncBundle(api).dashboard()
ops = BundleRequest.preset("dashboard").include("command_logs")
bundle = await AsyncBundle(api).fetch(ops)

register_preset("dispatch", ["players", "emergency_calls", "vehicles"])
dispatch = await AsyncBundle(api).fetch("dispatch")
```

## Rules

Import:

```python
from erlc_api.rules import RuleEngine, AsyncRuleEngine, Conditions
```

Rules evaluate data and return `RuleMatch` objects. They do not run PRC
commands.

```python
engine = RuleEngine()
engine.add(
    "queue-active",
    Conditions.queue_length(at_least=1),
    severity="info",
    message="Queue is active",
)

matches = engine.evaluate(bundle)
```

Condition helpers cover player count, queue length, staff count, vehicle count,
command names/prefixes, emergency-call age, and status severities.

## Multi Server

Import:

```python
from erlc_api.multiserver import AsyncMultiServer, MultiServer, ServerRef
```

Use named server refs so every result remains identifiable.

```python
servers = [
    ServerRef("main", "main-server-key"),
    ServerRef("training", "training-server-key"),
]

manager = AsyncMultiServer(api, servers, concurrency=3)
results = await manager.status()
summary = await manager.aggregate()
```

Failures are collected per server by default. `call(...)` only allows read-only
client methods; command broadcasting must stay explicit in user code.

## Discord Tools

Import:

```python
from erlc_api.discord_tools import DiscordFormatter, DiscordEmbed, DiscordMessage
```

These helpers return plain dictionaries compatible with most Discord libraries.
They do not import `discord.py`.

```python
from erlc_api.status import StatusBuilder

status = StatusBuilder(bundle).build()
payload = DiscordFormatter().server_status(status).to_dict()
await channel.send(**payload)
```

Text is clipped to Discord limits and `@everyone` / `@here` mentions are made
safe.

## Diagnostics

Import:

```python
from erlc_api.diagnostics import diagnose_error, diagnose_status, diagnose_command_result
```

Diagnostics turn wrapper objects into user-facing messages.

```python
try:
    await api.players()
except Exception as exc:
    diagnostics = diagnose_error(exc)
    print(diagnostics.to_dict())
```

Use diagnostics for logs, bot replies, and dashboards; keep catching typed
exceptions for control flow.

## Cache

Import:

```python
from erlc_api.cache import AsyncCachedClient, CachedClient, MemoryCache
```

The default cache is memory-only TTL. It caches read endpoints only and never
caches `command(...)`.

```python
cached = AsyncCachedClient(api, ttl_s=5)

players = await cached.players()
again = await cached.players()  # served from cache for the same arguments
```

Applications that need custom stores can provide an adapter implementing the
documented cache protocol.

## Status

Import:

```python
from erlc_api.status import AsyncStatus, Status, StatusBuilder
```

Status builders produce typed dashboard snapshots:

```python
status = await AsyncStatus(api).get()
print(status.health, status.to_dict())
```

`StatusBuilder(bundle).build()` works with data you already fetched, avoiding
an extra HTTP call.

## Command Flows

Import:

```python
from erlc_api.command_flows import CommandFlowBuilder, CommandTemplate
```

Flows preview and validate command sequences. They do not execute commands.

```python
warn = CommandTemplate("warn", "warn {target} {reason}")

flow = (
    CommandFlowBuilder("warn-and-pm")
    .template(warn, target="Avi", reason="RDM")
    .step("pm Avi Please review the rules")
    .build()
)

print(flow.preview())
```

Common mistakes:

- Expecting rules or command flows to send PRC commands automatically.
- Using multi-server utilities for command broadcasting.
- Installing Pillow for geometry-only location helpers; it is only needed for
  rendered overlays.
- Caching command results. `CachedClient` intentionally caches read methods
  only.

## Related Pages

- [Utilities Reference](./Utilities-Reference.md)
- [Ops Utilities Reference](./Ops-Utilities-Reference.md)
- [Formatting, Analytics, and Export](./Formatting-Analytics-and-Export.md)

---

[Previous Page: Ops Utilities Reference](./Ops-Utilities-Reference.md) | [Next Page: Formatting, Analytics, and Export](./Formatting-Analytics-and-Export.md)
