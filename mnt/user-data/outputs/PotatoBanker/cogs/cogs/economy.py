"""
cogs/economy.py
===============
Core economy commands: balance, daily, work, beg.

All commands are hybrid (prefix + slash) and share internal logic
via utils/economy.py.  Every response is an embed.
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

import database as db
import economy_utils as eco
import embeds as emb

logger = logging.getLogger(__name__)


class Economy(commands.Cog, name="Economy"):
    """💰 Core economy: balance, daily, work, and beg."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── /balance ──────────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="balance",
        aliases=["bal", "wallet"],
        description="Check your potato balance.",
    )
    @app_commands.describe(member="Whose balance to check (default: yourself).")
    async def balance(
        self,
        ctx: commands.Context,
        member: discord.Member | None = None,
    ) -> None:
        """Show wallet, bank, and total potato count for yourself or another member."""
        target = member or ctx.author

        # Auto-apply interest silently before displaying balance
        await eco.maybe_apply_interest(target.id)

        user = await db.get_user(target.id)
        embed = emb.balance(target, user["wallet"], user["bank"])
        await ctx.reply(embed=embed, mention_author=False)

    # ── /daily ────────────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="daily",
        description="Claim your daily potato reward (24h cooldown).",
    )
    async def daily(self, ctx: commands.Context) -> None:
        """Claim 10–100 potatoes once every 24 hours. Streak bonuses apply!"""
        await eco.maybe_apply_interest(ctx.author.id)
        result = await eco.claim_daily(ctx.author.id)

        if not result["success"]:
            embed = emb.cooldown_embed("daily", result["remaining"])
        else:
            embed = emb.daily_reward(
                ctx.author,
                result["amount"],
                result["message"],
                result["streak"],
            )

        await ctx.reply(embed=embed, mention_author=False)

    # ── /work ─────────────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="work",
        description="Work for exactly 10 potatoes (1h cooldown).",
    )
    async def work(self, ctx: commands.Context) -> None:
        """Put in an honest day's work for 10 🥔."""
        await eco.maybe_apply_interest(ctx.author.id)
        result = await eco.do_work(ctx.author.id)

        if not result["success"]:
            embed = emb.cooldown_embed("work", result["remaining"])
        else:
            embed = emb.work_reward(ctx.author, result["amount"], result["message"])

        await ctx.reply(embed=embed, mention_author=False)

    # ── /beg ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="beg",
        description="Beg for potatoes — you might get nothing!",
    )
    async def beg(self, ctx: commands.Context) -> None:
        """Beg for 0–100 🥔. No shame in it... sort of."""
        await eco.maybe_apply_interest(ctx.author.id)
        result = await eco.do_beg(ctx.author.id)

        if not result["success"]:
            embed = emb.cooldown_embed("beg", result["remaining"])
        else:
            embed = emb.beg_result(ctx.author, result["amount"], result["message"])

        await ctx.reply(embed=embed, mention_author=False)

    # ── /give ─────────────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="give",
        aliases=["pay", "transfer"],
        description="Give potatoes from your wallet to another member.",
    )
    @app_commands.describe(
        member="The member to send potatoes to.",
        amount="How many potatoes to send.",
    )
    async def give(
        self,
        ctx: commands.Context,
        member: discord.Member,
        amount: int,
    ) -> None:
        """Transfer potatoes wallet-to-wallet."""
        # --- validation ---
        if member.bot:
            return await ctx.reply(
                embed=emb.error("Invalid Target", "You can't send potatoes to a bot!"),
                mention_author=False,
            )
        if member.id == ctx.author.id:
            return await ctx.reply(
                embed=emb.error("Invalid Target", "You can't send potatoes to yourself!"),
                mention_author=False,
            )
        if amount <= 0:
            return await ctx.reply(
                embed=emb.error("Invalid Amount", "You must send at least **1** 🥔."),
                mention_author=False,
            )

        sender = await db.get_user(ctx.author.id)
        if sender["wallet"] < amount:
            return await ctx.reply(
                embed=emb.error(
                    "Insufficient Funds",
                    f"You only have **{sender['wallet']:,}** 🥔 in your wallet.",
                ),
                mention_author=False,
            )

        success = await db.transfer_wallet(ctx.author.id, member.id, amount)
        if not success:
            return await ctx.reply(
                embed=emb.error("Transfer Failed", "Something went wrong. Please try again."),
                mention_author=False,
            )

        await ctx.reply(
            embed=emb.transfer_embed(ctx.author, member, amount),
            mention_author=False,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Economy(bot))
