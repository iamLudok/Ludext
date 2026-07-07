# ─────────────────────────────────────────────────────────
# ai.py — Formateador del briefing diario
# ─────────────────────────────────────────────────────────

from datetime import datetime, timezone

_DIAS   = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES  = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
           "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

def _fecha_es(dt):
    return f"{_DIAS[dt.weekday()]} {dt.day} de {_MESES[dt.month - 1]} de {dt.year}"


def _seccion_correos(emails):
    if not emails:
        return ["📧 Correos: Sin correos no leídos."]
    lines = ["📧 Correos no leídos:"]
    for e in emails[:10]:
        lines.append(f"  • {e['from'][:50]} — {e['subject'][:80]}")
    return lines

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

def _seccion_noticias(articles):
    if not articles:
        return ["📰 Noticias: Sin artículos nuevos."]
    lines = ["📰 Noticias:"]
    for a in articles[:15]:
        feed = f"[{a['feed']}] " if a['feed'] else ""
        if a.get("date"):
            dt      = datetime.fromtimestamp(a["date"], tz=timezone.utc).astimezone()
            fecha   = f"{dt.day} {_MESES[dt.month - 1]}"
        else:
            fecha = ""
        header = f"  • {feed}{fecha} — {a['title']}" if fecha else f"  • {feed}{a['title']}"
        lines.append(header)
        if a.get("summary"):
            lines.append(f"    {a['summary'][:150]}")
    return lines


def build_briefing(emails, events, tasks, articles, medicinas=""):
    sections  = [f"🌅 Ludext — {_fecha_es(datetime.now())}", ""]
    sections += _seccion_correos(emails) + [""]
    sections += _seccion_agenda(events)  + [""]
    sections += _seccion_tareas(tasks)   + [""]
    if medicinas:
        sections += [medicinas, ""]
    sections += _seccion_noticias(articles)
    return "\n".join(sections)