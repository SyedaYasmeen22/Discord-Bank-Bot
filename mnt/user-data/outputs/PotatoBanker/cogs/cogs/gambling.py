"""
cogs/gambling.py
================
Gambling commands: coinflip and slots.

Both commands:
- Validate bet limits before touching the database.
- Deduct/credit the wallet atomically via utils/economy.
- Record gambling stats (total_gambled, total_won, total_lost).
- Apply a short per-user cooldown to prevent spam.
"""

import logging
import time
from collections import defaultdict

import discord
from discord import app_commands
from discord.ext import commands

import database as db
import economy_utils as eco
import embeds as emb
from checks import valid_bet
from constants import (
    COINFLIP_MIN_BET, COINFLIP_MAX_BET,
    SLOTS_MIN_BET, SLOTS_MAX_BET,
    GAMBLE_COOLDOWN_S,
)

logger = logging.getLogger(__name__)

# In-memory per-user cooldown tracker  {user_id: last_gamble_timestamp}
_last_gamble: dict[int, float] = defaultdict(float)


def _check_spam(user_id: int) -> float:
    """
    Return remaining cooldown seconds (float).
    Returns 0.0 if the user may gamble now.
    """
    remaining = GAMBLE_COOLDOWN_S - (time.time() - _last_gamble[user_id])
    return max(0.0, remaining)


def _record_gamble_ts(user_id: int) -> None:
    _last_gamble[user_id] = time.time()


class Gambling(commands.Cog, name="Gambling"):
    """🎰 Test your luck with coinflip and slots."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── /coinflip ─────────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="coinflip",
        aliases=["cf", "flip"],
        description="Bet on heads or tails (30% win chance, 2× payout).",
    )
    @app_commands.describe(
        amount="How many potatoes to bet (1–100,000).",
        side="Choose heads or tails.",
    )
    @app_commands.choices(
        side=[
            app_commands.Choice(name="Heads", value="heads"),
            app_commands.Choice(name="Tails", value="tails"),
        ]
    )
    async def coinflip(
        self,
        ctx: commands.Context,
        amount: int,
        side: str,
    ) -> None:
        """Flip a coin and hope for the best. Win = 2× your bet."""
        # Anti-spam cooldown
        remaining = _check_spam(ctx.author.id)
        if remaining > 0:
            return await ctx.reply(
                embed=emb.cooldown_embed("coinflip", remaining),
                mention_author=False,
            )

        # Normalise side input for prefix commands
        side = side.lower()
        if side not in ("heads", "tails"):
            return await ctx.reply(
                embed=emb.error("Invalid Choice", "Please choose **heads** or **tails**."),
                mention_author=False,
            )

        # Validate bet range
        ok, reason = valid_bet(amount, COINFLIP_MIN_BET, COINFLIP_MAX_BET)
        if not ok:
            return await ctx.reply(embed=emb.error("Invalid Bet", reason), mention_author=False)

        # Check wallet balance
        user = await db.get_user(ctx.author.id)
        if user["wallet"] < amount:
            return await ctx.reply(
                embed=emb.error(
                    "Insufficient Funds",
                    f"You only have **{user['wallet']:,}** 🥔 in your wallet.",
                ),
                mention_author=False,
            )

        _record_gamble_ts(ctx.author.id)

        result = await eco.do_coinflip(ctx.author.id, amount, side)
        embed  = emb.coinflip_embed(
            ctx.author,
            amount,
            result["won"],
            side,
            result["result"],
            result["message"],
        )
        await ctx.reply(embed=embed, mention_author=False)

    # ── /slots ────────────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="slots",
        aliases=["slot"],
        description="Spin the slot machine (40% win chance, 2× payout).",
    )
    @app_commands.describe(amount="How many potatoes to bet (1–100,000).")
    async def slots(self, ctx: commands.Context, amount: int) -> None:
        """Spin 🥔 🍟 💰 🎰 — match all three to win double your bet!"""
        # Anti-spam cooldown
        remaining = _check_spam(ctx.author.id)
        if remaining > 0:
            return await ctx.reply(
                embed=emb.cooldown_embed("slots", remaining),
                mention_author=False,
            )

        ok, reason = valid_bet(amount, SLOTS_MIN_BET, SLOTS_MAX_BET)
        if not ok:
            return await ctx.reply(embed=emb.error("Invalid Bet", reason), mention_author=False)

        user = await db.get_user(ctx.author.id)
        if user["wallet"] < amount:
            return await ctx.reply(
                embed=emb.error(
                    "Insufficient Funds",
                    f"You only have **{user['wallet']:,}** 🥔 in your wallet.",
                ),
                mention_author=False,
            )

        _record_gamble_ts(ctx.author.id)

        result = await eco.do_slots(ctx.author.id, amount)
        embed  = emb.slots_embed(
            ctx.author,
            amount,
            result["won"],
            result["reels"],
            result["message"],
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Gambling(bot))
