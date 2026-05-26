# 🥔 Potato Banker — Discord Economy Bot

**Potato Banker** is a polished Discord economy bot built in **Python 3.11+** using **discord.py** and **SQLite**.
It supports hybrid commands, structure for scalable cog loading, and secure async database access.

---

## 🚀 What This Bot Does

- `/balance` / `pot balance` — show wallet and bank balances
- `/daily` — claim daily potatoes with streak bonuses
- `/work` — earn potatoes on cooldown
- `/beg` — ask for potatoes with a low reward chance
- `/give` — send potatoes to another user
- `/deposit` / `/withdraw` / `/interest` — bank features with interest and storage
- `/coinflip` / `/slots` — gambling commands with risk/reward
- `/leaderboard` — interactive server leaderboard
- `/add` / `/take` — admin-only balance adjustments

---

## 📁 Repository Layout

```text
Discord-Bot/
├── bot.py
├── database.py
├── economy_utils.py
├── embeds.py
├── checks.py
├── constants.py
├── pagination.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
├── data/
│   └── messages.json
├── mnt/user-data/outputs/PotatoBanker/cogs/cogs/
│   ├── admin.py
│   ├── bank.py
│   ├── economy.py
│   ├── events.py
│   ├── gambling.py
│   └── leaderboard.py
└── venv/
```

---

## ⚙️ Installation

### Requirements

- Python 3.11+
- `pip`

### Setup

```powershell
cd E:\Repos\Discord-Bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Environment

Copy the example file and set your bot token:

```powershell
copy .env.example .env
```

Then update `.env`:

```env
DISCORD_TOKEN=your_token_here
PREFIX=pot
```

> Use a prefix like `pot` or `!` as desired.

---

## 🚨 Discord Bot Setup

1. Open the [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a new application.
3. Add a Bot and copy its token.
4. Enable:
   - Server Members Intent
   - Message Content Intent
5. In OAuth2 URL Generator select:
   - `bot`
   - `applications.commands`
6. Grant bot permissions to send messages, embed links, and read message history.
7. Invite the bot to your server.

---

## ▶️ Run the Bot

```powershell
python bot.py
```

Expected startup output:

```text
Bot ready!  Logged in as Potato Banker#1234 (ID 123456789)
```

---

## 🗄️ Database

The bot uses **SQLite** stored in `data/economy.db`.
This file is created automatically on first launch.

### Data directory

- `data/` — runtime assets and database files
- `data/messages.json` — command response templates and flavour text

### Safety

- The database schema prevents negative wallet/bank values.
- All SQL operations use parameterised queries.
- `PRAGMA journal_mode=WAL` improves concurrency.

---

## 📋 Supported Commands

All commands are available as slash commands and prefix commands.

### Economy

- `/balance [@member]`
- `/daily`
- `/work`
- `/beg`
- `/give <@member> <amount>`

### Bank

- `/deposit <amount|all>`
- `/withdraw <amount|all>`
- `/interest`

### Gambling

- `/coinflip <amount> <heads|tails>`
- `/slots <amount>`

### Leaderboard

- `/leaderboard`

### Admin only

- `/add <@member> <amount>`
- `/take <@member> <amount>`

---

## 🧩 Notes

- `add` and `take` are restricted to administrators only.
- Slash commands are automatically loaded from the `cogs` directory.
- Logs and runtime files are stored in `data/logs` and `data/backups`.

---

## 💡 Customization

- Modify `PREFIX` in `.env`
- Add new commands by creating a new cog in `mnt/user-data/outputs/PotatoBanker/cogs/cogs`
- Keep shared logic in `economy_utils.py`, `database.py`, and `embeds.py`

---

## 📬 Support

If you want help adding features or debugging commands, open an issue or message the maintainer directly.

```python
DAILY_MIN           = 10        # minimum daily reward
DAILY_MAX           = 100       # maximum daily reward
WORK_REWARD         = 10        # fixed work reward
COINFLIP_WIN_CHANCE = 0.30      # 30 % win probability
SLOTS_WIN_CHANCE    = 0.40      # 40 % win probability
INTEREST_RATE       = 0.01      # 1 % daily interest
```

---

## 🐛 Troubleshooting

**Bot doesn't respond to prefix commands**  
→ Make sure **Message Content Intent** is enabled in the Developer Portal.

**Slash commands don't appear**  
→ Global sync can take up to 1 hour to propagate. For instant testing, switch to guild sync in `bot.py` (see the comment in `setup_hook`).

**`DISCORD_TOKEN is not set` error**  
→ Make sure you copied `.env.example` to `.env` and filled in your token.

**`ModuleNotFoundError: No module named 'discord'`**  
→ Run `pip install -r requirements.txt` inside your virtual environment.

**Database errors on startup**  
→ Make sure the `database/` directory exists. The bot creates it automatically, but if permissions are wrong, create it manually: `mkdir database`.

---

## 📄 License

MIT — do whatever you want with it. Just don't steal other people's potatoes. 🥔
