# ─────────────────────────────────────────────────────────
# __main__.py — Entry point: polling de Telegram y arranque de hilos
# ─────────────────────────────────────────────────────────

import time
import threading
from datetime import datetime
import requests
from core.config import CONFIG
from .handlers import send, handle
from .background import _check_alertas, _check_medicinas, _check_sistema

BASE_URL = f"https://api.telegram.org/bot{CONFIG['telegram_token']}"
CHAT_ID  = str(CONFIG["telegram_chat_id"])

def get_updates(offset=None):
    """Obtiene mensajes nuevos de Telegram (long polling de 30s)."""
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        resp = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=35)
        return resp.json().get("result", [])
    except Exception:
        return []

def main():
    print("=" * 50)
    print(f"🤖 Bot Ludext iniciado — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("Esperando comandos de Telegram...")
    print("=" * 50)

    threading.Thread(target=_check_alertas,   daemon=True).start()
    print("⏰ Hilo de alertas de calendario activo")

    threading.Thread(target=_check_medicinas, daemon=True).start()
    print("💊 Hilo de avisos de medicinas activo")

    threading.Thread(target=_check_sistema,   daemon=True).start()
    print("🖥️ Hilo de monitor de sistema activo")

    offset = None
    while True:
        updates = get_updates(offset)

        for update in updates:
            offset  = update["update_id"] + 1
            message = update.get("message", {})
            chat_id = str(message.get("chat", {}).get("id", ""))
            text    = message.get("text", "")

            if chat_id != CHAT_ID:
                continue

            if not text.startswith("/"):
                continue

            print(f"   → {text}")
            response = handle(text)
            if response:
                for i in range(0, len(response), 4000):
                    send(response[i:i+4000])

        if not updates:
            time.sleep(1)

if __name__ == "__main__":
    main()