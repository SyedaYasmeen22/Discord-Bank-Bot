"""
cogs/events.py
==============
Global event listeners for Potato Banker.

Handles:
- on_ready        — log startup info
- on_command_error — centralised error handling for prefix commands
- on_app_command_error — centralised error handling for slash commands
- on_guild_join   — greet new servers
"""

import logging
import traceback

import discord
from discord import app_commands
from discord.ext import commands

import embeds as emb

logger = logging.getLogger(__name__)


class Events(commands.Cog, name="Events"):
    """⚡ Global bot event listeners."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        # Register the app_command error handler on the tree
        bot.tree.on_error = self.on_app_command_error  # type: ignore[assignment]

    # ── Ready ─────────────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        logger.info("Logged in as %s (ID: %s)", self.bot.user, self.bot.user.id)
        logger.info("Serving %d guilds", len(self.bot.guilds))
        await self.bot.change_presence(
            activity=discord.Game(name="Managing Potatoes 🥔")
        )

    # ── Prefix-command errors ─────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        # Errors that were already handled inside the cog
        if hasattr(ctx.command, "on_error"):
            return
        if ctx.cog and commands.Cog._get_overridden_hook(ctx.cog.cog_command_error):
            return

        error = getattr(error, "original", error)

        if isinstance(error, commands.CommandNotFound):
            return  # silently ignore unknown commands

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(
                embed=emb.error(
                    "Missing Argument",
                    f"You forgot to provide: **{error.param.name}**.\n"
                    f"Use `{ctx.prefix}help {ctx.command}` for usage.",
                ),
                mention_author=False,
            )

        elif isinstance(error, commands.BadArgument):
            await ctx.reply(
                embed=emb.error("Bad Argument", str(error)),
                mention_author=False,
            )

        elif isinstance(error, commands.CheckFailure):
            await ctx.reply(
                embed=emb.error(
                    "Permission Denied",
                    "You don't have permission to use this command.",
                ),
                mention_author=False,
            )

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(
                embed=emb.cooldown_embed(
                    ctx.command.qualified_name,
                    error.retry_after,
                ),
                mention_author=False,
            )

        elif isinstance(error, commands.MemberNotFound):
            await ctx.reply(
                embed=emb.error("Member Not Found", f"Could not find member: `{error.argument}`"),
                mention_author=False,
            )

        else:
            logger.error(
                "Unhandled error in command %s: %s\n%s",
                ctx.command,
                error,
                "".join(traceback.format_exception(type(error), error, error.__traceback__)),
            )
            await ctx.reply(
                embed=emb.error("Unexpected Error", "An unexpected error occurred. Please try again."),
                mention_author=False,
            )

    # ── Slash-command errors ──────────────────────────────────────────────────

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        error = getattr(error, "original", error)

        embed: discord.Embed

        if isinstance(error, app_commands.MissingPermissions):
            embed = emb.error(
                "Permission Denied",
                "You don't have the required permissions for this command.",
            )
        elif isinstance(error, app_commands.CommandOnCooldown):
            embed = emb.cooldown_embed(
                interaction.command.qualified_name if interaction.command else "command",
                error.retry_after,
            )
        elif isinstance(error, app_commands.CheckFailure):
            embed = emb.error("Permission Denied", "You can't use this command here.")
        else:
            logger.error(
                "Unhandled slash error: %s\n%s",
                error,
                "".join(traceback.format_exception(type(error), error, error.__traceback__)),
            )
            embed = emb.error("Unexpected Error", "An unexpected error occurred.")

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Guild join ────────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        logger.info("Joined guild: %s (ID: %s)", guild.name, guild.id)
        # Try to find a suitable channel and send a greeting
        channel = (
            guild.system_channel
            or next(
                (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages),
                None,
            )
        )
        if channel:
            embed = discord.Embed(
                title="🥔  Potato Banker has arrived!",
                description=(
                    "Thanks for adding me! I'll keep your potatoes safe.\n\n"
                    "Use `/balance` or `pot balance` to get started.\n"
                    "Run `/daily` to claim your first free potatoes!\n\n"
                    "Type `/help` or `pot help` to see all commands."
                ),
                colour=0xF4A460,
            )
            embed.set_thumbnail(
                url="https://em-content.zobj.net/source/twitter/376/potato_1f954.png"
            )
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Events(bot))
