# Endpoint Usage Cookbook

High-value endpoint patterns you can use directly.

## v2 selective fetch with fluent builder

```python
bundle = await (
    client.v2.server_query(ctx)
    .include_players()
    .include_staff()
    .include_helpers()
    .include_vehicles()
    .fetch_typed()
)
```

## v2 validated fetch (pydantic)

```python
bundle = await client.v2.server_validated(
    ctx,
    players=True,
    queue=True,
    strict=False,
)
```

## Command builder + tracking

```python
from erlc_api import CommandBuilder

result = await client.v1.command_with_tracking(
    ctx,
    CommandBuilder.pm(target="PlayerName", message="Hello"),
    timeout_s=8.0,
)
print(result.inferred_success, result.timed_out_waiting_for_log)
```

## Dry-run command validation

```python
preview = await client.v1.command(
    ctx,
    CommandBuilder.warn(target="PlayerName", reason="Follow rules"),
    dry_run=True,
)
print(preview)
```

## Stream logs as they arrive

```python
async for entry in client.v1.command_logs_stream(ctx, since_timestamp=1700000000):
    print(entry.timestamp, entry.player, entry.command)
```

## Track server state with callbacks

```python
from erlc_api import TrackerEvent

async with client.track_server(ctx, interval_s=2.0) as tracker:
    tracker.on(TrackerEvent.PLAYER_JOIN, lambda p: print("joined", p.name))
    tracker.on("command_executed", lambda c: print("cmd", c.command))  # string form also supported
```

## Cache controls

```python
stats = client.cache_stats()
await client.invalidate(ctx, "/v1/server/players")
```

## Parse `:log` payloads from command logs

```python
from erlc_api.helpers import fetch_log_commands

entries = await fetch_log_commands(client, ctx, payload_prefix="incident")
for item in entries:
    print(item.player, item.payload)
```

Note: `client.v1.command(...)` intentionally blocks `:log` execution.

## Next Steps

- Response mode selection: [Typed-vs-Raw-Responses.md](./Typed-vs-Raw-Responses.md)
- Reliability internals: [Rate-Limits-Retries-and-Reliability.md](./Rate-Limits-Retries-and-Reliability.md)
