<div align="center">

# Ludext

**Your private morning briefing, self-hosted on a Raspberry Pi.**

Calendar, tasks, medicines and news (as a voice note), delivered to Telegram every morning.<br>
Your data lives on your own hardware. No subscriptions. No AI cloud services.

[![License: MIT](https://img.shields.io/github/license/iamLudok/Ludext?style=flat-square&color=blue)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4%20%7C%205-A22846?style=flat-square&logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com/)
[![Nextcloud](https://img.shields.io/badge/Nextcloud-self--hosted-0082C9?style=flat-square&logo=nextcloud&logoColor=white)](https://nextcloud.com/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-bot-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://core.telegram.org/bots)

[Features](#features) · [Installation](#installation) · [Commands](docs/commands.md) · [Docs](docs/features.md) · [License](#license)

</div>

---

## Table of Contents

- [Why Ludext?](#why-ludext)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Cron & Services](#cron--services)
- [Contributing](#contributing)
- [License](#license)

---

## Why Ludext?

Most assistants send your personal data to external servers. Ludext is built around a different principle: **your data stays yours**.

- 🏠 **Self-hosted data**: Nextcloud stores your calendar, tasks, notes, and news feeds on hardware you own and control.
- 🔒 **Local processing**: the briefing is built on the Pi, the news audio is synthesized locally with Piper. No data is sent to AI or analytics providers.
- 💸 **No subscriptions**: once set up, Ludext runs for free indefinitely.

> **What does leave your network:** the briefing, news audio and bot replies are delivered through Telegram's servers (bot chats are not end-to-end encrypted). Everything else (calendar, tasks, notes, news) stays on your Nextcloud.

---

## Tech Stack

| Layer | Technology | Role |
|---|---|---|
| Self-hosted data | Nextcloud | Calendar, tasks, news feeds, notes |
| Text to speech | Piper | Reads the news aloud, runs locally |
| Delivery | Telegram Bot | Sends the briefing and accepts commands |
| Runtime | Raspberry Pi 4/5 | Runs the whole stack, 24/7 |

---

## Features

### Daily Briefing (automatic, every morning at 7:30)
- 📅 **Calendar**: events for today and tomorrow
- ✅ **Pending tasks**: most urgent ones highlighted
- 📰 **News**: the top headlines from your Nextcloud News feeds, plus a voice note that reads every article aloud
- 💊 **Medicines**: which ones to take today and at what time

### Telegram Bot (always on, responds instantly)
- 🗂️ **Organize**: manage tasks, calendar events, medicines, shopping list, car expenses, wishlist, and gift ideas directly from Telegram
- ⏰ **Reminders**: a notification 30 minutes before every calendar event, and medicine reminders with a one-tap ✅ button
- 🖥️ **System health**: automatic alerts for high CPU temperature, RAM, or disk usage, plus a network device scanner

The bot only answers your own `TELEGRAM_CHAT_ID`; messages from anyone else are ignored.

→ [Full command reference](docs/commands.md)  
→ [Feature documentation](docs/features.md)

---

## Requirements

### Hardware
- Raspberry Pi 4 or 5 (8 GB RAM recommended)

### Nextcloud apps
- **Calendar**: for CalDAV events and tasks
- **News**: for RSS feed summaries
- **Notes**: for shopping list, car expenses, wishlist, gift ideas, and medicine tracking

### Other
- A Telegram account to create a bot
- `nmap` and `ffmpeg` installed on the Pi (installed by `setup.sh`)
- ~65 MB for the Spanish Piper voice, downloaded by `setup.sh` into `voices/`

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/iamLudok/Ludext.git ~/Ludext
cd ~/Ludext
```

### 2. Run the setup script

```bash
bash deploy/setup.sh
```

This installs system dependencies, creates a Python virtual environment, installs the packages from `requirements.txt`, configures the daily cron job at 7:30, and installs the Telegram bot as a systemd service.

> **Security note:** so that `/red` can do a full ARP scan without running as root, the script grants `nmap` the `cap_net_raw` capability. This lets **any user on the Pi** run raw network scans. That's fine on a single-user Pi; on a shared machine, revert it with `sudo setcap -r "$(which nmap)"`. `/red` keeps working, but unprivileged `nmap` may miss devices that don't answer TCP probes.

### 3. Configure your credentials

```bash
cp .env.example .env
nano .env
```

| Variable | Description |
|---|---|
| `NEXTCLOUD_URL` | Your Nextcloud URL, e.g. `http://192.168.1.50:8080` |
| `NEXTCLOUD_USER` | Your Nextcloud username |
| `NEXTCLOUD_PASSWORD` | A Nextcloud [app password](https://docs.nextcloud.com/server/latest/user_manual/en/session_management.html#managing-devices), not your account password |
| `NEXTCLOUD_CALDAV_URL` | Usually `NEXTCLOUD_URL/remote.php/dav` |
| `TELEGRAM_TOKEN` | Your Telegram bot token |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |
| `PIPER_VOICE` | Optional: path to another Piper voice `.onnx` (default `voices/es_ES-davefx-medium.onnx`) |

### 4. Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the steps
3. Copy the token into `.env` → `TELEGRAM_TOKEN`
4. Send any message to your new bot, then open:  
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
5. Find `"id"` inside `"chat"`. That's your `TELEGRAM_CHAT_ID`

### 5. Register bot commands

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
You only need to do this once. The commands persist on Telegram's side and survive bot restarts.

### 6. Test it

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
│   ├── audio.py            ← News voice note (Piper TTS)
│   ├── config.py           ← Reads .env and exposes CONFIG
│   └── sources.py          ← Data collection (calendar, tasks, news)
├── deploy/
│   └── setup.sh            ← Automated installation script
├── docs/
│   ├── commands.md         ← Full Telegram command reference
│   └── features.md         ← Feature documentation
├── notes/
│   ├── api.py              ← Nextcloud Notes interface
│   ├── car.py              ← Car expenses
│   ├── gifts.py            ← Gift ideas list
│   ├── medicine.py         ← Medicine tracking
│   ├── shopping.py         ← Shopping list
│   └── wishlist.py         ← Wishlist
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

## Contributing

Pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the development setup and conventions. To report a security vulnerability, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.

---

## License

Distributed under the **MIT License**. You are free to use, modify and share Ludext, including for commercial use, as long as you keep the copyright notice. See [LICENSE](LICENSE) for the full text.

---

<div align="center">

Made by [Luken Iriondo](https://github.com/iamLudok) · If Ludext is useful to you, consider giving it a ⭐

</div>
