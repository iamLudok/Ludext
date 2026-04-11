# ─────────────────────────────────────────────────────────
# wishlist.py — Lista de deseos en Nextcloud Notes
# ─────────────────────────────────────────────────────────

import json
from .api import obtener_o_crear_nota, actualizar_nota

TITULO_NOTA = "Wishlist"

def _cargar():
    """
    Devuelve (nota_id, lista_de_productos)
    """
    nota = obtener_o_crear_nota(TITULO_NOTA, "[]")
    try:
        productos = json.loads(nota["content"] or "[]")
    except json.JSONDecodeError:
        productos = []
    return nota["id"], productos

def _guardar(nota_id, productos):
    """
    Guarda la lista de productos en la nota como JSON formateado
    """
    actualizar_nota(nota_id, json.dumps(productos, ensure_ascii=False, indent=2))

def listar_wish():
    """
    Devuelve un texto con la wishlist formateada
    """
    try:
        _, productos = _cargar()
    except Exception as e:
        return f"⚠️ Error al leer la wishlist: {e}"

    if not productos:
        return "🎁 Tu wishlist está vacía. Usa /wish <nombre> | <url> para añadir."

    lineas = [f"🎁 Wishlist ({len(productos)} productos):"]
    for p in productos:
        lineas.append(f"\n  • {p['nombre']}\n    {p['url']}")
    return "\n".join(lineas)

def añadir_wish(args):
    """
    /wish <nombre> | <url>
    """
    if "|" not in args:
        return "⚠️ Uso: /wish <nombre> | <url>"

    partes = args.split("|", 1)
    nombre = partes[0].strip()
    url    = partes[1].strip()

    if not nombre or not url:
        return "⚠️ Uso: /wish <nombre> | <url>"

    try:
        nota_id, productos = _cargar()

        if any(p["nombre"].lower() == nombre.lower() for p in productos):
            return f"ℹ️ '{nombre}' ya está en tu wishlist."

        productos.append({"nombre": nombre, "url": url})
        _guardar(nota_id, productos)
        return f"✅ Añadido a la wishlist: {nombre}"
    except Exception as e:
        return f"⚠️ Error al añadir: {e}"

def borrar_wish(nombre):
    """
    /unwish <nombre>
    """
    if not nombre:
        return "⚠️ Uso: /unwish <nombre>"

    try:
        nota_id, productos = _cargar()
        nombre_lower = nombre.lower()

        coincidencias = [p for p in productos if nombre_lower in p["nombre"].lower()]

        if not coincidencias:
            return f"⚠️ No encontré '{nombre}' en tu wishlist."
        if len(coincidencias) > 1:
            lista = "\n".join(f"  • {p['nombre']}" for p in coincidencias)
            return f"⚠️ Varias coincidencias, sé más específico:\n{lista}"

        productos.remove(coincidencias[0])
        _guardar(nota_id, productos)
        return f"🗑️ Eliminado: {coincidencias[0]['nombre']}"
    except Exception as e:
        return f"⚠️ Error al eliminar: {e}"