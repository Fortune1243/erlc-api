# Quickstart: Discord.py

This guide walks you through building a basic Discord bot that talks to a live ERLC server. By the end you will have four working prefix commands: `!status`, `!players`, `!staff`, and `!announce`.

## 1. Prerequisites

- Install both packages:
  ```
  pip install erlc-api.py discord.py
  ```
- A PRC server key — see [Clients and Authentication](./Clients-and-Authentication.md) for how to obtain one.

## 2. Client lifecycle

`AsyncClient` must be started before commands run and closed when the bot shuts down. The right place for this in discord.py v2 is `setup_hook` (runs once before the bot connects) and an overridden `close`.

```python
import logging
import os

import discord
from discord.ext import commands
from erlc_api import AsyncClient, CommandPolicy, CommandPolicyError, cmd
from erlc_api.cache import AsyncCachedClient
from erlc_api.security import key_fingerprint

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

class ERLCBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)
        self.api = AsyncClient.from_env()
        self.cached_api = AsyncCachedClient(self.api, ttl_s=5)
        self.announce_policy = CommandPolicy(allowed={"h"}, max_length=120)
        logger.info("Configured ERLC key %s", key_fingerprint(self.api.server_key or ""))

    async def setup_hook(self) -> None:
        await self.api.start()

    async def close(self) -> None:
        await self.api.close()
        await super().close()


bot = ERLCBot()
```

## 3. Commands

### `!status` — server overview

```python
@bot.command()
async def status(ctx):
    info = await bot.cached_api.server()
    await ctx.send(f"**{info.name}** — {info.current_players}/{info.max_players} players online")
```

### `!players` — list online players

```python
@bot.command()
async def players(ctx):
    online = await bot.cached_api.players()
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
    duty = (await bot.cached_api.staff()).members
    if not duty:
        await ctx.send("No staff on duty.")
        return
    lines = [f"**{m.role}** {m.name}" for m in duty]
    await ctx.send("\n".join(lines))
```

### `!announce <message>` — broadcast a hint

```python
@bot.command()
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
@commands.cooldown(1, 30, commands.BucketType.guild)
async def announce(ctx, *, message: str):
    try:
        safe_command = bot.announce_policy.validate(cmd.h(message))
    except CommandPolicyError as exc:
        await ctx.reply(exc.result.reason or "That command is not allowed.", mention_author=False)
        return

    preview = await bot.api.preview_command(safe_command, policy=bot.announce_policy)
    if not preview.allowed:
        await ctx.reply(preview.reason or "That command is not allowed.", mention_author=False)
        return
    logger.info("Discord announce by %s: %s", ctx.author.id, preview.command)
    result = await bot.api.command(preview.command, policy=bot.announce_policy)
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
        info = await bot.cached_api.server()
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

Add a local error handler for permission/cooldown failures:

```python
@announce.error
async def announce_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("You need Manage Server permission to use this.", mention_author=False)
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"Slow down. Try again in {error.retry_after:.0f}s.", mention_author=False)
    else:
        raise error
```

## 5. Running the bot

```python
bot.run(os.environ["DISCORD_TOKEN"])
```

## 6. Optional Discord Payload Helpers

`erlc_api.discord_tools` does not replace `discord.py`; it builds plain dict
payloads that most Discord libraries can send.

```python
from erlc_api.discord_tools import DiscordFormatter
from erlc_api.status import StatusBuilder

@bot.command()
async def richstatus(ctx):
    bundle = await bot.cached_api.server(players=True, staff=True, queue=True, vehicles=True, emergency_calls=True)
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
    manager = AsyncMultiServer(bot.cached_api, servers, concurrency=3)
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
- **Using `Client` (sync) instead of `AsyncClient`.** Calling a synchronous client inside an async bot blocks the event loop.
- **Not handling `RateLimitError`.** ERLC enforces per-endpoint rate limits. Unhandled, this raises an exception and silently drops your response.
- **Missing `intents.message_content = True`.** Without this intent the bot never sees message text and prefix commands will not fire.
- **Calling `await api.players()` before `setup_hook` completes.** The client raises if you call endpoints before `start()` has run.
- **Caching commands.** `AsyncCachedClient` caches read endpoints only; always call `api.command(...)` directly.
- **Using multi-server helpers to broadcast commands.** They intentionally support read-only methods.
- **Showing raw keys in logs or error messages.** Use `key_fingerprint(...)`
  when you need diagnostics.
- **Letting every guild member execute commands.** Use Discord permissions,
  cooldowns, and `CommandPolicy` before calling `bot.api.command(...)`.

## 10. Next steps

- [Endpoint Reference](./Endpoint-Reference.md) — full list of available endpoints (`kill_logs`, `bans`, `vehicles`, etc.)
- [Commands Reference](./Commands-Reference.md) — all supported in-game commands via `cmd.*`
- [Workflow Utilities Reference](./Workflow-Utilities-Reference.md) — status snapshots, Discord payloads, cache, rules, and multi-server helpers
- [Errors and Rate Limits](./Errors-and-Rate-Limits.md) — detailed error types and retry behaviour
- [Waiters and Watchers](./Waiters-and-Watchers.md) — poll for changes and build live-update features

## Related Pages

- [Earlier in the guide: Quickstart: Web Backend](./Quickstart-Web-Backend.md)
- [Next in the guide: Endpoint Usage Cookbook](./Endpoint-Usage-Cookbook.md)

---

[Previous Page: Quickstart: Web Backend](./Quickstart-Web-Backend.md) | [Next Page: Endpoint Usage Cookbook](./Endpoint-Usage-Cookbook.md)
