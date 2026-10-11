# ─────────────────────────────────────────────────────────
# gifts.py: Lista de ideas de regalo
# ─────────────────────────────────────────────────────────

import json
from .api import obtener_o_crear_nota, actualizar_nota, atomico

TITULO_NOTA = "Regalos"

def _cargar():
    nota = obtener_o_crear_nota(TITULO_NOTA, "[]")
    try:
        items = json.loads(nota["content"] or "[]")
    except json.JSONDecodeError:
        items = []
    return nota["id"], items

def _guardar(nota_id, items):
    actualizar_nota(nota_id, json.dumps(items, ensure_ascii=False, indent=2))

def listar_regalos():
    try:
        _, items = _cargar()
    except Exception as e:
        return f"⚠️ Error al leer la lista: {e}"

    if not items:
        return "💝 La lista de ideas de regalo está vacía.\nUsa /regalo <nombre> para añadir una idea."

    lineas = [f"💝 Ideas de regalo ({len(items)}):"]
    for item in items:
        url_line = f"\n    🔗 {item['url']}" if item.get("url") else ""
        lineas.append(f"\n  • {item['nombre']}{url_line}")
    return "\n".join(lineas)

@atomico
def añadir_regalo(args):
    """
    /regalo <nombre>
    /regalo <nombre> | <url>
    """
    if not args:
        return "⚠️ Uso: /regalo <nombre> o /regalo <nombre> | <url>"

    if "|" in args:
        partes = args.split("|", 1)
        nombre = partes[0].strip()
        url    = partes[1].strip()
    else:
        nombre = args.strip()
        url    = ""

    if not nombre:
        return "⚠️ Uso: /regalo <nombre> o /regalo <nombre> | <url>"

    try:
        nota_id, items = _cargar()

        if any(i["nombre"].lower() == nombre.lower() for i in items):
            return f"ℹ️ '{nombre}' ya está en la lista."

        items.append({"nombre": nombre, "url": url})
        _guardar(nota_id, items)
        return f"✅ Añadido a la lista de regalos: {nombre}"
    except Exception as e:
        return f"⚠️ Error al añadir: {e}"

@atomico
def borrar_regalo(nombre):
    """/regalado <nombre>"""
    if not nombre:
        return "⚠️ Uso: /regalado <nombre>"

    try:
        nota_id, items = _cargar()
        nombre_lower = nombre.lower()

        coincidencias = [i for i in items if nombre_lower in i["nombre"].lower()]

        if not coincidencias:
            return f"⚠️ No encontré '{nombre}' en la lista."
        if len(coincidencias) > 1:
            lista = "\n".join(f"  • {i['nombre']}" for i in coincidencias)
            return f"⚠️ Varias coincidencias, sé más específico:\n{lista}"

        items.remove(coincidencias[0])
        _guardar(nota_id, items)
        return f"🎀 ¡Comprado! Eliminado de la lista: {coincidencias[0]['nombre']}"
    except Exception as e:
        return f"⚠️ Error al eliminar: {e}"
