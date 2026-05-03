# Endpoint Usage Cookbook

This page shows common endpoint combinations. Use it when you know the task you
want to perform but not the exact method shape.

## Dashboard Snapshot

Fetch the sections most dashboards need:

```python
bundle = await api.server(players=True, queue=True, staff=True)

players = bundle.players or []
queue = bundle.queue or []
staff = bundle.staff.members() if bundle.staff else []
```

Return type: `ServerBundle`.

Use this for status panels, staff dashboards, and periodic snapshots.

## Full Server Bundle

Fetch every supported v2 section:

```python
bundle = await api.server(all=True)
```

This is convenient, but it can request more data than a command handler needs.
Prefer explicit include flags in hot paths.

## Player Lookup

```python
from erlc_api.find import Finder

bundle = await api.server(players=True)
player = Finder(bundle).player("Avi")
```

Use `Finder` for human-facing lookup by partial name or user ID. Use direct
loops when exact matching is simpler.

## Moderation Logs

```python
logs = await api.command_logs()
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
from erlc_api import cmd

await api.command("h hello")
await api.command(cmd.pm("Player", "hello"))
await api.command(cmd("warn", "Player", "RDM"))
```

Use `dry_run=True` for previews:

```python
preview = await api.command(cmd.pm("Player", "hello"), dry_run=True)
print(preview.raw["command"])
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

bundle = await api.server(all=True)
player = Finder(bundle).player("Avi")
summary = Analyzer(bundle).dashboard()
markdown = Exporter(summary).markdown()
```

Utilities stay lazy. Import only the modules you need.

## Common Mistakes

- Calling `server(all=True)` inside every high-frequency command handler.
- Using `raw=True` everywhere and losing model helpers.
- Reimplementing filters and finders in bot code instead of using lazy utility
  modules.
- Forgetting `server_key=` when reusing one client across multiple servers.

## Related Pages

- [Endpoint Reference](./Endpoint-Reference.md)
- [Models Reference](./Models-Reference.md)
- [Utilities Reference](./Utilities-Reference.md)

---

[Previous Page: Endpoint Reference](./Endpoint-Reference.md) | [Next Page: Models Reference](./Models-Reference.md)
