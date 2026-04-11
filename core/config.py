# ─────────────────────────────────────────────────────────
# config.py — Lee las credenciales del archivo .env
# ─────────────────────────────────────────────────────────

import os
from dotenv import load_dotenv

# Carga las variables del fichero .env
load_dotenv()

CONFIG = {
    # Gmail
    "gmail_user":           os.getenv("GMAIL_USER"),
    "gmail_app_password":   os.getenv("GMAIL_APP_PASSWORD"),

    # Nextcloud
    "nextcloud_url":        os.getenv("NEXTCLOUD_URL"),
    "nextcloud_user":       os.getenv("NEXTCLOUD_USER"),
    "nextcloud_password":   os.getenv("NEXTCLOUD_PASSWORD"),
    "nextcloud_caldav_url": os.getenv("NEXTCLOUD_CALDAV_URL"),

    # Ollama
    "ollama_url":           os.getenv("OLLAMA_URL"),
    "ollama_model":         os.getenv("OLLAMA_MODEL"),

    # Telegram
    "telegram_token":       os.getenv("TELEGRAM_TOKEN"),
    "telegram_chat_id":     os.getenv("TELEGRAM_CHAT_ID"),
}