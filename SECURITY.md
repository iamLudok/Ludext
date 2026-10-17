# Security Policy

## Supported Versions

Ludext is a personal project. Only the latest version on the `main` branch receives security fixes.

| Version | Supported |
|---|---|
| `main` (latest) | ✅ |
| Older commits and releases | ❌ |

## Reporting a Vulnerability

**Please do not report security problems in a public issue.** Issues are visible to everyone, so describing a vulnerability there would show anyone how to attack existing Ludext installations before a fix is available.

Report it privately through GitHub instead:

1. Go to the [Security tab](https://github.com/iamLudok/Ludext/security) of this repository
2. Click **Report a vulnerability**
3. Describe the issue, how to reproduce it, and its possible impact

Only the maintainer can see the report. You can expect a first response within a week. Once the issue is confirmed and fixed, the details are made public and you will be credited, unless you prefer to stay anonymous.

## Scope

In scope:

- Leaks of credentials or personal data handled by Ludext (Nextcloud, Telegram)
- Ways to make the bot run commands for a chat other than the configured `TELEGRAM_CHAT_ID`
- Injection or unsafe handling of command arguments, notes, news or calendar data
- Issues in `deploy/setup.sh` that weaken the security of the host

Out of scope:

- Vulnerabilities in Nextcloud, Telegram, Piper or other third-party software (report those upstream)
- Problems that require prior access to the Pi or to the `.env` file

## Hardening Your Installation

Ludext has access to your calendar and notes, so treat the Pi as a sensitive device:

- **Protect `.env`**: it holds all your credentials. Restrict it to your user with `chmod 600 .env` and never commit it (it is already in `.gitignore`).
- **Use app passwords**: use a Nextcloud [app password](https://docs.nextcloud.com/server/latest/user_manual/en/session_management.html#managing-devices) instead of your main password, so you can revoke them at any time.
- **Keep your bot token secret**: anyone with the token can control the bot. If it leaks, revoke it with `/revoke` in @BotFather.
- **Don't expose Nextcloud over plain HTTP**: an `http://` URL is fine inside your home network, but use HTTPS or a VPN to access Nextcloud from outside.
- **Know what goes through Telegram**: briefings and bot replies pass through Telegram's servers, and bot chats are not end-to-end encrypted.
- **`nmap` capability**: `setup.sh` grants `cap_net_raw` to `nmap`, which lets any user on the Pi run raw network scans. On a shared machine, revert it with `sudo setcap -r "$(which nmap)"`.
- **Keep the system updated**: run `sudo apt update && sudo apt upgrade` regularly and update the Python packages in `~/ludext-env`.
