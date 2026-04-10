# Quickstart (discord.py)

Use this pattern for production bot workflows with multiple guilds/servers.

## Install

```bash
pip install discord.py
pip install git+https://github.com/Fortune1243/erlc-api.git
```

## Minimal integration

```python
import discord
from discord.ext import commands
from erlc_api import CommandBuilder, ERLCClient


bot = commands.Bot(command_prefix="!")
api = ERLCClient()

# Replace with persistent storage.
guild_server_keys = {
    123456789012345678: "server-key-a",
}


@bot.event
async def on_ready() -> None:
    await api.start()


@bot.command(name="players")
async def players_cmd(ctx: commands.Context) -> None:
    server_key = guild_server_keys.get(ctx.guild.id if ctx.guild else 0)
    if not server_key:
        await ctx.send("No server key configured for this guild.")
        return

    erlc_ctx = api.ctx(server_key)
    players = await api.v1.players_typed(erlc_ctx)
    names = [p.name for p in players if p.name]
    await ctx.send(f"Online players ({len(names)}): " + ", ".join(names[:20]))


@bot.command(name="pm")
async def pm_cmd(ctx: commands.Context, target: str, *, message: str) -> None:
    server_key = guild_server_keys.get(ctx.guild.id if ctx.guild else 0)
    if not server_key:
        await ctx.send("No server key configured for this guild.")
        return

    erlc_ctx = api.ctx(server_key)
    result = await api.v1.command_with_tracking(
        erlc_ctx,
        CommandBuilder.pm(target=target, message=message),
        timeout_s=8.0,
    )
    await ctx.send(
        f"sent={result.inferred_success} confirmed={result.correlated_log_entry is not None} timeout={result.timed_out_waiting_for_log}"
    )
```

## Live event tracking

```python
import asyncio


async def watch(channel: discord.TextChannel, server_key: str) -> None:
    erlc_ctx = api.ctx(server_key)
    async with api.track_server(erlc_ctx, interval_s=2.0) as tracker:
        tracker.on("player_join", lambda p: channel.send(f"joined: {p.name}"))
        tracker.on("player_leave", lambda p: channel.send(f"left: {p.name}"))
        await asyncio.sleep(3600)
```

## Notes

- Non-idempotent command requests are not auto-replayed.
- Use one shared `ERLCClient` for all guilds in a process.
- Use cache/replay helpers for operational debugging.
