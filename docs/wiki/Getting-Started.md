# Getting Started

This page gets a new project from install to the first successful API call. It
uses the public v2 surface: `AsyncERLC`, `ERLC`, flat endpoint methods, typed
dataclasses by default, and `raw=True` only when exact PRC JSON is needed.

## Install

Install the PyPI package:

```bash
pip install erlc-api.py
```

Import the Python package with an underscore:

```python
from erlc_api import AsyncERLC, ERLC
```

For webhook signature verification, install the optional webhook extra:

```bash
pip install "erlc-api.py[webhooks]"
```

## First Async Request

Use `AsyncERLC` in bots, web apps, workers, and any code already running an
event loop.

```python
from erlc_api import AsyncERLC


async with AsyncERLC("server-key") as api:
    players = await api.players()
    for player in players:
        print(player.name, player.user_id, player.team)
```

Return type: `list[Player]`.

Important options:

- `raw=True` returns PRC JSON instead of models.
- `server_key=` overrides the default key for one request.
- `retry_429=False` disables the one safe 429 retry.

## First Sync Request

Use `ERLC` in scripts, cron jobs, one-off admin tools, and CLIs.

```python
from erlc_api import ERLC


with ERLC("server-key") as api:
    server = api.server()
    print(server.name, server.current_players, server.max_players)
```

Return type: `ServerBundle` when using `server()`.

## Fetch A Dashboard Snapshot

`server()` accepts include flags for v2 sections:

```python
bundle = await api.server(players=True, queue=True, staff=True)

print(bundle.name)
print(len(bundle.players or []))
print(len(bundle.queue or []))
print(bundle.staff.members() if bundle.staff else [])
```

Use `all=True` when you want every v2 section the wrapper supports:

```python
bundle = await api.server(all=True)
```

## Multi-server Use

Create one client with a default key and override per call:

```python
api = AsyncERLC("primary-server-key")

primary_players = await api.players()
secondary_players = await api.players(server_key="secondary-server-key")
```

Use `global_key=` only when PRC gives your application an Authorization key for
large-app flows.

## Send A Command

Commands can be plain strings or built with `cmd`:

```python
from erlc_api import cmd

await api.command("h Hello")
await api.command(":h Hello")
await api.command(cmd.pm("Player", "hello"))
```

The wrapper normalizes missing leading colons and validates only essentials:
non-empty command, no newline, and a command name.

## Common Mistakes

- Installing `erlc_api`; the PyPI package name is `erlc-api.py`.
- Importing `erlc-api.py`; the Python import name is `erlc_api`.
- Forgetting to close clients outside context managers.
- Expecting utility modules from top-level `erlc_api`; import utilities
  explicitly, such as `from erlc_api.find import Finder`.

## Related Pages

- [Installation and Extras](./Installation-and-Extras.md)
- [Clients and Authentication](./Clients-and-Authentication.md)
- [Endpoint Reference](./Endpoint-Reference.md)

---

[Previous Page: Installation and Extras](./Installation-and-Extras.md) | [Next Page: Quickstart: Web Backend](./Quickstart-Web-Backend.md)
