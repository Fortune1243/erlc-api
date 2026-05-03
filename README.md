# erlc-api.py

Lightweight Python wrapper for the **ER:LC PRC API**. Version 2 is a breaking,
v2-first release with flat sync and async clients, typed dataclass responses by
default, `raw=True` escape hatches, flexible commands, and explicit utility
modules that only load when you import them.

## Install And Extras

```bash
pip install erlc-api.py
```

Development install:

```bash
pip install -e .[dev]
```

Optional extras:

| Extra | Installs | Used by |
| --- | --- | --- |
| `webhooks` | `cryptography` | Event webhook Ed25519 signature verification |
| `export` | `openpyxl` | `Exporter(...).xlsx(...)` |
| `time` | `python-dateutil` | `TimeTools().parse(..., enhanced=True)` |
| `rich` | `rich` | `Formatter().rich_table(...)` |
| `scheduling` | `apscheduler` | Advanced scheduling integrations around watchers |
| `utils` | all utility extras | Export, time, rich, and scheduling helpers |
| `all` | webhooks plus utility extras | Everything optional |

Example:

```bash
pip install "erlc-api.py[webhooks,export]"
```

## Quickstart

Async apps and bots:

```python
import asyncio
from erlc_api import AsyncERLC, cmd


async def main() -> None:
    async with AsyncERLC("server-key") as api:
        bundle = await api.server(players=True, queue=True, staff=True)
        result = await api.command(cmd.h("Hello from the API"))

        print(bundle.name, len(bundle.players or []), result.message)


asyncio.run(main())
```

Sync scripts:

```python
from erlc_api import ERLC

with ERLC("server-key") as api:
    players = api.players()
    result = api.command("h Hello")
    print(len(players), result.message)
```

## Client Reference

`AsyncERLC` is for async frameworks, Discord bots, FastAPI apps, background
workers, and anything already running an event loop.

```python
AsyncERLC(
    server_key: str | None = None,
    *,
    global_key: str | None = None,
    base_url: str = "https://api.policeroleplay.community",
    timeout_s: float = 20.0,
    retry_429: bool = True,
    user_agent: str | None = None,
)
```

Use it as an async context manager, or call `await api.start()` and
`await api.close()` yourself.

`ERLC` has the same constructor and method names for sync scripts:

```python
ERLC(
    server_key: str | None = None,
    *,
    global_key: str | None = None,
    base_url: str = "https://api.policeroleplay.community",
    timeout_s: float = 20.0,
    retry_429: bool = True,
    user_agent: str | None = None,
)
```

Every request sends `Server-Key`. If `global_key=` is configured, requests also
send `Authorization`.

Every endpoint method accepts `server_key=` so one client can work with multiple
servers:

```python
api = ERLC("primary-server-key")

primary = api.players()
secondary = api.players(server_key="secondary-server-key")
```

`validate_key()` and `health_check()` return `ValidationResult` instead of
raising common API errors.

## Endpoint Methods

Typed models are returned by default. Pass `raw=True` to receive the exact JSON
payload returned by PRC.

| Method | PRC endpoint | Default return type | Notes |
| --- | --- | --- | --- |
| `server(...)` | `GET /v2/server` | `ServerBundle` | Accepts include flags for v2 sections |
| `players()` | `GET /v2/server?Players=true` | `list[Player]` | Parses `PlayerName:Id` |
| `staff()` | `GET /v2/server?Staff=true` | `StaffList` | Staff object maps plus `.members()` |
| `queue()` | `GET /v2/server?Queue=true` | `list[int]` | Queue user IDs in API order |
| `join_logs()` | `GET /v2/server?JoinLogs=true` | `list[JoinLogEntry]` | Includes join/leave flag and timestamp |
| `kill_logs()` | `GET /v2/server?KillLogs=true` | `list[KillLogEntry]` | Includes killer/victim helpers |
| `command_logs()` | `GET /v2/server?CommandLogs=true` | `list[CommandLogEntry]` | Useful with `Finder` and `Analyzer` |
| `mod_calls()` | `GET /v2/server?ModCalls=true` | `list[ModCallEntry]` | Includes caller/moderator helpers |
| `emergency_calls()` | `GET /v2/server?EmergencyCalls=true` | `list[EmergencyCall]` | v2 emergency call payloads |
| `vehicles()` | `GET /v2/server?Vehicles=true` | `list[Vehicle]` | Vehicle model, owner, plate, color |
| `bans()` | `GET /v1/server/bans` | `BanList` | Uses v1 because v2 does not replace it |
| `command(command, ...)` | `POST /v2/server/command` | `CommandResult` | Accepts strings or `cmd` values |
| `request(method, path, ...)` | Any path | raw JSON/text | Low-level escape hatch |

