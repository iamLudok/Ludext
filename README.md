# Ludext — Private Morning Briefing

[![License MIT](https://img.shields.io/github/license/iamLudok/ludext?cacheSeconds=1)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![Runs on](https://img.shields.io/badge/runs%20on-Raspberry%20Pi-c51a4a)](https://www.raspberrypi.com/)
[![Self-hosted](https://img.shields.io/badge/self--hosted-no%20cloud-green)](#)

**Ludext** is a self-hosted assistant that runs on a Raspberry Pi. Every morning it collects your emails, calendar events, tasks, and news from your own infrastructure, builds a briefing, and sends you a Telegram message before you start your day.

No data ever leaves your home network. No subscriptions. No third-party APIs.

---

## Why Ludext?

Most assistants send your personal data to external servers. Ludext is built around a different principle: **your data stays yours**.

- 🏠 **Self-hosted data** — Nextcloud stores your calendar, tasks, notes, photos, and news feeds on hardware you own and control.
- 🔒 **Everything runs locally** — even the semantic photo search uses a local CLIP model on the Pi; nothing is sent to any cloud provider.
- 💸 **No subscriptions** — Once set up, Ludext runs for free indefinitely.

---

## Tech Stack

| Layer | Technology | Role |
|---|---|---|
| Email | Gmail (IMAP) | Fetches and filters unread messages |
| Self-hosted data | Nextcloud | Calendar, tasks, news feeds, notes, photos |
| Photo search | CLIP (sentence-transformers) | Semantic photo search, runs locally |
| Delivery | Telegram Bot | Sends the briefing and accepts commands |
| Runtime | Raspberry Pi 4/5 | Runs the whole stack, 24/7 |

---

## Features

### Daily Briefing (automatic, every morning at 7:30)
- 📧 **Unread emails** — filtered and summarized, only what matters
- 📅 **Calendar** — events for today and tomorrow
- ✅ **Pending tasks** — most urgent ones highlighted
- 📰 **News** — relevant articles from your Nextcloud News feeds
- 💊 **Medicines** — which ones to take today and at what time

### Telegram Bot (always on, responds instantly)
Manage tasks, calendar events, medicines, shopping list, car expenses, and wishlist directly from Telegram. Search your Nextcloud photos by natural-language description (local CLIP model). The bot also monitors system health and sends automatic alerts for high CPU temperature, RAM, or disk usage.

→ [Full command reference](docs/commands.md)  
→ [Feature documentation](docs/features.md)

---

## Requirements

### Hardware
- Raspberry Pi 4 or 5 (8 GB RAM recommended)

### Nextcloud apps
- **Calendar** — for CalDAV events and tasks
- **News** — for RSS feed summaries
- **Notes** — for shopping list, car expenses, and medicine tracking

### Other
- A Gmail account with IMAP enabled
- A Telegram account to create a bot
- `nmap` installed on the Pi (for the `/red` command)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/iamLudok/ludext.git ~/Ludext
cd ~/Ludext
```

### 2. Run the setup script

```bash
bash deploy/setup.sh
```

This installs system dependencies, creates a Python virtual environment, installs the packages from `requirements.txt`, configures the daily cron job at 7:30, and installs the Telegram bot as a systemd service.

### 3. Configure your credentials

```bash
cp .env.example .env
nano .env
```

| Variable | Description |
|---|---|
| `GMAIL_USER` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | Gmail app password (see below) |
| `NEXTCLOUD_URL` | Your Nextcloud URL, e.g. `http://192.168.1.50:8080` |
| `NEXTCLOUD_USER` | Your Nextcloud username |
| `NEXTCLOUD_PASSWORD` | Your Nextcloud password |
| `NEXTCLOUD_CALDAV_URL` | Usually `NEXTCLOUD_URL/remote.php/dav` |
| `TELEGRAM_TOKEN` | Your Telegram bot token |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |

### 4. Gmail App Password

Gmail requires an app-specific password for IMAP access:

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already active
3. Go to **App passwords** and create a new one named "Ludext"
4. Copy the 16-character code into `.env` → `GMAIL_APP_PASSWORD`

### 5. Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the steps
3. Copy the token into `.env` → `TELEGRAM_TOKEN`
4. Send any message to your new bot, then open:  
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
5. Find `"id"` inside `"chat"` — that's your `TELEGRAM_CHAT_ID`

### 6. Register bot commands

This makes Telegram show the command menu when you type `/` in the chat.  
Run `setMyCommands` once with whichever commands you want to expose (replace `<YOUR_TOKEN>`):

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setMyCommands" \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {"command": "ayuda", "description": "Muestra todos los comandos"},
      {"command": "tareas", "description": "Lista tus tareas pendientes"}
    ]
  }'
```

Full list of available commands: `/ayuda` inside the bot or [docs/commands.md](docs/commands.md).  
You only need to do this once — the commands persist on Telegram's side and survive bot restarts.

### 7. Test it

```bash
source ~/ludext-env/bin/activate
python3 ludext.py
```

Use `--debug` to save the generated briefing to a file:

```bash
python3 ludext.py --debug
cat ludext_briefing.txt
```

---

## Project Structure

```
Ludext/
├── .env.example            ← Template for .env
├── .gitignore              ← Excludes files from git
├── LICENSE                 ← MIT license
├── ludext.py               ← Daily briefing script (runs via cron)
├── README.md               ← Project documentation
├── requirements.txt        ← Python dependencies
├── bot/
│   ├── __main__.py         ← Telegram polling and background threads
│   ├── background.py       ← Background alerts
│   └── handlers.py         ← Telegram bot command handlers
├── core/
│   ├── ai.py               ← Builds the briefing text
│   ├── config.py           ← Reads .env and exposes CONFIG
│   └── sources.py          ← Data collection (emails, calendar, tasks, news)
├── deploy/
│   └── setup.sh            ← Automated installation script
├── docs/
│   ├── commands.md         ← Full Telegram command reference
│   └── features.md         ← Feature documentation
├── notes/
│   ├── api.py              ← Nextcloud Notes interface
│   ├── car.py              ← Car expenses
│   ├── gf_gifts.py         ← Gift ideas list
│   ├── medicine.py         ← Medicine tracking
│   ├── shopping.py         ← Shopping list
│   └── wishlist.py         ← Wishlist
├── photos/
│   ├── indexer.py          ← Indexes Nextcloud photos with CLIP
│   └── search.py           ← Semantic photo search
├── scheduling/
│   ├── events.py           ← Event CRUD (Nextcloud CalDAV)
│   └── tasks.py            ← Task CRUD (Nextcloud CalDAV)
└── system/
    ├── monitor.py          ← System monitor (CPU temp, RAM, disk, uptime)
    └── network.py          ← Network device scanner
```

---

## Cron & Services

```bash
crontab -l                                  # daily briefing schedule
sudo systemctl status ludext-bot            # Telegram bot service

cat ~/ludext.log                            # daily briefing logs
journalctl -u ludext-bot -n 50 --no-pager  # bot logs
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.
