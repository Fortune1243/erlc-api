# Endpoint Usage Cookbook

High-value endpoint patterns you can copy directly.

## Server status

```python
status = await client.v1.server(ctx)
print(status)
```

## Typed players list + filtering

```python
from erlc_api.utils.filters import filter_players

players = await client.v1.players_typed(ctx)
police_players = filter_players(players, team="Police")
```

## Queue diff between snapshots

```python
from erlc_api.utils.diff import diff_queue

before = await client.v1.queue_typed(ctx)
after = await client.v1.queue_typed(ctx)
changes = diff_queue(before, after)
print("joined:", len(changes.joined), "left:", len(changes.left), "moved:", len(changes.moved))
```

## Remote command execution

```python
result = await client.v1.command(ctx, ":h Server restart in 5 minutes")
print(result)
```

Note: this wrapper intentionally blocks `:log` command execution via `client.v1.command(...)`. Use command log retrieval for `:log` workflows.

## Parse `:log` payloads from command logs

```python
from erlc_api.helpers import fetch_log_commands

entries = await fetch_log_commands(client, ctx, payload_prefix="incident")
for item in entries:
    print(item.player, item.payload)
```

## Next Steps

- See response tradeoffs in [Typed-vs-Raw-Responses.md](./Typed-vs-Raw-Responses.md)
- Production hardening guide: [Rate-Limits-Retries-and-Reliability.md](./Rate-Limits-Retries-and-Reliability.md)
