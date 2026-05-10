# erlc-api.py

[![PyPI](https://img.shields.io/pypi/v/erlc-api.py)](https://pypi.org/project/erlc-api.py/)
[![Python](https://img.shields.io/pypi/pyversions/erlc-api.py)](https://pypi.org/project/erlc-api.py/)
[![License](https://img.shields.io/badge/license-Custom_Attribution-blue)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://fortune1243.github.io/erlc-api)
[![Last Commit](https://img.shields.io/github/last-commit/Fortune1243/erlc-api)](https://github.com/Fortune1243/erlc-api)

`erlc-api.py` is a typed, v2-first Python wrapper for the ER:LC PRC API. It
ships matching sync and async clients, safe defaults for bots, typed dataclass
responses, raw payload escape hatches, and optional utilities for dashboards,
Discord bots, moderation workflows, exports, webhooks, and multi-server reads.

Install the package as `erlc-api.py`; import it as `erlc_api`.

```bash
pip install erlc-api.py
```

Requires Python `>=3.11`.

## Quickstart

Sync scripts:

```python
from erlc_api import Client

with Client.from_env() as api:
    players = api.players()
    print([player.name for player in players])
```

Async apps and bots:

```python
from erlc_api import AsyncClient

async with AsyncClient.from_env() as api:
    bundle = await api.bundle()
    print(bundle.name, len(bundle.players_list), len(bundle.queue_list))
```

Set your key through the environment:

```bash
set ERLC_SERVER_KEY=your-server-key
```

Use `ERLC_GLOBAL_KEY` only when PRC gives your application an Authorization key.

## What You Get

- `Client` / `ERLC` for sync scripts.
- `AsyncClient` / `AsyncERLC` for async bots, web apps, and workers.
- Flat endpoint methods: `players()`, `staff()`, `queue()`, `vehicles()`,
  `bans()`, `command()`, and log helpers.
- `bundle()` for a dashboard-ready server snapshot without remembering include
  flags.
- Frozen dataclass models with `.raw`, `.extra`, and `.to_dict()`.
- `raw=True` when you need exact PRC payloads.
- Dynamic rate limiting enabled by default.
- Explicit opt-in utilities that stay lazy until imported.

## Common Reads

```python
from erlc_api import Client

with Client.from_env() as api:
    server = api.server()
    dashboard = api.bundle()
    all_data = api.bundle("all")
    command_logs = api.logs("command")

    print(server.name)
    print(dashboard.players_list)
    print(command_logs[0].command if command_logs else "no commands")
```

`api.server()` stays lean. Use `api.bundle()` when you want player, staff,
queue, vehicle, and emergency-call data in one typed `ServerBundle`.

## Safe Commands

Command execution is explicit. For bot or web input, validate locally before
sending anything to PRC:

```python
from erlc_api import Client, CommandPolicy, cmd

policy = CommandPolicy(allowed={"h", "pm"}, max_length=120)

with Client.from_env() as api:
    preview = api.preview_command(cmd.h("Restart in 5 minutes"), policy=policy)
    if preview.allowed:
        result = api.command(preview.command, policy=policy)
        print(result.message)
```

`preview_command(...)` never sends HTTP. `command(..., policy=policy)` validates
before the request and raises `CommandPolicyError` if blocked.

## Optional Extras

Base installs only depend on `httpx`. Extras stay opt-in:

| Extra | Used by |
| --- | --- |
| `webhooks` | Event webhook Ed25519 signature verification |
| `export` | XLSX export helpers |
| `time` | Enhanced time parsing |
| `rich` | Rich terminal tables |
| `scheduling` | Advanced scheduling integrations around watchers |
| `location` | Optional map overlays |
| `utils` | Utility extras except webhooks |
| `all` | Everything optional |

Example:

```bash
pip install "erlc-api.py[webhooks,export]"
```

## Utilities Stay Explicit

The core import remains lightweight:

```python
from erlc_api import AsyncClient, Client, CommandPolicy, PermissionLevel, cmd
from erlc_api.vehicles import VehicleTools
from erlc_api.cache import AsyncCachedClient
from erlc_api.webhooks import assert_valid_event_webhook_signature
```

Advanced modules include caching, filters, finders, sorting, grouping, analytics,
export, waiters, watchers, moderation helpers, Discord payload helpers, command
flows, webhooks, vehicle tools, emergency-call tools, and multi-server reads.

## Documentation

Full documentation is at **https://fortune1243.github.io/erlc-api**.

Useful starting points:

- [How It Works](https://fortune1243.github.io/erlc-api/How-It-Works/) — mental model, sync vs async, rate limits
- [Endpoint Reference](https://fortune1243.github.io/erlc-api/Endpoint-Reference/) — every API method
- [Getting Started](https://fortune1243.github.io/erlc-api/Getting-Started/) — first calls, commands, multi-server
- [Migration to v3](https://fortune1243.github.io/erlc-api/Migration-to-v3/) — upgrade from v2

Runnable examples live in [`examples`](examples).

## Development

```bash
pip install -e .[dev]
python -m ruff check src tests scripts examples
$env:PYTHONPATH = "src"; python -m pytest -q
```

Before release work:

```bash
python -m build
python -m twine check dist/*
```

## Contributing

Bug reports and pull requests are welcome on the [GitHub repository](https://github.com/Fortune1243/erlc-api).
Before submitting, run `ruff check` and `pytest -q` locally.

## License

This project uses a custom attribution license. See [LICENSE](LICENSE) for details.
