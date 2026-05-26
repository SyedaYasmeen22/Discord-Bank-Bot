"""
pagination.py
=============
discord.ui.View subclass that adds ◀ / ▶ buttons to the leaderboard embed.

The view holds the full ranked list in memory and re-renders the embed on
every button press, so no extra database calls are needed while paginating.
"""

import discord
import embeds as emb


class LeaderboardView(discord.ui.View):
    """Paginated leaderboard with Previous / Next buttons."""

    def __init__(
        self,
        entries: list[dict],    # full ranked list (all pages combined)
        guild: discord.Guild,
        page_size: int = 10,
        *,
        timeout: float = 120.0, # seconds before the buttons stop responding
    ) -> None:
        super().__init__(timeout=timeout)
        self.entries   = entries
        self.guild     = guild
        self.page_size = page_size
        self.page      = 1
        self.total_pages = max(1, -(-len(entries) // page_size))  # ceiling div

        # Disable Prev on first page
        self._sync_buttons()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _current_entries(self) -> list[dict]:
        """Return the slice of entries for the current page."""
        start = (self.page - 1) * self.page_size
        return self.entries[start : start + self.page_size]

    def _sync_buttons(self) -> None:
        """Enable / disable buttons based on current page."""
        self.prev_button.disabled = self.page <= 1
        self.next_button.disabled = self.page >= self.total_pages

    def build_embed(self) -> discord.Embed:
        return emb.leaderboard_page(
            self._current_entries(),
            self.page,
            self.total_pages,
            self.guild,
        )

    # ── Buttons ───────────────────────────────────────────────────────────────

    @discord.ui.button(label="◀  Previous", style=discord.ButtonStyle.secondary, disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.page -= 1
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next  ▶", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.page += 1
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    # ── Timeout ───────────────────────────────────────────────────────────────

    async def on_timeout(self) -> None:
        """Disable all buttons when the view expires."""
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        # The message reference is stored by discord.py automatically via
        # the interaction; nothing extra needed here.
