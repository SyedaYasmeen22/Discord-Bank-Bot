"""
database.py
===========
Async SQLite database manager for Potato Banker.

Responsibilities:
- Create / migrate tables on startup.
- Provide all CRUD helpers used by the cogs.
- Guarantee no negative balances (enforced at DB layer).
- Use parameterised queries throughout to prevent SQL injection.
"""

import logging
import aiosqlite
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Path to the SQLite database file
DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "economy.db"


# ── Schema ────────────────────────────────────────────────────────────────────

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id             INTEGER PRIMARY KEY,
    wallet              INTEGER NOT NULL DEFAULT 0,
    bank                INTEGER NOT NULL DEFAULT 0,
    total_gambled       INTEGER NOT NULL DEFAULT 0,
    total_won           INTEGER NOT NULL DEFAULT 0,
    total_lost          INTEGER NOT NULL DEFAULT 0,
    last_daily          REAL    NOT NULL DEFAULT 0,
    last_work           REAL    NOT NULL DEFAULT 0,
    last_beg            REAL    NOT NULL DEFAULT 0,
    daily_streak        INTEGER NOT NULL DEFAULT 0,
    last_interest_claim REAL    NOT NULL DEFAULT 0,
    CHECK (wallet >= 0),
    CHECK (bank   >= 0)
)
"""


# ── Initialisation ────────────────────────────────────────────────────────────

async def init_db() -> None:
    """Create tables if they don't exist. Called once at bot startup."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")   # better concurrency
        await db.execute("PRAGMA foreign_keys=ON;")
        await db.execute(CREATE_USERS_TABLE)
        await db.commit()
    logger.info("Database initialised at %s", DB_PATH)


# ── User helpers ──────────────────────────────────────────────────────────────

