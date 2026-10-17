# ─────────────────────────────────────────────────────────
# ai.py: Formateador del briefing diario
# ─────────────────────────────────────────────────────────

from datetime import datetime

_DIAS   = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES  = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
           "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

def _fecha_es(dt):
    return f"{_DIAS[dt.weekday()]} {dt.day} de {_MESES[dt.month - 1]} de {dt.year}"


def _seccion_agenda(events):
    if not events:
        return ["📅 Agenda: Sin eventos próximos."]
    lines = ["📅 Agenda de hoy y mañana:"]
    for ev in events:
        hora = f" a las {ev['time']}" if ev['time'] else ""
        lines.append(f"  • {ev['title']}{hora}")
    return lines

def _seccion_tareas(tasks):
    if not tasks:
        return ["✅ Tareas: Sin tareas pendientes."]
    lines = ["✅ Tareas pendientes:"]
    for t in tasks[:10]:
        vence = f" (vence {t['due']})" if t['due'] else ""
        lines.append(f"  • {t['title']}{vence}")
    return lines

def _seccion_noticias(articles, con_audio=False):
    """
    Solo titulares (máx. 5): el detalle va en la nota de voz
    """
    if not articles:
        return ["📰 Noticias: Sin artículos nuevos."]
    cabecera = "📰 Noticias (escúchalas en el audio 🎧):" if con_audio else "📰 Noticias:"
    lines = [cabecera]
    for a in articles[:5]:
        feed = f"[{a['feed']}] " if a['feed'] else ""
        lines.append(f"  • {feed}{a['title']}")
    if len(articles) > 5:
        lines.append(f"  … y {len(articles) - 5} más")
    return lines


def build_briefing(events, tasks, articles, medicinas="", con_audio=False):
    sections  = [f"🌅 Ludext: {_fecha_es(datetime.now())}", ""]
    sections += _seccion_agenda(events)  + [""]
    sections += _seccion_tareas(tasks)   + [""]
    if medicinas:
        sections += [medicinas, ""]
    sections += _seccion_noticias(articles, con_audio)
    return "\n".join(sections)
