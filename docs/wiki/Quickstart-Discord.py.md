# Quickstart (discord.py)

This wrapper is optimized for Discord bot workloads where reliability and low glue code matter.

## Install dependencies

```bash
pip install discord.py
pip install git+https://github.com/Fortune1243/erlc-api.git
```

## Minimal discord.py integration

```python
import discord
from discord.ext import commands
from erlc_api import ERLCClient


bot = commands.Bot(command_prefix="!")
api = ERLCClient()

# Example key mapping; replace with your storage layer.
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
```

## Push join/leave events without background worker ownership

```python
import asyncio
from erlc_api.discord import iter_player_events


async def watch_players(channel: discord.TextChannel, server_key: str) -> None:
    erlc_ctx = api.ctx(server_key)
    async for event in iter_player_events(api, erlc_ctx, interval_s=5.0):
        player_name = event.player.name or "Unknown"
        await channel.send(f"{type(event).__name__}: {player_name}")


# Launch from your startup path:
# asyncio.create_task(watch_players(channel, "your-server-key"))
```

## Why this works well for bots

- One shared client can serve many guilds cleanly.
- Rate-limit state is isolated per server key and endpoint bucket.
- Non-idempotent commands are not auto-replayed, preventing accidental duplicate actions.

## Next Steps

- Add web/backend endpoints in [Quickstart-Web-Backend.md](./Quickstart-Web-Backend.md)
- Harden failure handling with [Error-Handling-and-Troubleshooting.md](./Error-Handling-and-Troubleshooting.md)
