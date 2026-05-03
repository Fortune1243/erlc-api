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

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
api = AsyncERLC("your-server-key")


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
    info = await api.server()
    await ctx.send(f"**{info.name}** — {info.current_players}/{info.max_players} players online")
```

### `!players` — list online players

```python
@bot.command()
async def players(ctx):
    online = await api.players()
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
    duty = (await api.staff()).members()
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

@bot.command()
async def status(ctx):
    try:
        info = await api.server()
        await ctx.send(f"**{info.name}** — {info.current_players}/{info.max_players} players online")
    except AuthError:
        await ctx.send("Invalid server key. Check your configuration.")
    except RateLimitError as e:
        await ctx.send(f"Rate limited. Try again in {e.retry_after:.0f}s.")
    except ERLCError as e:
        await ctx.send(f"API error: {e}")
```

## 5. Running the bot

```python
bot.run("your-discord-bot-token")
```

## 6. Common mistakes

- **Starting the client in `on_ready` instead of `setup_hook`.** `on_ready` fires on every reconnect, so `api.start()` would be called multiple times. `setup_hook` runs exactly once.
- **Using `ERLC` (sync) instead of `AsyncERLC`.** Calling a synchronous client inside an async bot blocks the event loop.
- **Not handling `RateLimitError`.** ERLC enforces per-endpoint rate limits. Unhandled, this raises an exception and silently drops your response.
- **Missing `intents.message_content = True`.** Without this intent the bot never sees message text and prefix commands will not fire.
- **Calling `await api.players()` before `setup_hook` completes.** The client raises if you call endpoints before `start()` has run.

## 7. Next steps

- [Endpoint Reference](./Endpoint-Reference.md) — full list of available endpoints (`kill_logs`, `bans`, `vehicles`, etc.)
- [Commands Reference](./Commands-Reference.md) — all supported in-game commands via `cmd.*`
- [Errors and Rate Limits](./Errors-and-Rate-Limits.md) — detailed error types and retry behaviour
- [Waiters and Watchers](./Waiters-and-Watchers.md) — poll for changes and build live-update features

---

← [Error Handling and Troubleshooting](./Error-Handling-and-Troubleshooting.md) | [Quickstart: Web Backend](./Quickstart-Web-Backend.md) →
