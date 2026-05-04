# Quickstart: Discord.py

This guide walks you through building a basic Discord bot that talks to a live ERLC server. By the end you will have four working prefix commands: `!status`, `!players`, `!staff`, and `!announce`.

## 1. Prerequisites

- Install both packages:
  ```
  pip install erlc-api.py discord.py
  ```
- A PRC server key — see [Clients and Authentication](./Clients-and-Authentication.md) for how to obtain one.

## 2. Client lifecycle

`AsyncERLC` must be started before commands run and closed when the bot shuts down. The right place for this in discord.py v2 is `setup_hook` (runs once before the bot connects) and an overridden `close`.

```python
import discord
from discord.ext import commands
from erlc_api import AsyncERLC, cmd
from erlc_api.cache import AsyncCachedClient

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
api = AsyncERLC("your-server-key", rate_limited=True)
cached_api = AsyncCachedClient(api, ttl_s=5)


async def setup_hook():
    await api.start()

bot.setup_hook = setup_hook


async def on_close():
    await api.close()

bot.close = on_close
```

## 3. Commands

### `!status` — server overview

```python
@bot.command()
async def status(ctx):
    info = await cached_api.server()
    await ctx.send(f"**{info.name}** — {info.current_players}/{info.max_players} players online")
```

### `!players` — list online players

```python
@bot.command()
async def players(ctx):
    online = await cached_api.players()
    if not online:
        await ctx.send("No players online.")
        return
    names = [p.name for p in online[:15]]
    suffix = f" (+{len(online) - 15} more)" if len(online) > 15 else ""
    await ctx.send(", ".join(names) + suffix)
```

### `!staff` — who is on duty

```python
@bot.command()
async def staff(ctx):
    duty = (await cached_api.staff()).members
    if not duty:
        await ctx.send("No staff on duty.")
        return
    lines = [f"**{m.role}** {m.name}" for m in duty]
    await ctx.send("\n".join(lines))
```

### `!announce <message>` — broadcast a hint

```python
@bot.command()
async def announce(ctx, *, message: str):
    result = await api.command(cmd.h(message))
    await ctx.send(result.message or "Announcement sent.")
```

## 4. Error handling

Wrap calls in try/except to give users readable feedback instead of a traceback.

```python
from erlc_api import AuthError, RateLimitError, ERLCError
from erlc_api.diagnostics import diagnose_error
from erlc_api.discord_tools import DiscordFormatter

@bot.command()
async def status(ctx):
    try:
        info = await cached_api.server()
        await ctx.send(f"**{info.name}** — {info.current_players}/{info.max_players} players online")
    except AuthError:
        await ctx.send("Invalid server key. Check your configuration.")
    except RateLimitError as e:
        retry_after = e.retry_after_s or 0
        await ctx.send(f"Rate limited. Try again in {retry_after:.0f}s.")
    except ERLCError as e:
        diagnostics = diagnose_error(e)
        await ctx.send(**DiscordFormatter().diagnostics(diagnostics).to_dict())
```

## 5. Running the bot

```python
bot.run("your-discord-bot-token")
```

## 6. Optional Discord Payload Helpers

`erlc_api.discord_tools` does not replace `discord.py`; it builds plain dict
payloads that most Discord libraries can send.

```python
from erlc_api.discord_tools import DiscordFormatter
from erlc_api.status import StatusBuilder

@bot.command()
async def richstatus(ctx):
    bundle = await cached_api.server(players=True, staff=True, queue=True, vehicles=True, emergency_calls=True)
    status = StatusBuilder(bundle).build()
    await ctx.send(**DiscordFormatter().server_status(status).to_dict())
```

## 7. Multi-server status

For bots serving more than one ER:LC server, keep server keys named and collect
per-server errors instead of failing the whole command.

```python
from erlc_api.multiserver import AsyncMultiServer, ServerRef

servers = [
    ServerRef("main", "main-server-key"),
    ServerRef("training", "training-server-key"),
]

@bot.command()
async def servers(ctx):
    manager = AsyncMultiServer(cached_api, servers, concurrency=3)
    summary = await manager.aggregate()
    await ctx.send(
        f"{summary['ok']}/{summary['servers']} servers online-ish, "
        f"{summary['players']} total players, {summary['queue']} queued"
    )
```

## 8. Command-flow previews

Use command flows when a bot command should show or log the exact command
sequence before a moderator confirms it.

```python
from erlc_api.command_flows import CommandFlowBuilder, CommandTemplate

warn_template = CommandTemplate("warn", "warn {target} {reason}")

@bot.command()
async def previewwarn(ctx, target: str, *, reason: str):
    flow = (
        CommandFlowBuilder("warn-preview")
        .template(warn_template, target=target, reason=reason)
        .step(f"pm {target} Please review the rules")
        .build()
    )
    await ctx.send("\n".join(flow.preview()))
```

## 9. Common mistakes

- **Starting the client in `on_ready` instead of `setup_hook`.** `on_ready` fires on every reconnect, so `api.start()` would be called multiple times. `setup_hook` runs exactly once.
- **Using `ERLC` (sync) instead of `AsyncERLC`.** Calling a synchronous client inside an async bot blocks the event loop.
- **Not handling `RateLimitError`.** ERLC enforces per-endpoint rate limits. Unhandled, this raises an exception and silently drops your response.
- **Missing `intents.message_content = True`.** Without this intent the bot never sees message text and prefix commands will not fire.
- **Calling `await api.players()` before `setup_hook` completes.** The client raises if you call endpoints before `start()` has run.
- **Caching commands.** `AsyncCachedClient` caches read endpoints only; always call `api.command(...)` directly.
- **Using multi-server helpers to broadcast commands.** They intentionally support read-only methods.

## 10. Next steps

- [Endpoint Reference](./Endpoint-Reference.md) — full list of available endpoints (`kill_logs`, `bans`, `vehicles`, etc.)
- [Commands Reference](./Commands-Reference.md) — all supported in-game commands via `cmd.*`
- [Workflow Utilities Reference](./Workflow-Utilities-Reference.md) — status snapshots, Discord payloads, cache, rules, and multi-server helpers
- [Errors and Rate Limits](./Errors-and-Rate-Limits.md) — detailed error types and retry behaviour
- [Waiters and Watchers](./Waiters-and-Watchers.md) — poll for changes and build live-update features

## Related Pages

- [Earlier in the guide: Quickstart: Web Backend](./Quickstart-Web-Backend.md)
- [Next in the guide: FAQ](./FAQ.md)

---

[Previous Page: Quickstart: Web Backend](./Quickstart-Web-Backend.md) | [Next Page: FAQ](./FAQ.md)
