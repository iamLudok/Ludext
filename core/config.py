# ─────────────────────────────────────────────────────────
# config.py: Lee las credenciales del archivo .env
# ─────────────────────────────────────────────────────────

import os
from dotenv import load_dotenv

# Carga las variables del fichero .env
load_dotenv()

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG = {
    # Nextcloud
    "nextcloud_url":        os.getenv("NEXTCLOUD_URL"),
    "nextcloud_user":       os.getenv("NEXTCLOUD_USER"),
    "nextcloud_password":   os.getenv("NEXTCLOUD_PASSWORD"),
    "nextcloud_caldav_url": os.getenv("NEXTCLOUD_CALDAV_URL"),

    # Telegram
    "telegram_token":       os.getenv("TELEGRAM_TOKEN"),
    "telegram_chat_id":     os.getenv("TELEGRAM_CHAT_ID"),

    # Piper (noticias en audio): ruta al modelo de voz .onnx
    "piper_voice":          os.getenv("PIPER_VOICE",
                                      os.path.join(_RAIZ, "voices", "es_ES-davefx-medium.onnx")),
}
