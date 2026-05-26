"""
cogs/leaderboard.py
===================
Leaderboard command with interactive button pagination.

Fetches the top 50 members of the current guild (by wallet + bank),
resolves their Discord usernames, and renders pages of 10 via
utils/pagination.LeaderboardView.
"""

import logging

import discord
from discord.ext import commands

import database as db
import embeds as emb
from constants import LEADERBOARD_PAGE_SIZE
from pagination import LeaderboardView

logger = logging.getLogger(__name__)


class Leaderboard(commands.Cog, name="Leaderboard"):
    """🏆 See who has the most potatoes in the server."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="leaderboard",
        aliases=["lb", "top", "richest"],
        description="Show the richest potato holders in this server.",
    )
    async def leaderboard(self, ctx: commands.Context) -> None:
        """Display the server's top potato holders (10 per page)."""
        if ctx.guild is None:
            return await ctx.reply(
                embed=emb.error("Server Only", "This command can only be used in a server."),
                mention_author=False,
            )

        # Collect member IDs so we filter out people who left
        member_ids = [m.id for m in ctx.guild.members if not m.bot]
        if not member_ids:
            return await ctx.reply(
                embed=emb.info("Leaderboard", "No members found in this server."),
                mention_author=False,
            )

        raw = await db.get_leaderboard(member_ids, limit=50)
        if not raw:
            return await ctx.reply(
                embed=emb.info(
                    "Leaderboard",
                    "Nobody has any potatoes yet! Run `/daily` to get started. 🥔",
                ),
                mention_author=False,
            )

        # Resolve usernames and add rank field
        entries: list[dict] = []
        for rank, row in enumerate(raw, start=1):
            member = ctx.guild.get_member(row["user_id"])
            name   = member.display_name if member else f"Unknown ({row['user_id']})"
            entries.append({
                "rank":  rank,
                "name":  name,
                "total": row["total"],
            })

        view  = LeaderboardView(entries, ctx.guild, page_size=LEADERBOARD_PAGE_SIZE)
        embed = view.build_embed()

        # Slash commands support ephemeral; prefix commands just reply normally.
        await ctx.reply(embed=embed, view=view, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leaderboard(bot))
