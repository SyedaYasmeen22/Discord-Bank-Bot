"""
cogs/bank.py
============
Bank commands: deposit, withdraw, and a manual interest-claim command.

The 1% daily interest is also applied automatically by maybe_apply_interest()
called inside economy commands, but users can also run /interest to
claim it manually and see how much they earned.
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

import database as db
import economy_utils as eco
import embeds as emb
from constants import INTEREST_RATE, INTEREST_COOLDOWN_H

logger = logging.getLogger(__name__)


class Bank(commands.Cog, name="Bank"):
    """🏦 Deposit, withdraw, and earn daily interest."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── /deposit ──────────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="deposit",
        aliases=["dep"],
        description="Deposit potatoes from your wallet into the bank.",
    )
    @app_commands.describe(amount="Amount to deposit, or 'all' to deposit everything.")
    async def deposit(self, ctx: commands.Context, *, amount: str) -> None:
        """Move potatoes from wallet → bank. Use 'all' to deposit everything."""
        user = await db.get_user(ctx.author.id)

        # Resolve "all"
        if amount.lower() == "all":
            real_amount = user["wallet"]
        else:
            try:
                real_amount = int(amount)
            except ValueError:
                return await ctx.reply(
                    embed=emb.error("Invalid Amount", "Please enter a number or `all`."),
                    mention_author=False,
                )

        if real_amount <= 0:
            return await ctx.reply(
                embed=emb.error("Invalid Amount", "You must deposit at least **1** 🥔."),
                mention_author=False,
            )
        if real_amount > user["wallet"]:
            return await ctx.reply(
                embed=emb.error(
                    "Insufficient Funds",
                    f"You only have **{user['wallet']:,}** 🥔 in your wallet.",
                ),
                mention_author=False,
            )

        success = await db.deposit_to_bank(ctx.author.id, real_amount)
        if not success:
            return await ctx.reply(
                embed=emb.error("Deposit Failed", "Something went wrong. Please try again."),
                mention_author=False,
            )

        refreshed = await db.get_user(ctx.author.id)
        await ctx.reply(
            embed=emb.deposit_embed(ctx.author, real_amount, refreshed["bank"]),
            mention_author=False,
        )

    # ── /withdraw ─────────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="withdraw",
        aliases=["with"],
        description="Withdraw potatoes from your bank to your wallet.",
    )
    @app_commands.describe(amount="Amount to withdraw, or 'all' to withdraw everything.")
    async def withdraw(self, ctx: commands.Context, *, amount: str) -> None:
        """Move potatoes from bank → wallet. Use 'all' to withdraw everything."""
        user = await db.get_user(ctx.author.id)

        if amount.lower() == "all":
            real_amount = user["bank"]
        else:
            try:
                real_amount = int(amount)
            except ValueError:
                return await ctx.reply(
                    embed=emb.error("Invalid Amount", "Please enter a number or `all`."),
                    mention_author=False,
                )

        if real_amount <= 0:
            return await ctx.reply(
                embed=emb.error("Invalid Amount", "You must withdraw at least **1** 🥔."),
                mention_author=False,
            )
        if real_amount > user["bank"]:
            return await ctx.reply(
                embed=emb.error(
                    "Insufficient Funds",
                    f"You only have **{user['bank']:,}** 🥔 in your bank.",
                ),
                mention_author=False,
            )

        success = await db.withdraw_from_bank(ctx.author.id, real_amount)
        if not success:
            return await ctx.reply(
                embed=emb.error("Withdrawal Failed", "Something went wrong. Please try again."),
                mention_author=False,
            )

        refreshed = await db.get_user(ctx.author.id)
        await ctx.reply(
            embed=emb.withdraw_embed(ctx.author, real_amount, refreshed["wallet"]),
            mention_author=False,
        )

    # ── /interest ─────────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="interest",
        description=f"Claim your {int(INTEREST_RATE * 100)}% daily bank interest.",
    )
    async def interest(self, ctx: commands.Context) -> None:
        """Manually claim your 1% daily interest on your bank balance."""
        import time

        user = await db.get_user(ctx.author.id)
        now  = time.time()
        last = user["last_interest_claim"]
        remaining = (INTEREST_COOLDOWN_H * 3600) - (now - last)

        if remaining > 0:
            return await ctx.reply(
                embed=emb.cooldown_embed("interest", remaining),
                mention_author=False,
            )

        if user["bank"] == 0:
            return await ctx.reply(
                embed=emb.warning(
                    "No Bank Balance",
                    "You need potatoes in your bank to earn interest!",
                ),
                mention_author=False,
            )

        earned = await db.apply_interest(ctx.author.id, INTEREST_RATE, now)
        if earned == 0:
            return await ctx.reply(
                embed=emb.warning(
                    "Nothing to Claim",
                    "Your bank balance is too small to earn any interest right now.",
                ),
                mention_author=False,
            )

        refreshed = await db.get_user(ctx.author.id)
        await ctx.reply(
            embed=emb.interest_embed(ctx.author, earned, refreshed["bank"]),
            mention_author=False,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bank(bot))
