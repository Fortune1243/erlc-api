from __future__ import annotations

import logging
import os

import discord
from discord.ext import commands

from erlc_api import AsyncClient, CommandPolicy, CommandPolicyError, ERLCError, RateLimitError, cmd
from erlc_api.security import key_fingerprint


logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True


class ERLCBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)
        self.api = AsyncClient.from_env()
        self.announce_policy = CommandPolicy(allowed={"h"}, max_length=120)
        logger.info("Configured ERLC key %s", key_fingerprint(self.api.server_key or ""))

    async def setup_hook(self) -> None:
        await self.api.start()

    async def close(self) -> None:
        await self.api.close()
        await super().close()


bot = ERLCBot()


@bot.command()
async def status(ctx: commands.Context) -> None:
    try:
        bundle = await bot.api.bundle()
    except RateLimitError as exc:
        retry_after = exc.retry_after_s or 0
        await ctx.reply(f"Rate limited. Try again in {retry_after:.0f}s.", mention_author=False)
        return
    except ERLCError:
        await ctx.reply("ER:LC API request failed.", mention_author=False)
        return

    await ctx.send(
        f"**{bundle.name or 'Server'}** - "
        f"{bundle.current_players}/{bundle.max_players} players, "
        f"{len(bundle.queue_list)} queued"
    )


@bot.command()
async def players(ctx: commands.Context) -> None:
    online = await bot.api.players()
    if not online:
        await ctx.send("No players online.")
        return

    names = [player.name or str(player.user_id) for player in online[:15]]
    suffix = f" (+{len(online) - 15} more)" if len(online) > 15 else ""
    await ctx.send(", ".join(names) + suffix)


@bot.command()
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
@commands.cooldown(1, 30, commands.BucketType.guild)
async def announce(ctx: commands.Context, *, message: str) -> None:
    try:
        preview = await bot.api.preview_command(cmd.h(message), policy=bot.announce_policy)
        if not preview.allowed:
            await ctx.reply(preview.reason or "That command is not allowed.", mention_author=False)
            return
        result = await bot.api.command(preview.command, policy=bot.announce_policy)
    except CommandPolicyError as exc:
        await ctx.reply(exc.result.reason or "That command is not allowed.", mention_author=False)
        return

    logger.info("Discord announce by %s: %s", ctx.author.id, preview.command)
    await ctx.send(result.message or "Announcement sent.")


@announce.error
async def announce_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("You need Manage Server permission to use this.", mention_author=False)
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"Slow down. Try again in {error.retry_after:.0f}s.", mention_author=False)
    else:
        raise error


bot.run(os.environ["DISCORD_TOKEN"])
