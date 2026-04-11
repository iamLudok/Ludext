# ─────────────────────────────────────────────────────────
# ai.py — Prompt y consulta a Ollama
# ─────────────────────────────────────────────────────────

from datetime import datetime
import requests
from .config import CONFIG

def _seccion_correos(emails):
    if not emails:
        return ["CORREOS: Sin correos no leídos."]
    lines = ["CORREOS NO LEÍDOS:"]
    for e in emails[:10]:
        lines.append(f"- De: {e['from'][:50]} | Asunto: {e['subject'][:80]}")
        if e['body']:
            lines.append(f"  Contenido: {e['body'][:200]}")
    return lines

def _seccion_agenda(events):
    if not events:
        return ["AGENDA: Sin eventos próximos."]
    lines = ["AGENDA DE HOY Y MAÑANA:"]
    for ev in events:
        hora = f" a las {ev['time']}" if ev['time'] else ""
        lines.append(f"- {ev['title']}{hora}")
    return lines

def _seccion_tareas(tasks):
    if not tasks:
        return ["TAREAS: Sin tareas pendientes."]
    lines = ["TAREAS PENDIENTES:"]
    for t in tasks[:10]:
        vence = f" (vence {t['due']})" if t['due'] else ""
        lines.append(f"- {t['title']}{vence}")
    return lines

def _seccion_noticias(articles):
    if not articles:
        return ["NOTICIAS: Sin artículos nuevos."]
    lines = ["NOTICIAS RECIENTES (feeds del usuario):"]
    for a in articles[:20]:
        lines.append(f"- [{a['feed']}] {a['title']}: {a['summary'][:150]}")
    return lines

_INSTRUCCIONES = """INSTRUCCIONES PARA EL RESUMEN:
1. 📧 CORREOS: Lista todos los correos recibidos con remitente y asunto. Si no hay, dilo.
2. 📅 AGENDA: Lista todos los eventos de hoy y mañana. Si no hay, dilo.
3. ✅ TAREAS: Lista todas las tareas pendientes. Si no hay, dilo.
4. 💊 MEDICINAS: Indica qué medicinas hay que tomar hoy y a qué hora.
5. 📰 NOTICIAS: Destaca las noticias más relevantes sobre economía, España y País Vasco.

Sé conciso. No inventes información que no esté en los datos."""

def build_prompt(emails, events, tasks, articles, medicinas=""):
    """
    Construye el prompt completo con todos los datos del día
    """
    today_str = datetime.now().strftime("%A %d de %B de %Y")

    sections = [
        f"Hoy es {today_str}. El usuario vive en el País Vasco, España.",
        "Eres un asistente personal que genera un briefing matutino conciso y útil.",
        "Responde SIEMPRE en español. Sé directo, usa listas cortas y emojis para separar secciones.",
        "IMPORTANTE: Menciona TODOS los datos que se te dan. No omitas nada por considerarlo poco importante.",
        "---",
        *_seccion_correos(emails),
        "---",
        *_seccion_agenda(events),
        "---",
        *_seccion_tareas(tasks),
        "---",
    ]

    if medicinas:
        sections += ["MEDICINAS DE HOY:", medicinas, "---"]

    sections += [
        *_seccion_noticias(articles),
        "---",
        _INSTRUCCIONES,
    ]

    return "\n".join(sections)

def ask_ollama(prompt):
    """
    Envía el prompt a Ollama y devuelve el texto generado
    temperature 0.3 para respuestas consistentes, timeout 900s para CPU
    """
    print(f"🤖 Consultando Ollama ({CONFIG['ollama_model']})...")
    try:
        resp = requests.post(
            f"{CONFIG['ollama_url']}/api/generate",
            json={
                "model":   CONFIG["ollama_model"],
                "prompt":  prompt,
                "stream":  False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 600,
                },
            },
            timeout=900,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"   ⚠️  Error en Ollama: {e}")
        return None