# Quickstart: Discord.py

```python
from discord.ext import commands
from erlc_api import AsyncERLC, cmd

bot = commands.Bot(command_prefix="!")
api = AsyncERLC("server-key")


@bot.event
async def on_ready():
    await api.start()


@bot.command()
async def players(ctx):
    current = await api.players()
    await ctx.send(f"{len(current)} players online")


@bot.command()
async def announce(ctx, *, message: str):
    result = await api.command(cmd.h(message))
    await ctx.send(result.message or "sent")
```