`server()` include options:

```python
bundle = await api.server(players=True, queue=True, staff=True)
everything = await api.server(all=True)
custom = await api.server(include=["players", "vehicles"])
raw_payload = await api.server(all=True, raw=True)
```

## Command API

Commands are intentionally flexible:

```python
from erlc_api import cmd, normalize_command

await api.command(":h hi")
await api.command("h hi")
await api.command(cmd.h("hi"))
await api.command(cmd.pm("Player", "hello"))
await api.command(cmd("pm", "Player", "hello"))

assert normalize_command("h hi") == ":h hi"
```

Validation is minimal and predictable:

| Rule | Behavior |
| --- | --- |
| Leading colon missing | Added automatically |
| Blank command | Raises `ValueError` |
| Newline in command | Raises `ValueError` |
| Missing command name | Raises `ValueError` |
| `:log` | Not blocked by the wrapper |

Dry-run validates and returns a local `CommandResult` without sending HTTP:

```python
preview = await api.command(cmd.pm("Player", "hello"), dry_run=True)
print(preview.raw["command"], preview.success)
```

## Models

Models are frozen dataclasses. They preserve the original payload in `.raw`,
unknown fields in `.extra`, and convert back to dictionaries with `.to_dict()`.

Key models:

| Model | Returned by | Useful fields |
| --- | --- | --- |
| `ServerInfo` | `server()` without sections | `name`, `owner_id`, `current_players`, `max_players` |
| `ServerBundle` | `server()` | server fields plus optional `players`, `staff`, logs, queue, vehicles |
| `Player` | `players()` | `player`, `name`, `user_id`, `permission`, `callsign`, `team`, `location` |
| `StaffList` | `staff()` | `co_owners`, `admins`, `mods`, `helpers`, `.members()` |
| `CommandLogEntry` | `command_logs()` | `player`, `name`, `user_id`, `timestamp`, `command` |
| `CommandResult` | `command()` | `message`, `success` |

```python
players = await api.players()
first = players[0]

print(first.name, first.user_id)
print(first.extra)
print(first.to_dict())
```

Parse PRC `PlayerName:Id` strings directly:

```python
from erlc_api import parse_player_identifier

name, user_id = parse_player_identifier("Avi:123")
```

## Utility Modules

Utilities are explicit lazy modules. `import erlc_api` only imports clients,
models, errors, and `cmd`.

| Module | Import | Purpose |
| --- | --- | --- |
| Find | `from erlc_api.find import Finder` | Look up players, staff, vehicles, logs, bans, and calls |
| Filter | `from erlc_api.filter import Filter` | Chain filters and return `.all()`, `.first()`, `.count()` |
| Sort | `from erlc_api.sort import Sorter` | Sort by name, timestamp, team, permission, queue position, vehicle fields |
| Group | `from erlc_api.group import Grouper` | Group by team, permission, role, owner, command, day, hour |
| Diff | `from erlc_api.diff import Differ` | Compare lists or full server bundles |
| Wait | `from erlc_api.wait import AsyncWaiter, Waiter` | Poll until joins, leaves, queue changes, logs, or counts occur |
| Watch | `from erlc_api.watch import AsyncWatcher, Watcher` | Stream snapshot diffs as events and callbacks |
| Format | `from erlc_api.format import Formatter` | Compact Discord-safe, console-safe, and rich text formatting |
| Analytics | `from erlc_api.analytics import Analyzer` | Dashboard summaries, distributions, command usage, moderation trends |
| Export | `from erlc_api.export import Exporter` | JSON, CSV, Markdown, HTML, optional XLSX |
| Moderation | `from erlc_api.moderation import AsyncModerator, Moderator` | Safe command composition, previews, audit messages |
| Time | `from erlc_api.time import TimeTools` | Timestamp parsing, age strings, windows, timezone formatting |
| Schema | `from erlc_api.schema import SchemaInspector` | Field discovery, raw/extra inspection, payload diagnostics |
| Snapshot | `from erlc_api.snapshot import SnapshotStore` | JSONL snapshot persistence and latest-state comparisons |
| Audit | `from erlc_api.audit import AuditLog` | JSON-safe audit events for commands, webhooks, watchers, and moderation |
| Idempotency | `from erlc_api.idempotency import MemoryDeduper, FileDeduper` | TTL dedupe for webhook deliveries and watcher restarts |
| Limits | `from erlc_api.limits import poll_plan, safe_interval` | Conservative polling guidance without fake PRC limit claims |
| Custom Commands | `from erlc_api.custom_commands import CustomCommandRouter` | Framework-neutral router for PRC webhook messages starting with `;` |

