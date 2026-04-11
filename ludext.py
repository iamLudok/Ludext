# ─────────────────────────────────────────────────────────
# ludext.py — Script principal
# ─────────────────────────────────────────────────────────

import sys
import requests
from datetime import datetime
from core.config import CONFIG
from core.sources import get_emails, get_calendar_events, get_tasks, get_news
from core.ai import build_prompt, ask_ollama
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

    # Paso 2: Construir el prompt con todos los datos
    prompt = build_prompt(emails, events, tasks, articles, medicines)

    # Paso 3 (opcional): guardar el prompt para depuración
    if "--debug" in sys.argv:
        with open("/tmp/ludext_prompt.txt", "w") as f:
            f.write(prompt)
        print("   📝 Prompt guardado en /tmp/ludext_prompt.txt")

    # Paso 4: Consultar la IA y obtener el resumen
    summary = ask_ollama(prompt)
    if not summary:
        summary = "⚠️ No se pudo generar el resumen con IA. Revisa que Ollama esté corriendo."

    # Paso 5: Enviar el resumen por Telegram
    header = f"🌅 Ludext — {datetime.now().strftime('%A %d/%m/%Y')}\n\n"
    send_telegram(header + summary)

    print("=" * 50)
    print("✅ Ludext completado")

if __name__ == "__main__":
    main()