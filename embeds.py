"""
embeds.py
=========
Factory functions that return fully-formed discord.Embed objects.

Every response in Potato Banker goes through one of these helpers so that
the visual style stays consistent across all cogs.
"""

import datetime
import discord
from constants import (
    COLOUR_PRIMARY,
    COLOUR_SUCCESS,
    COLOUR_ERROR,
    COLOUR_WARNING,
    COLOUR_INFO,
    POTATO_THUMBNAIL,
)


def _base(colour: int) -> discord.Embed:
    """Return an embed with the standard footer timestamp."""
    embed = discord.Embed(colour=colour, timestamp=datetime.datetime.utcnow())
    embed.set_thumbnail(url=POTATO_THUMBNAIL)
    return embed


# ── Generic helpers ───────────────────────────────────────────────────────────

def success(title: str, description: str = "") -> discord.Embed:
    embed = _base(COLOUR_SUCCESS)
    embed.title = f"✅  {title}"
    if description:
        embed.description = description
    return embed


def error(title: str, description: str = "") -> discord.Embed:
    embed = _base(COLOUR_ERROR)
    embed.title = f"❌  {title}"
    if description:
        embed.description = description
    return embed


def warning(title: str, description: str = "") -> discord.Embed:
    embed = _base(COLOUR_WARNING)
    embed.title = f"⚠️  {title}"
    if description:
        embed.description = description
    return embed


def info(title: str, description: str = "") -> discord.Embed:
    embed = _base(COLOUR_INFO)
    embed.title = f"ℹ️  {title}"
    if description:
        embed.description = description
    return embed


# ── Economy embeds ────────────────────────────────────────────────────────────

def balance(user: discord.User | discord.Member, wallet: int, bank: int) -> discord.Embed:
    """Potato-themed balance card."""
    embed = _base(COLOUR_PRIMARY)
    embed.title = f"🥔  {user.display_name}'s Potato Vault"
    embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    embed.add_field(name="👛  Wallet",    value=f"**{wallet:,}** 🥔", inline=True)
    embed.add_field(name="🏦  Bank",      value=f"**{bank:,}** 🥔",   inline=True)
    embed.add_field(name="💰  Total",     value=f"**{wallet + bank:,}** 🥔", inline=False)
    embed.set_footer(text="Potato Banker  •  Your spuds, secured.")
    return embed


def daily_reward(user: discord.User | discord.Member, amount: int, message: str, streak: int) -> discord.Embed:
    embed = _base(COLOUR_SUCCESS)
    embed.title = "🌅  Daily Potatoes Collected!"
    embed.description = message
    embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    embed.add_field(name="Reward",        value=f"**+{amount:,}** 🥔", inline=True)
    embed.add_field(name="🔥  Streak",   value=f"**{streak}** day(s)",  inline=True)
    embed.set_footer(text="Come back in 24 h for more potatoes!")
    return embed


def cooldown_embed(command: str, remaining_seconds: float) -> discord.Embed:
    """Shown when a user triggers a command too early."""
    hours, rem = divmod(int(remaining_seconds), 3600)
    minutes, seconds = divmod(rem, 60)

    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")

    embed = _base(COLOUR_WARNING)
    embed.title = "⏰  Slow Down, Spud!"
    embed.description = (
        f"The **{command}** command is on cooldown.\n"
        f"Come back in **{' '.join(parts)}**."
    )
    return embed


def work_reward(user: discord.User | discord.Member, amount: int, message: str) -> discord.Embed:
    embed = _base(COLOUR_SUCCESS)
    embed.title = "👷  You Did Some Work!"
    embed.description = message
    embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    embed.add_field(name="Earnings", value=f"**+{amount:,}** 🥔", inline=True)
    embed.set_footer(text="Back to the fields in 1 h!")
    return embed


def beg_result(user: discord.User | discord.Member, amount: int, message: str) -> discord.Embed:
    colour = COLOUR_SUCCESS if amount > 0 else COLOUR_WARNING
    embed = _base(colour)
    embed.title = "🙏  Begging Results"
    embed.description = message
    embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    embed.add_field(name="Received", value=f"**{amount:,}** 🥔", inline=True)
    return embed


def transfer_embed(
    sender: discord.User | discord.Member,
    receiver: discord.User | discord.Member,
    amount: int,
) -> discord.Embed:
    embed = _base(COLOUR_SUCCESS)
    embed.title = "📦  Potato Transfer"
    embed.description = (
        f"{sender.mention} sent **{amount:,}** 🥔 to {receiver.mention}!"
    )
    embed.set_footer(text="Potato Banker  •  Safe & secure transfers.")
    return embed