async def ensure_user(user_id: int) -> None:
    """Insert a new user row if one does not already exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,),
        )
        await db.commit()


async def get_user(user_id: int) -> Optional[dict]:
    """
    Return a dict of all columns for *user_id*, or None if not found.
    Calls ensure_user first so a row is always present after this call.
    """
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


# ── Balance operations ────────────────────────────────────────────────────────

async def add_to_wallet(user_id: int, amount: int) -> bool:
    """
    Add *amount* potatoes to wallet.
    Returns True on success, False on failure.
    """
    await ensure_user(user_id)
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE users SET wallet = wallet + ? WHERE user_id = ?",
                (amount, user_id),
            )
            await db.commit()
        return True
    except Exception as exc:
        logger.error("add_to_wallet failed for %s: %s", user_id, exc)
        return False


async def remove_from_wallet(user_id: int, amount: int) -> bool:
    """
    Remove *amount* from wallet.
    Fails (returns False) if the balance would go below 0.
    """
    await ensure_user(user_id)
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # The CHECK constraint on the table prevents negative balances,
            # but we also check explicitly to give a friendly error.
            async with db.execute(
                "SELECT wallet FROM users WHERE user_id = ?", (user_id,)
            ) as cur:
                row = await cur.fetchone()
                if row is None or row[0] < amount:
                    return False
            await db.execute(
                "UPDATE users SET wallet = wallet - ? WHERE user_id = ?",
                (amount, user_id),
            )
            await db.commit()
        return True
    except Exception as exc:
        logger.error("remove_from_wallet failed for %s: %s", user_id, exc)
        return False


async def deposit_to_bank(user_id: int, amount: int) -> bool:
    """Move *amount* from wallet to bank atomically."""
    await ensure_user(user_id)
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT wallet FROM users WHERE user_id = ?", (user_id,)
            ) as cur:
                row = await cur.fetchone()
                if row is None or row[0] < amount:
                    return False
            await db.execute(
                """UPDATE users
                   SET wallet = wallet - ?,
                       bank   = bank   + ?
                   WHERE user_id = ?""",
                (amount, amount, user_id),
            )
            await db.commit()
        return True
    except Exception as exc:
        logger.error("deposit_to_bank failed for %s: %s", user_id, exc)
        return False


async def withdraw_from_bank(user_id: int, amount: int) -> bool:
    """Move *amount* from bank to wallet atomically."""
    await ensure_user(user_id)
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT bank FROM users WHERE user_id = ?", (user_id,)
            ) as cur:
                row = await cur.fetchone()
                if row is None or row[0] < amount:
                    return False
            await db.execute(
                """UPDATE users
                   SET bank   = bank   - ?,
                       wallet = wallet + ?
                   WHERE user_id = ?""",
                (amount, amount, user_id),
            )
            await db.commit()
        return True
    except Exception as exc:
        logger.error("withdraw_from_bank failed for %s: %s", user_id, exc)
        return False


async def transfer_wallet(sender_id: int, receiver_id: int, amount: int) -> bool:
    """Transfer *amount* from sender's wallet to receiver's wallet atomically."""
    await ensure_user(sender_id)
    await ensure_user(receiver_id)
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT wallet FROM users WHERE user_id = ?", (sender_id,)
            ) as cur:
                row = await cur.fetchone()
                if row is None or row[0] < amount:
                    return False
            await db.execute(
                "UPDATE users SET wallet = wallet - ? WHERE user_id = ?",
                (amount, sender_id),
            )
            await db.execute(
                "UPDATE users SET wallet = wallet + ? WHERE user_id = ?",
                (amount, receiver_id),
            )
            await db.commit()
        return True
    except Exception as exc:
        logger.error("transfer_wallet failed %s→%s: %s", sender_id, receiver_id, exc)
        return False


# ── Gambling stats ────────────────────────────────────────────────────────────

async def record_gamble(user_id: int, bet: int, won: bool) -> None:
    """Update cumulative gambling statistics for a user."""
    await ensure_user(user_id)
    if won:
        await _update_field(user_id, "total_won", bet)
    else:
        await _update_field(user_id, "total_lost", bet)
    await _update_field(user_id, "total_gambled", bet)


async def _update_field(user_id: int, field: str, delta: int) -> None:
    """Generic helper to increment a numeric field (internal use only)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE users SET {field} = {field} + ? WHERE user_id = ?",  # noqa: S608
            (delta, user_id),
        )
        await db.commit()


# ── Cooldown helpers ──────────────────────────────────────────────────────────

async def set_timestamp(user_id: int, field: str, ts: float) -> None:
    """Store a Unix timestamp in the given column."""
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE users SET {field} = ? WHERE user_id = ?",  # noqa: S608
            (ts, user_id),
        )
        await db.commit()


# ── Interest ──────────────────────────────────────────────────────────────────

async def apply_interest(user_id: int, rate: float, ts: float) -> int:
    """
    Calculate and apply daily interest to the bank balance.
    Returns the number of potatoes added (0 if nothing was done).
    """
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT bank, last_interest_claim FROM users WHERE user_id = ?",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return 0
        bank, last_claim = row
        interest = int(bank * rate)
        if interest <= 0:
            return 0
        await db.execute(
            """UPDATE users
               SET bank = bank + ?,
                   last_interest_claim = ?
               WHERE user_id = ?""",
            (interest, ts, user_id),
        )
        await db.commit()
    return interest


# ── Leaderboard ───────────────────────────────────────────────────────────────

async def get_leaderboard(guild_member_ids: list[int], limit: int = 50) -> list[dict]:
    """
    Return up to *limit* users sorted by total wealth (wallet + bank),
    filtered to members currently in the guild.
    """
    if not guild_member_ids:
        return []

    placeholders = ",".join("?" * len(guild_member_ids))
    query = f"""
        SELECT user_id,
               wallet,
               bank,
               (wallet + bank) AS total
        FROM   users
        WHERE  user_id IN ({placeholders})
        ORDER  BY total DESC
        LIMIT  ?
    """  # noqa: S608 – placeholders are safe; column names are hardcoded
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, (*guild_member_ids, limit)) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]
