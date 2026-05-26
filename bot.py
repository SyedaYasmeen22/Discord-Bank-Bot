"""
bot.py
======
Entry point for Potato Banker.

Responsibilities
----------------
1. Load environment variables (.env).
2. Configure the logging system.
3. Initialise the SQLite database.
4. Load every cog from the cogs/ directory.
5. Sync slash commands to Discord on first run.
6. Start the bot and handle graceful shutdown.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from database import init_db

# ── Environment ───────────────────────────────────────────────────────────────

load_dotenv()

TOKEN  = os.getenv("DISCORD_TOKEN", "")
PREFIX = os.getenv("PREFIX", "pot")

if not TOKEN:
    print("[FATAL] DISCORD_TOKEN is not set in .env — cannot start the bot.")
    sys.exit(1)

# ── Logging ───────────────────────────────────────────────────────────────────

Path("data/logs").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/logs/potato_banker.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Silence noisy discord.py internals (keep WARNING+ only)
logging.getLogger("discord.gateway").setLevel(logging.WARNING)
logging.getLogger("discord.client").setLevel(logging.WARNING)
logging.getLogger("discord.http").setLevel(logging.WARNING)

# ── Cog package discovery ──────────────────────────────────────────────────────

COGS_DIR = Path("cogs")
if not COGS_DIR.exists():
    COGS_DIR = Path("mnt/user-data/outputs/PotatoBanker/cogs/cogs")

if not COGS_DIR.exists():
    raise RuntimeError(
        "Unable to locate cogs directory. Expected cogs/ or mnt/user-data/outputs/PotatoBanker/cogs/cogs"
    )

# Ensure the repository root is on sys.path so root modules like database,
# embeds, and constants can be imported from loaded cog modules.
sys.path.insert(0, str(Path(__file__).parent.resolve()))
sys.path.insert(0, str(COGS_DIR.parent.resolve()))

# ── Bot class ─────────────────────────────────────────────────────────────────


class PotatoBot(commands.Bot):
    """Potato Banker — your friendly Discord economy bot."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True  # required for prefix commands
        intents.members = True          # required for leaderboard member resolution

        super().__init__(
            command_prefix=commands.when_mentioned_or(PREFIX),
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
            description="🥔 Potato Banker — managing your spuds since 2024.",
        )

    # ------------------------------------------------------------------
    # async setup_hook runs before on_ready and is the correct place to
    # do async initialisation (DB, cog loading, tree sync).
    # ------------------------------------------------------------------

    async def setup_hook(self) -> None:
        # 1. Ensure the database directory exists and tables are created
        Path("data").mkdir(exist_ok=True)
        Path("data/backups").mkdir(parents=True, exist_ok=True)
        await init_db()
        logger.info("Database ready.")

        # 2. Load cogs
        logger.info("Loading cogs from %s", COGS_DIR)
        for file in sorted(COGS_DIR.iterdir()):
            if file.suffix == ".py" and not file.name.startswith("_"):
                cog = f"cogs.{file.stem}"
                try:
                    await self.load_extension(cog)
                    logger.info("Loaded cog: %s", cog)
                except Exception as exc:  # noqa: BLE001
                    logger.error("Failed to load cog %s: %s", cog, exc)

        # 3. Sync slash commands globally
        #    On first run this can take up to an hour to propagate globally.
        #    For instant testing during development, sync to a specific guild:
        #
        #      guild = discord.Object(id=YOUR_GUILD_ID)
        #      self.tree.copy_global_to(guild=guild)
        #      await self.tree.sync(guild=guild)
        #
        try:
            synced = await self.tree.sync()
            logger.info("Synced %d slash command(s) globally.", len(synced))
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to sync slash commands: %s", exc)

    async def on_ready(self) -> None:
        logger.info("discord.py version: %s", discord.__version__)
        logger.info("=" * 50)
        logger.info("Bot ready!  Logged in as %s (ID %s)", self.user, self.user.id)
        logger.info("Prefix: %r  |  Guilds: %d", PREFIX, len(self.guilds))
        logger.info("=" * 50)

    async def close(self) -> None:
        """Graceful shutdown — flush logs, close DB connections."""
        logger.info("Shutting down Potato Banker…")
        await super().close()


# ── Runner ────────────────────────────────────────────────────────────────────


async def main() -> None:
    async with PotatoBot() as bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user — bye!")
