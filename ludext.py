# ─────────────────────────────────────────────────────────
# ludext.py — Script principal
# ─────────────────────────────────────────────────────────

import os
import sys
import requests
from datetime import datetime
from core.config import CONFIG
from core.sources import get_emails, get_calendar_events, get_tasks, get_news
from core.ai import build_briefing
from notes.medicine import resumen_medicinas

def send_telegram(message):
    """
    Envía el mensaje por Telegram.
    Si el mensaje supera 4000 caracteres lo divide en partes,
    ya que Telegram tiene un límite de 4096 por mensaje.
    """
    print("📱 Enviando por Telegram...")
    try:
        chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
        for chunk in chunks:
            resp = requests.post(
                f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendMessage",
                json={
                    "chat_id": CONFIG["telegram_chat_id"],
                    "text": chunk,
                },
                timeout=15,
            )
            resp.raise_for_status()
        print("   ✅ Enviado correctamente")
        return True
    except Exception as e:
        print(f"   ⚠️  Error Telegram: {e}")
        return False

def main():
    print("=" * 50)
    print(f"🌅 LUDEXT — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 50)

    # Paso 1: Recoger todos los datos del día
    emails    = get_emails()
    events    = get_calendar_events()
    tasks     = get_tasks()
    articles  = get_news()
    medicines = resumen_medicinas()

    # Paso 2: Construir el briefing con todos los datos
    briefing = build_briefing(emails, events, tasks, articles, medicines)

    # Paso 3 (opcional): guardar el briefing para depuración
    if "--debug" in sys.argv:
        debug_path = os.path.join(os.path.dirname(__file__), "ludext_briefing.txt")
        with open(debug_path, "w") as f:
            f.write(briefing)
        print(f"   📝 Briefing guardado en {debug_path}")

    # Paso 4: Enviar el briefing por Telegram
    send_telegram(briefing)

    print("=" * 50)
    print("✅ Ludext completado")

if __name__ == "__main__":
    main()