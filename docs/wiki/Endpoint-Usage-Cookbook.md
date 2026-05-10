# Endpoint Usage Cookbook

This page shows common endpoint combinations. Use it when you know the task you
want to perform but not the exact method shape.

## Dashboard Snapshot

Fetch the sections most dashboards need:

```python
bundle = await api.bundle()

players = bundle.players_list
queue = bundle.queue_list
staff = bundle.staff_members
```

Return type: `ServerBundle`.

Use this for status panels, staff dashboards, and periodic snapshots.

For custom presets, use `bundle(...)` with a preset or include/exclude names:

```python
bundle = await api.bundle("dashboard", include="command_logs")
```

To turn that bundle into a dashboard-ready object:

```python
from erlc_api.status import StatusBuilder

status = StatusBuilder(bundle).build()
return status.to_dict()
```

## Full Server Bundle

Fetch every supported v2 section:

```python
bundle = await api.server(all=True)
```

This is convenient, but it can request more data than a command handler needs.
Prefer `bundle()` presets or explicit include flags in hot paths.

## Cached Reads

For bot commands and web dashboards that repeat the same reads, wrap the client
with a short memory TTL cache:

```python
from erlc_api.cache import AsyncCachedClient

cached = AsyncCachedClient(api, ttl_s=5)
players = await cached.players()
```

The cache applies to read endpoints only. Commands are never cached.

## Multi-server Overview

```python
from erlc_api.multiserver import AsyncMultiServer, ServerRef

servers = [
    ServerRef("main", "main-key"),
    ServerRef("training", "training-key"),
]

summary = await AsyncMultiServer(api, servers, concurrency=3).aggregate()
```

Use this for fleet dashboards. Results collect per-server errors by default.

## Player Lookup

```python
from erlc_api.find import Finder

bundle = await api.bundle(include="players", exclude=["staff", "queue", "vehicles", "emergency_calls"])
player = Finder(bundle).player("Avi")
```

Use `Finder` for human-facing lookup by partial name or user ID. Use direct
loops when exact matching is simpler.

## Moderation Logs

```python
logs = await api.logs("command")
recent_warns = [entry for entry in logs if entry.command.startswith(":warn")]
```

For richer filtering:

```python
from erlc_api.filter import Filter

warns = Filter(logs).command("warn").all()
```

## Queue View

```python
queue = await api.queue()

for position, user_id in enumerate(queue, start=1):
    print(position, user_id)
```

Return type: `list[int]`.

## Send Commands

```python
from erlc_api import CommandPolicy, cmd

policy = CommandPolicy(allowed={"h", "pm", "warn"}, max_length=120)

await api.command("h hello", policy=policy)
await api.command(cmd.pm("Player", "hello"), policy=policy)
await api.command(cmd("warn", "Player", "RDM"), policy=policy)
```

Use `preview_command(...)` for local previews:

```python
preview = await api.preview_command(cmd.pm("Player", "hello"), policy=policy)
print(preview.command, preview.allowed)
```

## Raw JSON Escape Hatch

Use `raw=True` when you need exact PRC payloads:

```python
payload = await api.server(all=True, raw=True)
```

Keep typed responses as the default for most application code.

## Low-level Request

Use `request()` for a newly added PRC endpoint before the wrapper has a typed
method:

```python
payload = await api.request("GET", "/v2/server", params={"Players": "true"})
```

Return type: decoded JSON when possible, otherwise response text.

## Utility Composition

```python
from erlc_api.analytics import Analyzer
from erlc_api.export import Exporter
from erlc_api.find import Finder
from erlc_api.location import LocationTools

bundle = await api.bundle()
player = Finder(bundle).player("Avi")
summary = Analyzer(bundle).dashboard()
markdown = Exporter(summary).markdown()
if bundle.emergency_calls_list:
    nearest = LocationTools(bundle).nearest_players_to_call(bundle.emergency_calls_list[0], limit=3)
```

Utilities stay lazy. Import only the modules you need.

## Alert Rules

Use rules when application code needs reusable alert conditions:

```python
from erlc_api.rules import RuleEngine, Conditions

engine = RuleEngine()
engine.add("queue-active", Conditions.queue_length(at_least=1), severity="info")
matches = engine.evaluate(bundle)
```

Rules return matches and optional callback results. They do not execute PRC
commands.

## Common Mistakes

- Calling `server(all=True)` inside every high-frequency command handler.
- Forgetting that multi-server helpers are read-only and will reject `command`.
- Caching reads for too long on fast-changing dashboards.
- Using `raw=True` everywhere and losing model helpers.
- Reimplementing filters and finders in bot code instead of using lazy utility
  modules.
- Forgetting `server_key=` when reusing one client across multiple servers.

## Related Pages

- [Quickstart: Discord.py](./Quickstart-Discord.py.md)
- [Models Reference](./Models-Reference.md)
- [Migration to v3](./Migration-to-v3.md)

---

[Previous Page: Quickstart: Discord.py](./Quickstart-Discord.py.md) | [Next Page: Migration to v3](./Migration-to-v3.md)
