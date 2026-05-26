"""
economy.py  (utils)
===================
Shared business-logic helpers shared across cogs.
Keeps the cog files thin and prevents duplicate code.
"""

import json
import random
import time
import logging
from pathlib import Path

import database as db
from constants import (
    DAILY_MIN, DAILY_MAX,
    WORK_REWARD,
    BEG_MIN, BEG_MAX,
    DAILY_COOLDOWN_S, WORK_COOLDOWN_S, BEG_COOLDOWN_S,
    INTEREST_RATE, INTEREST_COOLDOWN_H,
    COINFLIP_WIN_CHANCE, COINFLIP_MULTIPLIER,
    SLOTS_WIN_CHANCE, SLOT_EMOJIS,
)

logger = logging.getLogger(__name__)

# ── Load messages once at import time ─────────────────────────────────────────
MESSAGES_PATH = Path(__file__).resolve().parent / "messages.json"
with open(MESSAGES_PATH, encoding="utf-8") as _f:
    MESSAGES: dict = json.load(_f)


# ── Interest (called automatically during economy commands) ───────────────────

async def maybe_apply_interest(user_id: int) -> int:
    """
    If 24 h have elapsed since the last interest claim for *user_id*,
    apply 1% interest to their bank balance and return the amount earned.
    Returns 0 if interest was not applied this call.
    """
    user = await db.get_user(user_id)
    if user is None:
        return 0

    now = time.time()
    last = user["last_interest_claim"]
    if now - last >= INTEREST_COOLDOWN_H * 3600:
        return await db.apply_interest(user_id, INTEREST_RATE, now)
    return 0


# ── Daily ─────────────────────────────────────────────────────────────────────

async def claim_daily(user_id: int) -> dict:
    """
    Try to claim the daily reward.

    Returns a dict:
      success  bool
      amount   int  (0 if on cooldown)
      streak   int
      remaining float  (seconds remaining if on cooldown)
      message  str
    """
    user = await db.get_user(user_id)
    now  = time.time()
    last = user["last_daily"]
    remaining = DAILY_COOLDOWN_S - (now - last)

    if remaining > 0:
        return {"success": False, "amount": 0, "streak": user["daily_streak"],
                "remaining": remaining, "message": ""}

    amount = random.randint(DAILY_MIN, DAILY_MAX)
    streak = user["daily_streak"] + 1

    # Streak bonus: +5 potatoes per streak day (capped at day 30)
    bonus = min(streak, 30) * 5
    amount += bonus

    await db.add_to_wallet(user_id, amount)

    # Update streak + timestamp
    async with __import__("aiosqlite").connect(db.DB_PATH) as conn:
        await conn.execute(
            "UPDATE users SET last_daily = ?, daily_streak = ? WHERE user_id = ?",
            (now, streak, user_id),
        )
        await conn.commit()

    msg = random.choice(MESSAGES["daily"]).format(amount=amount)
    return {"success": True, "amount": amount, "streak": streak,
            "remaining": 0.0, "message": msg}


# ── Work ──────────────────────────────────────────────────────────────────────

async def do_work(user_id: int) -> dict:
    """
    Try to work for potatoes.

    Returns:
      success  bool
      amount   int
      remaining float
      message  str
    """
    user = await db.get_user(user_id)
    now  = time.time()
    last = user["last_work"]
    remaining = WORK_COOLDOWN_S - (now - last)

    if remaining > 0:
        return {"success": False, "amount": 0, "remaining": remaining, "message": ""}

    await db.add_to_wallet(user_id, WORK_REWARD)
    await db.set_timestamp(user_id, "last_work", now)

    msg = random.choice(MESSAGES["work"])
    return {"success": True, "amount": WORK_REWARD, "remaining": 0.0, "message": msg}


# ── Beg ───────────────────────────────────────────────────────────────────────

async def do_beg(user_id: int) -> dict:
    """
    Try to beg for potatoes.

    Returns:
      success   bool  (False = cooldown)
      amount    int   (0 = begged but got nothing)
      remaining float
      message   str
    """
    user = await db.get_user(user_id)
    now  = time.time()
    last = user["last_beg"]
    remaining = BEG_COOLDOWN_S - (now - last)

    if remaining > 0:
        return {"success": False, "amount": 0, "remaining": remaining, "message": ""}

    amount = random.randint(BEG_MIN, BEG_MAX)
    if amount > 0:
        await db.add_to_wallet(user_id, amount)
        msg = random.choice(MESSAGES["beg_success"]).format(amount=amount)
    else:
        msg = random.choice(MESSAGES["beg_fail"])

    await db.set_timestamp(user_id, "last_beg", now)
    return {"success": True, "amount": amount, "remaining": 0.0, "message": msg}


# ── Coinflip ──────────────────────────────────────────────────────────────────

async def do_coinflip(user_id: int, bet: int, chosen: str) -> dict:
    """
    Flip a (weighted) coin.

    chosen must be 'heads' or 'tails'.
    Win probability = COINFLIP_WIN_CHANCE (30%).
    Win payout = bet × COINFLIP_MULTIPLIER.

    Returns:
      won      bool
      result   str  ('heads' or 'tails')
      net      int  (positive = gained, negative = lost)
      message  str
    """
    result = random.choices(["heads", "tails"], weights=[50, 50], k=1)[0]
    won    = (result == chosen) and (random.random() < COINFLIP_WIN_CHANCE / 0.5)

    # Simpler: independently decide win/lose based on COINFLIP_WIN_CHANCE
    won = random.random() < COINFLIP_WIN_CHANCE

    if won:
        net = bet * (COINFLIP_MULTIPLIER - 1)   # already has bet; net gain
        await db.add_to_wallet(user_id, net)
        msg = random.choice(MESSAGES["coinflip_win"])
    else:
        net = -bet
        await db.remove_from_wallet(user_id, bet)
        msg = random.choice(MESSAGES["coinflip_lose"])

    await db.record_gamble(user_id, bet, won)
    return {"won": won, "result": result, "net": net, "message": msg}


# ── Slots ─────────────────────────────────────────────────────────────────────

async def do_slots(user_id: int, bet: int) -> dict:
    """
    Spin the slot machine.
    Win = all three reels show the same emoji (SLOTS_WIN_CHANCE override).

    Returns:
      won    bool
      reels  list[str]
      net    int
      message str
    """
    reels = [random.choice(SLOT_EMOJIS) for _ in range(3)]
    # Override RNG result with configured win probability
    won = random.random() < SLOTS_WIN_CHANCE

    if won:
        # Force matching reels on a win
        symbol = random.choice(SLOT_EMOJIS)
        reels  = [symbol, symbol, symbol]
        net    = bet   # win = +bet (total payout = bet*2, but they keep original bet)
        await db.add_to_wallet(user_id, net)
        msg = random.choice(MESSAGES["slots_win"])
    else:
        # Ensure reels don't accidentally all match
        while len(set(reels)) == 1:
            reels = [random.choice(SLOT_EMOJIS) for _ in range(3)]
        net = -bet
        await db.remove_from_wallet(user_id, bet)
        msg = random.choice(MESSAGES["slots_lose"])

    await db.record_gamble(user_id, bet, won)
    return {"won": won, "reels": reels, "net": net, "message": msg}
