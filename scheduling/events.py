# ─────────────────────────────────────────────────────────
# events.py — Eventos en Nextcloud Calendar
# ─────────────────────────────────────────────────────────

import uuid
from datetime import datetime, timedelta
from icalendar import Calendar, Event, vText
from . import get_calendars

def fetch(start=None, end=None):
    """
    Devuelve eventos en el rango dado como lista de dicts
    Por defecto devuelve los de hoy y mañana
    Formato: [{"title": ..., "time": ..., "calendar": ...}]
    """
    if start is None:
        today = datetime.now().date()
        start = datetime.combine(today, datetime.min.time())
        end   = datetime.combine(today + timedelta(days=2), datetime.min.time())

    events = []
    try:
        for cal in get_calendars():
            try:
                for event in cal.search(start=start, end=end, event=True, expand=True):
                    comp     = event.icalendar_component
                    summary  = str(comp.get("SUMMARY", "Sin título"))
                    dtstart  = comp.get("DTSTART")
                    time_str = ""
                    if dtstart:
                        dt = dtstart.dt
                        if hasattr(dt, "hour"):
                            time_str = dt.strftime("%H:%M")
                        elif hasattr(dt, "strftime"):
                            time_str = str(dt)
                    events.append({"title": summary, "time": time_str, "calendar": str(cal.name)})
            except Exception:
                pass
    except Exception:
        pass
    return events

def _buscar(titulo):
    """
    Busca eventos en los próximos 365 días cuyo título contenga el texto
    Devuelve lista de tuplas (objeto_event, título_completo)
    """
    titulo_lower = titulo.lower()
    encontrados  = []
    ahora        = datetime.now()

    for cal in get_calendars():
        try:
            results = cal.search(
                start=ahora,
                end=ahora + timedelta(days=365),
                event=True,
                expand=True,
            )
            for event in results:
                summary = str(event.icalendar_component.get("SUMMARY", ""))
                if titulo_lower in summary.lower():
                    encontrados.append((event, summary))
        except Exception:
            pass

    return encontrados

def crear_evento(titulo, fecha, hora=None):
    """
    Crea un evento en el calendario
    Sin hora se crea como día completo, con hora dura 1 hora por defecto
    """
    try:
        calendars = get_calendars()
        if not calendars:
            return False, "⚠️ No se encontró ningún calendario."

        ical  = Calendar()
        event = Event()
        event.add("uid",     str(uuid.uuid4()) + "@ludext")
        event.add("summary", titulo)

        if hora:
            inicio = datetime.combine(fecha, hora)
            event.add("dtstart", inicio)
            event.add("dtend",   inicio + timedelta(hours=1))
            hora_str = f" a las {hora.strftime('%H:%M')}"
        else:
            event.add("dtstart", fecha)
            event.add("dtend",   fecha + timedelta(days=1))
            hora_str = ""

        ical.add_component(event)
        calendars[0].save_event(ical.to_ical().decode())
        return True, f"✅ Evento creado: {titulo} el {fecha.strftime('%d/%m')}{hora_str}"
    except Exception as e:
        return False, f"⚠️ Error al crear evento: {e}"

def borrar_evento(titulo):
    """
    Elimina el próximo evento que coincida con el título
    Si hay varias coincidencias, pide más precisión
    """
    try:
        encontrados = _buscar(titulo)
        if not encontrados:
            return False, f"⚠️ No encontré ningún evento con '{titulo}' en los próximos 365 días"
        if len(encontrados) > 1:
            lista = "\n".join(f"  • {s}" for _, s in encontrados)
            return False, f"⚠️ Varios eventos coinciden, sé más específico:\n{lista}"
        event, summary = encontrados[0]
        event.delete()
        return True, f"🗑️ Evento eliminado: {summary}"
    except Exception as e:
        return False, f"⚠️ Error al borrar evento: {e}"

def editar_evento(titulo_viejo, titulo_nuevo):
    """
    Renombra el próximo evento que coincida con el título
    """
    try:
        encontrados = _buscar(titulo_viejo)
        if not encontrados:
            return False, f"⚠️ No encontré ningún evento con '{titulo_viejo}' en los próximos 365 días"
        if len(encontrados) > 1:
            lista = "\n".join(f"  • {s}" for _, s in encontrados)
            return False, f"⚠️ Varios eventos coinciden, sé más específico:\n{lista}"
        event, summary = encontrados[0]
        event.icalendar_component["SUMMARY"] = vText(titulo_nuevo)
        event.save()
        return True, f"✏️ Evento renombrado:\n  Antes: {summary}\n  Ahora: {titulo_nuevo}"
    except Exception as e:
        return False, f"⚠️ Error al editar evento: {e}"