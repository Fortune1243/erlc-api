# erlc-api

A production-ready asynchronous Python wrapper for the **ER:LC PRC Private Server API** with first-class **v1 + v2** support, multi-server contexts, typed models, resilience controls, and integration helpers.

> Release status in this repo: **v1.0.1** + unreleased enhancements documented below.

---

## Why `erlc-api`

`erlc-api` is designed for real bot/backend operations, not thin endpoint forwarding.

- Async-first `httpx` client
- Multi-server contexts from one shared client
- Bucket-aware rate limiting with reset-aware pre-acquire
- Configurable retries (`429` / `5xx` / network) with exponential backoff + jitter
- Optional in-flight request coalescing for identical idempotent GET calls
- Built-in TTL caching + manual invalidation + cache statistics
- Optional per-bucket circuit breaker
- Raw + typed + validated v2 response modes
- Structured command ergonomics with dry-run and tracking
- Log stream helpers and live server tracker
- Expanded production error taxonomy

---

## Installation

```bash
pip install -e .
```

Development:

```bash
pip install -e .[dev]
```

Optional extras:

```bash
pip install -e .[pydantic]       # validated v2 models
pip install -e .[redis]          # redis cache backend
pip install -e .[observability]  # structlog + opentelemetry-api
pip install -e .[all]            # all optional extras
```

Requirements:

- Python 3.11+
- `httpx>=0.27.0`

---

## Quickstart

```python
import asyncio
from erlc_api import ERLCClient


async def main() -> None:
    async with ERLCClient() as client:
        ctx = client.ctx("your-server-key")

        server = await client.v1.server(ctx)
        bundle = await client.v2.server_default_typed(ctx)
        validation = await client.validate_key(ctx)

        print(server)
        print(bundle.server_name)
        print(validation.status)


asyncio.run(main())
```

---

## API Surfaces

### v1 methods

Raw:

- `client.v1.command(ctx, command, dry_run=False)`
- `client.v1.server(ctx)`
- `client.v1.players(ctx)`
- `client.v1.join_logs(ctx)`
- `client.v1.queue(ctx)`
- `client.v1.kill_logs(ctx)`
- `client.v1.command_logs(ctx)`
- `client.v1.mod_calls(ctx)`
- `client.v1.bans(ctx)`
- `client.v1.vehicles(ctx)`
- `client.v1.staff(ctx)`

Typed:

- `client.v1.command_typed(...)`
- `client.v1.server_typed(...)`
- `client.v1.players_typed(...)`
- `client.v1.join_logs_typed(...)`
- `client.v1.queue_typed(...)`
- `client.v1.kill_logs_typed(...)`
- `client.v1.command_logs_typed(...)`
- `client.v1.mod_calls_typed(...)`
- `client.v1.bans_typed(...)`
- `client.v1.vehicles_typed(...)`
- `client.v1.staff_typed(...)`

Command ergonomics:

- `client.v1.send_command(...)`
- `client.v1.command_with_tracking(...)`
- `client.v1.command_history(...)`

Log streams:

- `client.v1.command_logs_stream(...)`
- `client.v1.join_logs_stream(...)`
- `client.v1.kill_logs_stream(...)`

### v2 methods

Raw:

- `client.v2.server(...)`
- `client.v2.server_all(...)`
- `client.v2.server_default(...)`

Typed dataclass:

- `client.v2.server_typed(...)`
- `client.v2.server_all_typed(...)`
- `client.v2.server_default_typed(...)`

Validated (requires `pydantic` extra):

- `client.v2.server_validated(..., strict=False)`
- `client.v2.server_all_validated(..., strict=False)`
- `client.v2.server_default_validated(..., strict=False)`

Fluent v2 query builder:

- `client.v2.server_query(ctx)`
- Includes: `.include_players()`, `.include_staff()`, `.include_helpers()`, `.include_join_logs()`, `.include_queue()`, `.include_kill_logs()`, `.include_command_logs()`, `.include_mod_calls()`, `.include_vehicles()`, `.include_emergency_calls()`, `.include_all()`
- Fetch: `.fetch()`, `.fetch_typed()`, `.fetch_validated(strict=False)`

---

## Typed Models (Highlights)

- `Player` includes `wanted_stars` and `location_typed: PlayerLocation | None`
- `Vehicle` includes `color_hex`, `color_name`, `color_info: VehicleColor | None`
- `V2ServerBundle` includes `helpers` and `emergency_calls`
- `EmergencyCall` includes team/caller/position/started timestamp helpers
- Unknown fields are preserved via `extra`
- Top-level shape mismatch raises `ModelDecodeError`

---

## Client Reliability and Operations

### `ClientConfig` capabilities

- Retry config: `max_retries`, `retry_429`, `retry_5xx`, `retry_network`
- Backoff config: `backoff_base_s`, `backoff_cap_s`, `backoff_jitter_s`
- Connection pooling: `max_connections`, `max_keepalive_connections`, `keepalive_expiry_s`
- Coalescing: `request_coalescing`
- Cache: `cache_enabled`, `cache_backend`, `cache_ttl_by_path`
- Circuit breaker: `circuit_breaker_enabled`, `circuit_failure_threshold`, `circuit_open_s`
- Observability hooks: `metrics_sink`, `use_structlog`, `opentelemetry_tracing_enabled`, `debug_dump`
- Request replay buffer: `request_replay_size`

### Cache controls

```python
await client.invalidate(ctx)                     # all cached endpoints for ctx
await client.invalidate(ctx, "/v1/server")      # specific endpoint
await client.clear_cache()                       # clear all cache entries
print(client.cache_stats())                      # hit/miss + backend stats
```

### Request replay (debug)

```python
for item in client.request_replay(limit=20):
    print(item["method"], item["path"], item["status"])
```

---

## Server Tracking and Events

```python
async with client.track_server(ctx, interval_s=2.0) as tracker:
    tracker.on("player_join", lambda player: print("joined", player.name))
    tracker.on("command_executed", lambda entry: print("cmd", entry.command))

    await asyncio.sleep(10)
    print("players", len(tracker.players))
```

Supported event names:

- `player_join`
- `player_leave`
- `staff_join`
- `staff_leave`
- `command_executed`
- `snapshot`

---

## Command Builder

```python
from erlc_api import CommandBuilder

cmd = CommandBuilder.pm(target="PlayerName", message="Hello")
result = await client.v1.command_with_tracking(ctx, cmd, timeout_s=8.0)
print(result.inferred_success, result.timed_out_waiting_for_log)
```

`client.v1.command(...)` intentionally blocks `:log` execution; use command log retrieval/helpers for `:log` workflows.

---

## Error Taxonomy

Base classes:

- `ERLCError`
- `APIError`
- `AuthError`
- `NotFoundError`
- `NetworkError`
- `RateLimitError`
- `ModelDecodeError`

Extended classes:

- `PermissionDeniedError`
- `PlayerNotFoundError`
- `ServerEmptyError`
- `RobloxCommunicationError`
- `InvalidCommandError`
- `CircuitOpenError`

---

## Validation Helpers

```python
result = await client.validate_key(ctx)
if result.status != "ok":
    print(result.status, result.retry_after)
```

Aliases/utilities:

- `await client.health_check(ctx)`
- `helpers.validate_server_key(client, ctx)`
- `helpers.fetch_log_commands(client, ctx, payload_prefix=...)`

---

## Notes

- Non-idempotent command requests are not auto-replayed.
- v2 access depends on PRC allowing your key.
- `py.typed` is included for static typing support.
