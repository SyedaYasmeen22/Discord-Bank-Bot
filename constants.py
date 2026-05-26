"""
constants.py
============
Central configuration for Potato Banker bot.
All magic numbers, colours, limits and cooldowns live here
so you only ever have to change one file.
"""

# ── Colour palette ────────────────────────────────────────────────────────────
COLOUR_PRIMARY   = 0xF4A460  # sandy-brown  – main brand colour
COLOUR_SUCCESS   = 0x2ECC71  # green        – positive outcomes
COLOUR_ERROR     = 0xE74C3C  # red          – errors / failures
COLOUR_WARNING   = 0xF39C12  # orange       – warnings / cooldowns
COLOUR_INFO      = 0x3498DB  # blue         – neutral information

# ── Economy limits ────────────────────────────────────────────────────────────
DAILY_MIN            = 10        # minimum daily reward (potatoes)
DAILY_MAX            = 100       # maximum daily reward
WORK_REWARD          = 10        # fixed work reward
BEG_MIN              = 0         # minimum beg reward (can be zero)
BEG_MAX              = 100       # maximum beg reward

COINFLIP_MIN_BET     = 1
COINFLIP_MAX_BET     = 100_000
COINFLIP_WIN_CHANCE  = 0.30      # 30 % win probability
COINFLIP_MULTIPLIER  = 2         # win = bet × 2

SLOTS_MIN_BET        = 1
SLOTS_MAX_BET        = 100_000
SLOTS_WIN_CHANCE     = 0.40      # 40 % win probability

# ── Interest ──────────────────────────────────────────────────────────────────
INTEREST_RATE        = 0.01      # 1 % daily interest on bank balance
INTEREST_COOLDOWN_H  = 24        # hours between interest claims

# ── Cooldowns (seconds) ───────────────────────────────────────────────────────
DAILY_COOLDOWN_S     = 86_400    # 24 h
WORK_COOLDOWN_S      = 3_600     # 1 h
BEG_COOLDOWN_S       = 300       # 5 min
GAMBLE_COOLDOWN_S    = 10        # anti-spam between gambling commands

# ── Leaderboard ───────────────────────────────────────────────────────────────
LEADERBOARD_PAGE_SIZE = 10       # users displayed per page

# ── Slot machine emojis ───────────────────────────────────────────────────────
SLOT_EMOJIS = ["🥔", "🍟", "💰", "🎰"]

# ── Bot thumbnail URL (used in embeds) ────────────────────────────────────────
# Replace with your own CDN link if you host a custom icon.
POTATO_THUMBNAIL = "https://em-content.zobj.net/source/twitter/376/potato_1f954.png"
