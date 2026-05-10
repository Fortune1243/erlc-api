# erlc-api.py

[![PyPI](https://img.shields.io/pypi/v/erlc-api.py)](https://pypi.org/project/erlc-api.py/)
[![Python](https://img.shields.io/pypi/pyversions/erlc-api.py)](https://pypi.org/project/erlc-api.py/)
[![License](https://img.shields.io/badge/license-Custom_Attribution-blue)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/Fortune1243/erlc-api)](https://github.com/Fortune1243/erlc-api)

The most complete Python wrapper for the **ER:LC PRC API**. The only library
with both sync and async clients, a command safety policy system, 14 typed
exception classes, and 30+ production utility modules — built for bots and
dashboards that have to be correct, not just functional.

Install the PyPI package as `erlc-api.py`; import it in Python as `erlc_api`.

## Why erlc-api.py

- **Only ERLC wrapper with both sync + async** — `ERLC` and `AsyncERLC` share
  identical method names, so scripts, Discord bots, and FastAPI apps use the
  same library.
- **14 typed exceptions** — catch `RateLimitError`, `RestrictedCommandError`,
  `ServerOfflineError`, and 11 more without pattern-matching error strings.
- **`CommandPolicy`** — the only command safety system in any ERLC Python
  library; define an allowlist, cap length, and dry-run before any HTTP is sent.
- **30+ lazy utility modules** — analytics, export (CSV/JSON/HTML/XLSX), rules
  engine, moderation helpers, Discord embed builders, multi-server aggregation,
  and more; none load unless you import them.
- **Frozen dataclass responses** — typed, immutable, thread-safe by default,
  with `.raw`, `.extra`, and `.to_dict()` on every model.
- **Per-request `server_key=`** — one client instance, any number of servers.

[Full comparison with other ER:LC wrappers →](comparison.md)

## Highlights

- Sync `ERLC` and async `AsyncERLC` clients with the same flat method names.
- Typed frozen dataclasses with `.raw`, `.extra`, and `.to_dict()`.
- v2-first coverage for players, locations, wanted stars, vehicles, emergency calls, and commands.
- Dynamic rate limiting on by default, plus explicit read caching when you choose it.
- Vehicle catalog/tools, permission levels, command metadata, and safe command policy helpers.
- Lazy utility modules: import only the tools your bot, script, or dashboard needs.

## Install And Extras

```bash
pip install erlc-api.py
```

Requires Python `>=3.11`.

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
| `location` | `Pillow` | Optional map overlays through `MapRenderer` |
| `utils` | all utility extras | Export, time, rich, scheduling, and location helpers |
| `all` | webhooks plus utility extras | Everything optional |

Example:

```bash
pip install "erlc-api.py[webhooks,export]"
```

## Package Name And Import Name

| Where | Name |
| --- | --- |
| PyPI install | `pip install erlc-api.py` |
| Python import | `import erlc_api` |
| Core imports | `from erlc_api import AsyncERLC, ERLC, cmd` |

The repository URL still uses `erlc-api`, but the published package name is
`erlc-api.py` to avoid ambiguity with other packages.

## Quickstart

Async apps and bots:

```python
import asyncio
from erlc_api import AsyncERLC, CommandPolicy, cmd


async def main() -> None:
    policy = CommandPolicy(allowed={"h"}, max_length=120)
    async with AsyncERLC("server-key") as api:
        bundle = await api.server(players=True, queue=True, staff=True)
        preview = await api.command(policy.validate(cmd.h("Hello from the API")), dry_run=True)

        print(bundle.name, len(bundle.players or []), preview.raw["command"])


asyncio.run(main())
```

Sync scripts:

```python
from erlc_api import ERLC, CommandPolicy

with ERLC("server-key") as api:
    policy = CommandPolicy(allowed={"h"}, max_length=120)
    players = api.players()
    result = api.command(policy.validate("h Hello"), dry_run=True)
    print(len(players), result.message)
```

Multi-server reads:

```python
from erlc_api import AsyncERLC
from erlc_api.multiserver import AsyncMultiServer, ServerRef

servers = [
    ServerRef("main", "main-server-key"),
    ServerRef("training", "training-server-key"),
]

async with AsyncERLC() as api:
    summary = await AsyncMultiServer(api, servers, concurrency=3).aggregate()
    print(summary["servers"], summary["players"])
```

Webhook custom commands:

```python
from erlc_api.custom_commands import CustomCommandRouter
from erlc_api.webhooks import assert_valid_event_webhook_signature

router = CustomCommandRouter(prefix=";")


@router.command("ping")
async def ping(ctx):
    return ctx.reply("pong")


async def handle_webhook(raw_body, headers, payload):
    assert_valid_event_webhook_signature(raw_body=raw_body, headers=headers)
    return await router.dispatch(payload)
```

## Safe Defaults

- Dynamic process-local rate limiting is enabled by default with
  `rate_limited=True`.
- `retry_429=True` sleeps once and retries once when PRC provides retry timing.
- Commands stay flexible, but bot/web examples should gate execution with
  `CommandPolicy`, permissions, and cooldowns.
- Server keys are never stored or encrypted by the wrapper; keep them in your
  secret manager or environment.

```python
from erlc_api.security import key_fingerprint

print(key_fingerprint("server-key"))  # safe for logs; never log the key itself
```

## Client Reference

`AsyncERLC` is for async frameworks, Discord bots, FastAPI apps, background
workers, and anything already running an event loop.

```python
AsyncERLC(
    server_key: str | None = None,
    *,
    global_key: str | None = None,
    base_url: str = "https://api.erlc.gg",
    timeout_s: float = 20.0,
    retry_429: bool = True,
    rate_limited: bool = True,
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
    base_url: str = "https://api.erlc.gg",
    timeout_s: float = 20.0,
    retry_429: bool = True,
    rate_limited: bool = True,
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

Typed models are returned by default. Pass `raw=True` when you need raw PRC data;
the exact shape depends on the method and is summarized below.

| Method | PRC endpoint | Default return type | Notes |
| --- | --- | --- | --- |
| `server(...)` | `GET /v2/server` | `ServerBundle` | Accepts include flags for v2 sections |
| `players()` | `GET /v2/server?Players=true` | `list[Player]` | Parses `PlayerName:Id` |
| `staff()` | `GET /v2/server?Staff=true` | `StaffList` | Staff object maps plus `.members` |
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

### Endpoint Version Map

| API area | PRC version | Wrapper methods |
| --- | --- | --- |
| Server status and includes | v2 | `server`, `players`, `staff`, `queue`, logs, `vehicles`, `emergency_calls` |
| Command execution | v2 | `command` |
| Bans | v1 | `bans` |
| Custom requests | caller chooses | `request` |

### Support Matrix

| Feature | Built in | Notes |
| --- | --- | --- |
| Async client | Yes | `AsyncERLC` |
| Sync client | Yes | `ERLC` |
| Typed dataclasses | Yes | Default response mode |
| Raw PRC data | Yes | `raw=True` |
| Dynamic rate limiting | Yes | Enabled by default, process-local |
| Event webhook verification | Optional extra | `erlc-api.py[webhooks]` |
| Discord bot framework | No | Docs use `discord.py`; wrapper stays framework-neutral |
| Persistent/distributed cache | No | Bring your own adapter or external store |

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
from erlc_api import CommandPolicy, CommandPolicyError, cmd, normalize_command

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

For Discord bots, web routes, and custom-command handlers, put an application
policy in front of command execution:

```python
policy = CommandPolicy(allowed={"h", "pm"}, max_length=120)

try:
    safe_command = policy.validate(cmd.h("Short staff announcement"))
except CommandPolicyError as exc:
    print(exc.result.reason)
else:
    await api.command(safe_command)
```

`CommandPolicy.check(...)` returns a `CommandPolicyResult` for previews and UI;
`CommandPolicy.validate(...)` raises `CommandPolicyError` when blocked.

## Raw Response Behavior

`raw=True` returns PRC data before typed model decoding, but wrapper convenience
methods intentionally return the section they are named after:

| Call | `raw=True` returns |
| --- | --- |
| `api.server(raw=True)` | Full `/v2/server` payload |
| `api.server(players=True, raw=True)` | Full `/v2/server` payload including `Players` |
| `api.players(raw=True)` | Raw `Players` list only |
| `api.staff(raw=True)` | Raw `Staff` object only |
| `api.queue(raw=True)` | Raw `Queue` list only |
| log/vehicle/call helpers with `raw=True` | Raw section list only |
| `api.bans(raw=True)` | Full raw v1 bans mapping |
| `api.command(raw=True)` | Raw v2 command response |
| `api.request(...)` | Raw decoded response body |

Model `.to_dict()` output uses wrapper field names and helper shapes. It is
JSON-safe, but it is not guaranteed to be byte-for-byte identical to PRC JSON.

## Models

Models are frozen dataclasses. They preserve the original payload in `.raw`,
unknown fields in `.extra`, and convert back to dictionaries with `.to_dict()`.

Key models:

| Model | Returned by | Useful fields |
| --- | --- | --- |
| `ServerInfo` | `server()` without sections | `name`, `owner_id`, `current_players`, `max_players` |
| `ServerBundle` | `server()` | server fields plus optional `players`, `staff`, logs, queue, vehicles |
| `Player` | `players()` | `player`, `name`, `user_id`, `permission`, `callsign`, `team`, `location` |
| `StaffList` | `staff()` | `co_owners`, `admins`, `mods`, `helpers`, `.members` |
| `CommandLogEntry` | `command_logs()` | `player`, `name`, `user_id`, `timestamp`, `command` |
| `Vehicle` | `vehicles()` | `name`, `model_name`, `year`, `owner_name`, `plate`, `color` |
| `EmergencyCall` | `emergency_calls()` | `team`, `caller`, `players`, `position`, `started_at` |
| `CommandResult` | `command()` | `message`, `success`, `command_id` |

```python
players = await api.players()
first = players[0]

print(first.name, first.user_id)
print(first.extra)
print(first.to_dict())
```

Permission strings stay raw for compatibility, with ordered enum helpers:

```python
from erlc_api import PermissionLevel

if first.permission_level >= PermissionLevel.MOD:
    print("staff-capable player")
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
| Watch | `from erlc_api.watch import AsyncWatcher, Watcher` | Stream snapshot diffs as events and callbacks |
| Vehicles | `from erlc_api.vehicles import VehicleTools` | Vehicle catalog, model/year parsing, plates, owners, summaries |
| Emergency | `from erlc_api.emergency import EmergencyCallTools` | Active/unresponded calls, team filters, nearest-call helpers |
| Multi Server | `from erlc_api.multiserver import AsyncMultiServer, MultiServer` | Read and aggregate multiple named servers with bounded concurrency |
| Discord Tools | `from erlc_api.discord_tools import DiscordFormatter` | Dependency-free Discord embed/message payload dictionaries |
| Cache | `from erlc_api.cache import AsyncCachedClient, CachedClient` | Explicit memory TTL caching for read endpoints plus adapter protocols |
| Rules | `from erlc_api.rules import RuleEngine, Conditions` | Evaluate flexible alert rules and return matches/callback results |
| Analytics | `from erlc_api.analytics import Analyzer` | Dashboard summaries, distributions, command usage, moderation trends |
| Export | `from erlc_api.export import Exporter` | JSON, CSV, Markdown, HTML, optional XLSX |
| Moderation | `from erlc_api.moderation import AsyncModerator, Moderator` | Safe command composition, previews, audit messages |

See [Function List](docs/wiki/Function-List.md) and
[Utilities Reference](docs/wiki/Utilities-Reference.md) for the full module
index.

Example:

```python
from erlc_api.find import Finder
from erlc_api.filter import Filter
from erlc_api.export import Exporter
from erlc_api.bundle import AsyncBundle
from erlc_api.status import StatusBuilder
from erlc_api.vehicles import VehicleTools

bundle = await AsyncBundle(api).dashboard()
player = Finder(bundle).player("Avi")
police = Filter(bundle.players or []).team("Police").all()
vehicle_summary = VehicleTools(bundle).summary()
csv_text = Exporter(police).csv()
status = StatusBuilder(bundle).build()
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

Dynamic rate limiting is enabled by default. It learns from PRC rate-limit
headers and waits before avoidable requests:

```python
api = AsyncERLC("server-key")
print(api.rate_limits)
```

Pass `rate_limited=False` only when your application has its own limiter and
you want to disable the wrapper's pre-request waiting.

## Known Limitations

- Built-in rate limiting is process-local. Multiple bot shards, containers, or
  workers need external coordination if they share keys.
- The wrapper does not store, encrypt, rotate, or validate server keys unless
  your app calls `validate_key()`.
- Command execution is powerful. Gate it with Discord permissions, web auth,
  cooldowns, `CommandPolicy`, dry-run previews, and audit logs.
- Discord and FastAPI examples are safe templates, not complete production bot
  or web security systems.
- Optional rendering/export/webhook features load only when explicitly imported
  and installed through extras.

## Documentation Deep Dives

The README is the compact API reference. The full documentation source lives in
`docs/wiki`:

- [Home](docs/wiki/Home.md)
- [Installation and Extras](docs/wiki/Installation-and-Extras.md)
- [Getting Started](docs/wiki/Getting-Started.md)
- [Quickstart: Web Backend](docs/wiki/Quickstart-Web-Backend.md)
- [Quickstart: Discord.py](docs/wiki/Quickstart-Discord.py.md)
- [FAQ](docs/wiki/FAQ.md)
- [Clients and Authentication](docs/wiki/Clients-and-Authentication.md)
- [Endpoint Reference](docs/wiki/Endpoint-Reference.md)
- [Endpoint Usage Cookbook](docs/wiki/Endpoint-Usage-Cookbook.md)
- [Models Reference](docs/wiki/Models-Reference.md)
- [Typed vs Raw Responses](docs/wiki/Typed-vs-Raw-Responses.md)
- [Commands Reference](docs/wiki/Commands-Reference.md)
- [Function List](docs/wiki/Function-List.md)
- [Utilities Reference](docs/wiki/Utilities-Reference.md)
- [Vehicle Tools](docs/wiki/Vehicle-Tools.md)
- [Emergency Calls](docs/wiki/Emergency-Calls.md)
- [Permission Levels](docs/wiki/Permission-Levels.md)
- [Wanted Stars](docs/wiki/Wanted-Stars.md)
- [Scaling Your App](docs/wiki/Scaling-Your-App.md)
- [Ops Utilities Reference](docs/wiki/Ops-Utilities-Reference.md)
- [Workflow Utilities Reference](docs/wiki/Workflow-Utilities-Reference.md)
- [Formatting, Analytics, and Export](docs/wiki/Formatting-Analytics-and-Export.md)
- [Moderation Helpers](docs/wiki/Moderation-Helpers.md)
- [Waiters and Watchers](docs/wiki/Waiters-and-Watchers.md)
- [Webhooks Reference](docs/wiki/Webhooks-Reference.md)
- [Event Webhooks and Custom Commands](docs/wiki/Event-Webhooks-and-Custom-Commands.md)
- [Custom Commands Reference](docs/wiki/Custom-Commands-Reference.md)
- [Security and Secrets](docs/wiki/Security-and-Secrets.md)
- [Rate Limits, Retries, and Reliability](docs/wiki/Rate-Limits-Retries-and-Reliability.md)
- [Errors and Rate Limits](docs/wiki/Errors-and-Rate-Limits.md)
- [Error Handling and Troubleshooting](docs/wiki/Error-Handling-and-Troubleshooting.md)
- [Testing and Mocking](docs/wiki/Testing-and-Mocking.md)
- [Migration to v2](docs/wiki/Migration-to-v2.md)
- [Comparison and Why erlc-api.py](docs/wiki/Comparison-and-Why-erlc-api.md)

## Development

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q
python -m ruff check src tests scripts
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Public behavior changes should include
tests, docs, and a changelog entry.

## Support

For questions and vulnerability reports, contact Avi Sehrawat on Discord:
`avi1243`.

## License

`erlc-api.py` uses a custom attribution license. You may use, modify, and
redistribute it, but public or distributed use must retain the license and give
reasonable visible credit as described in [LICENSE](LICENSE).

## Disclaimer

This is an independent community wrapper. It is not an official PRC, ER:LC, or
Roblox product.
