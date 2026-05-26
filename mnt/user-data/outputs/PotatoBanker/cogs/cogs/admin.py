"""
cogs/admin.py
=============
Administrator-only commands for managing user balances.

Commands:
  /add  <member> <amount>  — Add potatoes to a user's wallet.
  /take <member> <amount>  — Remove potatoes from a user's wallet.

Both commands require the caller to have the Administrator permission
(enforced via utils/checks.is_admin).
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

import database as db
import embeds as emb
from checks import is_admin

logger = logging.getLogger(__name__)


class Admin(commands.Cog, name="Admin"):
    """🛠️ Admin-only balance management commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── /add ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="add",
        description="[Admin] Add potatoes to a member's wallet.",
        default_member_permissions=discord.Permissions(administrator=True),
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        member="The member to give potatoes to.",
        amount="How many potatoes to add (must be positive).",
    )
    @is_admin()
    async def add(
        self,
        ctx: commands.Context,
        member: discord.Member,
        amount: int,
    ) -> None:
        """Add potatoes to any member's wallet (no upper limit)."""
        if amount <= 0:
            return await ctx.reply(
                embed=emb.error("Invalid Amount", "Amount must be greater than 0."),
                ephemeral=True,
                mention_author=False,
            )
        if member.bot:
            return await ctx.reply(
                embed=emb.error("Invalid Target", "You can't add potatoes to a bot."),
                ephemeral=True,
                mention_author=False,
            )

        success = await db.add_to_wallet(member.id, amount)
        if not success:
            return await ctx.reply(
                embed=emb.error("Database Error", "Failed to update balance. Please try again."),
                ephemeral=True,
                mention_author=False,
            )

        logger.info("Admin %s added %d to %s (%d)", ctx.author, amount, member, member.id)
        await ctx.reply(
            embed=emb.admin_add(ctx.author, member, amount),
            mention_author=False,
        )

    # ── /take ─────────────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="take",
        description="[Admin] Remove potatoes from a member's wallet.",
        default_member_permissions=discord.Permissions(administrator=True),
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        member="The member to take potatoes from.",
        amount="How many potatoes to remove (cannot reduce below 0).",
    )
    @is_admin()
    async def take(
        self,
        ctx: commands.Context,
        member: discord.Member,
        amount: int,
    ) -> None:
        """Remove potatoes from a member's wallet (minimum 0)."""
        if amount <= 0:
            return await ctx.reply(
                embed=emb.error("Invalid Amount", "Amount must be greater than 0."),
                ephemeral=True,
                mention_author=False,
            )
        if member.bot:
            return await ctx.reply(
                embed=emb.error("Invalid Target", "You can't take potatoes from a bot."),
                ephemeral=True,
                mention_author=False,
            )

        success = await db.remove_from_wallet(member.id, amount)
        if not success:
            user = await db.get_user(member.id)
            wallet = user["wallet"] if user else 0
            return await ctx.reply(
                embed=emb.error(
                    "Insufficient Funds",
                    f"{member.mention} only has **{wallet:,}** 🥔 in their wallet.",
                ),
                ephemeral=True,
                mention_author=False,
            )

        logger.info("Admin %s removed %d from %s (%d)", ctx.author, amount, member, member.id)
        await ctx.reply(
            embed=emb.admin_take(ctx.author, member, amount),
            mention_author=False,
        )

    # ── Error handler (permission denied) ─────────────────────────────────────

    @add.error
    @take.error
    async def admin_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.reply(
                embed=emb.error(
                    "Permission Denied",
                    "You need the **Administrator** permission to use this command.",
                ),
                ephemeral=True,
                mention_author=False,
            )
        else:
            logger.error("Admin command error: %s", error)
            await ctx.reply(
                embed=emb.error("Unexpected Error", str(error)),
                ephemeral=True,
                mention_author=False,
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot))
