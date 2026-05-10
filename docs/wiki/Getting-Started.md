# Getting Started

This page gets a new project from install to the first successful API call. It
uses the v3 simple path: `Client`/`AsyncClient`, `from_env()`, typed models by
default, `bundle()` for dashboard data, and `CommandPolicy` for user-triggered
commands.

## Install

```bash
pip install erlc-api.py
```

Import the Python package with an underscore:

```python
from erlc_api import AsyncClient, Client
```

Set your server key in the environment:

```powershell
$env:ERLC_SERVER_KEY = "server-key"
```

## First Sync Request

Use `Client` in scripts, cron jobs, one-off admin tools, and CLIs.

```python
from erlc_api import Client


with Client.from_env() as client:
    players = client.players()
    for player in players:
        print(player.name, player.user_id, player.team)
```

Return type: `list[Player]`.

## First Async Request

Use `AsyncClient` in Discord bots, FastAPI apps, workers, and code already
running an event loop.

```python
from erlc_api import AsyncClient


async with AsyncClient.from_env() as client:
    server = await client.server()
    print(server.name, server.current_players, server.max_players)
```

## Fetch A Dashboard Bundle

Use `bundle()` when you want common dashboard data without remembering include
flags:

```python
bundle = await api.bundle()

print(bundle.name)
print(len(bundle.players_list))
print(len(bundle.queue_list))
print(len(bundle.staff_members))
```

Use `bundle("all")` when you want every supported v2 section.

## Fetch Logs

```python
command_logs = await api.logs("command")
all_logs = await api.logs("all")

print(command_logs[0].command if command_logs else "none")
print(len(all_logs.mod_calls))
```

## Send A Safe Command

Commands can be plain strings or built with `cmd`. For bot or web input, put a
local policy in front of execution:

```python
from erlc_api import CommandPolicy, cmd

policy = CommandPolicy(allowed={"h", "pm"}, max_length=120)

preview = await api.preview_command(cmd.h("Hello"), policy=policy)
if preview.allowed:
    await api.command(preview.command, policy=policy)
```

`preview_command(...)` never sends HTTP. `command(..., policy=policy)` validates
before sending the request.

## Multi-server Use

Create one client with no default key and pass keys per request, or use a
default key and override individual calls:

```python
client = AsyncClient.from_env()

primary = await client.players()
secondary = await client.players(server_key="secondary-server-key")
```

Use `global_key=` or `ERLC_GLOBAL_KEY` only when PRC gives your application an
Authorization key for large-app flows.

## Common Mistakes

- Installing `erlc_api`; the PyPI package name is `erlc-api.py`.
- Importing `erlc-api.py`; the Python import name is `erlc_api`.
- Forgetting to close clients outside context managers.
- Calling `api.command(...)` with raw user input instead of a policy-checked command.
- Expecting utility modules from top-level `erlc_api`; import utilities
  explicitly, such as `from erlc_api.vehicles import VehicleTools`.

## Related Pages

- [Earlier in the guide: Testing and Mocking](./Testing-and-Mocking.md)
- [Next in the guide: Quickstart: Web Backend](./Quickstart-Web-Backend.md)

---

[Previous Page: Testing and Mocking](./Testing-and-Mocking.md) | [Next Page: Quickstart: Web Backend](./Quickstart-Web-Backend.md)