def deposit_embed(user: discord.User | discord.Member, amount: int, new_bank: int) -> discord.Embed:
    embed = _base(COLOUR_SUCCESS)
    embed.title = "🏦  Deposit Successful"
    embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    embed.add_field(name="Deposited",    value=f"**{amount:,}** 🥔",     inline=True)
    embed.add_field(name="Bank Balance", value=f"**{new_bank:,}** 🥔",   inline=True)
    return embed


def withdraw_embed(user: discord.User | discord.Member, amount: int, new_wallet: int) -> discord.Embed:
    embed = _base(COLOUR_SUCCESS)
    embed.title = "💸  Withdrawal Successful"
    embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    embed.add_field(name="Withdrawn",      value=f"**{amount:,}** 🥔",       inline=True)
    embed.add_field(name="Wallet Balance", value=f"**{new_wallet:,}** 🥔",   inline=True)
    return embed


def interest_embed(user: discord.User | discord.Member, amount: int, new_bank: int) -> discord.Embed:
    embed = _base(COLOUR_SUCCESS)
    embed.title = "📈  Daily Interest Claimed!"
    embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    embed.add_field(name="Interest Earned", value=f"**+{amount:,}** 🥔",  inline=True)
    embed.add_field(name="New Bank Balance", value=f"**{new_bank:,}** 🥔", inline=True)
    embed.set_footer(text="1% daily interest on your bank balance.")
    return embed


# ── Gambling embeds ───────────────────────────────────────────────────────────

def coinflip_embed(
    user: discord.User | discord.Member,
    bet: int,
    won: bool,
    chosen: str,
    result: str,
    message: str,
) -> discord.Embed:
    colour = COLOUR_SUCCESS if won else COLOUR_ERROR
    payout = bet * 2 if won else 0
    embed = _base(colour)
    embed.title = "🪙  Coin Flip"
    embed.description = message.format(side=result)
    embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    embed.add_field(name="You chose",  value=chosen.capitalize(),  inline=True)
    embed.add_field(name="Result",     value=result.capitalize(),   inline=True)
    embed.add_field(name="Bet",        value=f"{bet:,} 🥔",         inline=True)
    embed.add_field(name="Payout",     value=f"{payout:,} 🥔",      inline=True)
    return embed


def slots_embed(
    user: discord.User | discord.Member,
    bet: int,
    won: bool,
    reels: list[str],
    message: str,
) -> discord.Embed:
    colour = COLOUR_SUCCESS if won else COLOUR_ERROR
    payout = bet * 2 if won else 0
    embed = _base(colour)
    embed.title = "🎰  Slot Machine"
    embed.description = f"**{'  '.join(reels)}**\n\n{message}"
    embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    embed.add_field(name="Bet",    value=f"{bet:,} 🥔",    inline=True)
    embed.add_field(name="Payout", value=f"{payout:,} 🥔", inline=True)
    return embed


# ── Admin embeds ──────────────────────────────────────────────────────────────

def admin_add(
    admin: discord.User | discord.Member,
    target: discord.User | discord.Member,
    amount: int,
) -> discord.Embed:
    embed = _base(COLOUR_INFO)
    embed.title = "🛠️  Admin: Potatoes Added"
    embed.add_field(name="Target",  value=target.mention,      inline=True)
    embed.add_field(name="Amount",  value=f"+{amount:,} 🥔",   inline=True)
    embed.set_footer(text=f"Action by {admin}")
    return embed


def admin_take(
    admin: discord.User | discord.Member,
    target: discord.User | discord.Member,
    amount: int,
) -> discord.Embed:
    embed = _base(COLOUR_WARNING)
    embed.title = "🛠️  Admin: Potatoes Removed"
    embed.add_field(name="Target",  value=target.mention,      inline=True)
    embed.add_field(name="Amount",  value=f"-{amount:,} 🥔",   inline=True)
    embed.set_footer(text=f"Action by {admin}")
    return embed


# ── Leaderboard ───────────────────────────────────────────────────────────────

def leaderboard_page(
    entries: list[dict],
    page: int,
    total_pages: int,
    guild: discord.Guild,
) -> discord.Embed:
    """
    Build one page of the leaderboard embed.
    *entries* is a slice of the full leaderboard list (already ranked).
    """
    embed = _base(COLOUR_PRIMARY)
    embed.title = f"🏆  {guild.name} Potato Leaderboard"
    embed.set_footer(text=f"Page {page}/{total_pages}  •  Potato Banker")

    if not entries:
        embed.description = "No potato holders found!"
        return embed

    lines = []
    for entry in entries:
        rank   = entry["rank"]
        name   = entry["name"]
        total  = entry["total"]
        medal  = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"`#{rank}`")
        lines.append(f"{medal}  **{name}** — {total:,} 🥔")

    embed.description = "\n".join(lines)
    return embed