Example:

```python
from erlc_api.find import Finder
from erlc_api.filter import Filter
from erlc_api.export import Exporter
from erlc_api.snapshot import SnapshotStore

bundle = await api.server(all=True)
player = Finder(bundle).player("Avi")
police = Filter(bundle.players or []).team("Police").all()
csv_text = Exporter(police).csv()
SnapshotStore("snapshots.jsonl").save(bundle)
```

Custom in-game commands are received through PRC Event Webhooks. Use
`erlc_api.webhooks` for signature verification and `erlc_api.custom_commands`
for flexible routing:

```python
from erlc_api.custom_commands import CustomCommandRouter

router = CustomCommandRouter(prefix=";")


@router.command("ping", "p")
async def ping(ctx):
    return ctx.reply("pong")


result = await router.dispatch({"Message": ";p"})
```

## Errors

All wrapper exceptions inherit from `ERLCError`.

| Exception | Raised when |
| --- | --- |
| `APIError` | Non-success response without a more specific mapping |
| `BadRequestError` | Request payload, path, or params are invalid |
| `AuthError` | Server key or global key is missing, invalid, banned, or unauthorized |
| `PermissionDeniedError` | A valid key cannot access the resource |
| `NotFoundError` | The requested API path/resource was not found |
| `NetworkError` | Timeout, DNS, connection, or transport failure |
| `RateLimitError` | PRC returns `429` or a rate-limit error code |
| `InvalidCommandError` | Command syntax/payload is rejected by PRC |
| `RestrictedCommandError` | PRC restricts the command from API execution |
| `ProhibitedMessageError` | Command text is prohibited by PRC |
| `ServerOfflineError` | Server is offline or unavailable for the request |
| `RobloxCommunicationError` | PRC cannot communicate with Roblox or the module |
| `ModuleOutdatedError` | In-game module must be updated |
| `ModelDecodeError` | Typed decoding received an unexpected payload shape |

```python
from erlc_api import ERLCError, RateLimitError

try:
    players = await api.players()
except RateLimitError as exc:
    print(exc.retry_after, exc.reset_epoch_s, exc.bucket)
except ERLCError as exc:
    print(exc.status_code, exc.error_code, exc.body_excerpt)
```

## Rate Limits

On `429`, `RateLimitError` exposes:

| Attribute | Meaning |
| --- | --- |
| `retry_after` / `retry_after_s` | Seconds to wait when PRC provides `Retry-After` or body retry data |
| `reset_epoch_s` | Epoch reset time parsed from `X-RateLimit-Reset` |
| `bucket` | Bucket name from `X-RateLimit-Bucket` |
| `error_code` | PRC error code when present |

By default `retry_429=True`, so the transport sleeps once and retries once when
it has retry timing. Set `retry_429=False` to handle rate limits yourself.

## Documentation Deep Dives

The README is the compact API reference. The full documentation source lives in
`docs/wiki`:

- [Clients and Authentication](docs/wiki/Clients-and-Authentication.md)
- [Endpoint Reference](docs/wiki/Endpoint-Reference.md)
- [Models Reference](docs/wiki/Models-Reference.md)
- [Commands Reference](docs/wiki/Commands-Reference.md)
- [Utilities Reference](docs/wiki/Utilities-Reference.md)
- [Custom Commands Reference](docs/wiki/Custom-Commands-Reference.md)
- [Waiters and Watchers](docs/wiki/Waiters-and-Watchers.md)
- [Formatting, Analytics, and Export](docs/wiki/Formatting-Analytics-and-Export.md)
- [Moderation Helpers](docs/wiki/Moderation-Helpers.md)
- [Webhooks Reference](docs/wiki/Webhooks-Reference.md)
- [Errors and Rate Limits](docs/wiki/Errors-and-Rate-Limits.md)
- [Migration to v2](docs/wiki/Migration-to-v2.md)

## Development

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q
python -m ruff check src tests scripts
```
