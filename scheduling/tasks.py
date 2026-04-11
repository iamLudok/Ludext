# ─────────────────────────────────────────────────────────
# tasks.py — Tareas en Nextcloud Decs
# ─────────────────────────────────────────────────────────

import uuid
from datetime import datetime
from icalendar import Calendar, Todo, vText
from . import get_calendars

def fetch():
    """
    Devuelve las tareas pendientes como lista de dicts
    Formato: [{"title": ..., "due": ...}]
    """
    tasks = []
    try:
        for cal in get_calendars():
            try:
                for todo in cal.todos():
                    comp    = todo.icalendar_component
                    summary = str(comp.get("SUMMARY", ""))
                    if not summary:
                        continue
                    due     = comp.get("DUE")
                    due_str = ""
                    if due and hasattr(due.dt, "strftime"):
                        due_str = due.dt.strftime("%d/%m")
                    tasks.append({"title": summary, "due": due_str})
            except Exception:
                pass
    except Exception:
        pass
    return tasks[:20]

def _buscar(titulo):
    """
    Busca tareas cuyo título contenga el texto (sin distinguir mayúsculas)
    Devuelve lista de tuplas (objeto_todo, título_completo)
    """
    titulo_lower = titulo.lower()
    encontradas  = []
    for cal in get_calendars():
        try:
            for todo in cal.todos():
                summary = str(todo.icalendar_component.get("SUMMARY", ""))
                if titulo_lower in summary.lower():
                    encontradas.append((todo, summary))
        except Exception:
            pass
    return encontradas

def listar_tareas():
    """
    Devuelve un texto con todas las tareas pendientes
    """
    try:
        tasks = fetch()
        if not tasks:
            return "✅ No tienes tareas pendientes."
        lineas = [
            f"• {t['title']}" + (f" ({t['due']})" if t["due"] else "")
            for t in tasks
        ]
        return f"📋 Tareas pendientes ({len(tasks)}):\n" + "\n".join(lineas)
    except Exception as e:
        return f"⚠️ Error al listar tareas: {e}"

def crear_tarea(titulo, fecha=None):
    """
    Crea una nueva tarea en el primer calendario de Nextcloud
    fecha es un objeto date opcional para la fecha de vencimiento
    """
    try:
        calendars = get_calendars()
        if not calendars:
            return False, "⚠️ No se encontró ningún calendario."

        ical = Calendar()
        todo = Todo()
        todo.add("uid",     str(uuid.uuid4()) + "@ludext")
        todo.add("summary", titulo)
        todo.add("status",  "NEEDS-ACTION")
        todo.add("created", datetime.now())
        if fecha:
            todo.add("due", fecha)
        ical.add_component(todo)
        calendars[0].save_todo(ical.to_ical().decode())

        fecha_str = f" para el {fecha.strftime('%d/%m')}" if fecha else ""
        return True, f"✅ Tarea creada{fecha_str}: {titulo}"
    except Exception as e:
        return False, f"⚠️ Error al crear tarea: {e}"

def borrar_tarea(titulo):
    """
    Elimina la tarea que coincida con el título
    Si hay varias coincidencias, pide que sea más específico
    """
    try:
        encontradas = _buscar(titulo)
        if not encontradas:
            return False, f"⚠️ No encontré ninguna tarea con '{titulo}'"
        if len(encontradas) > 1:
            lista = "\n".join(f"  • {s}" for _, s in encontradas)
            return False, f"⚠️ Varias tareas coinciden, sé más específico:\n{lista}"
        todo, summary = encontradas[0]
        todo.delete()
        return True, f"🗑️ Tarea eliminada: {summary}"
    except Exception as e:
        return False, f"⚠️ Error al borrar tarea: {e}"

def editar_tarea(titulo_viejo, titulo_nuevo):
    """
    Renombra una tarea existente
    Busca por título_viejo y lo sustituye por título_nuevo
    """
    try:
        encontradas = _buscar(titulo_viejo)
        if not encontradas:
            return False, f"⚠️ No encontré ninguna tarea con '{titulo_viejo}'"
        if len(encontradas) > 1:
            lista = "\n".join(f"  • {s}" for _, s in encontradas)
            return False, f"⚠️ Varias tareas coinciden, sé más específico:\n{lista}"
        todo, summary = encontradas[0]
        todo.icalendar_component["SUMMARY"] = vText(titulo_nuevo)
        todo.save()
        return True, f"✏️ Tarea renombrada:\n  Antes: {summary}\n  Ahora: {titulo_nuevo}"
    except Exception as e:
        return False, f"⚠️ Error al editar tarea: {e}"