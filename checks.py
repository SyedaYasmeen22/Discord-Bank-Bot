"""
checks.py
=========
Reusable guard functions and custom discord.py check decorators
used across multiple cogs.
"""

import discord
from discord.ext import commands


def is_admin():
    """
    Command check: caller must have Administrator permission
    OR be the server owner.
    Works for both prefix and slash (hybrid) commands.
    """
    async def predicate(ctx: commands.Context) -> bool:
        if isinstance(ctx.author, discord.Member):
            return (
                ctx.author.guild_permissions.administrator
                or ctx.author.id == ctx.guild.owner_id
            )
        return False

    return commands.check(predicate)


def positive_amount(amount: int) -> bool:
    """Return True if *amount* is a strictly positive integer."""
    return isinstance(amount, int) and amount > 0


def valid_bet(amount: int, min_bet: int, max_bet: int) -> tuple[bool, str]:
    """
    Validate a gambling bet.
    Returns (True, "") on success or (False, reason) on failure.
    """
    if amount < min_bet:
        return False, f"Minimum bet is **{min_bet:,}** 🥔."
    if amount > max_bet:
        return False, f"Maximum bet is **{max_bet:,}** 🥔."
    return True, ""
