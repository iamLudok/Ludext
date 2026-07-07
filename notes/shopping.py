# ─────────────────────────────────────────────────────────
# shopping.py — Lista de la compra en Nextcloud Notes
# ─────────────────────────────────────────────────────────

from .api import obtener_o_crear_nota, actualizar_nota, atomico

TITULO_NOTA = "Lista de la compra"

def _cargar():
    """
    Devuelve (nota_id, lista_de_items)
    """
    nota  = obtener_o_crear_nota(TITULO_NOTA)
    items = [
        linea.lstrip("- ").strip()
        for linea in nota["content"].splitlines()
        if linea.strip()
    ]
    return nota["id"], items

def _guardar(nota_id, items):
    """
    Guarda la lista actualizada en la nota
    """
    contenido = "\n".join(f"- {item}" for item in items)
    actualizar_nota(nota_id, contenido)

def listar():
    """
    Devuelve el texto con todos los artículos de la lista
    """
    try:
        _, items = _cargar()
        if not items:
            return "🛒 La lista de la compra está vacía."
        lineas = [f"  • {item}" for item in items]
        return f"🛒 Lista de la compra ({len(items)}):\n" + "\n".join(lineas)
    except Exception as e:
        return f"⚠️ Error al leer la lista: {e}"

@atomico
def añadir(articulo):
    """
    Añade un artículo a la lista si no estaba ya
    """
    try:
        nota_id, items = _cargar()
        if any(i.lower() == articulo.lower() for i in items):
            return f"ℹ️ '{articulo}' ya está en la lista."
        items.append(articulo)
        _guardar(nota_id, items)
        return f"✅ Añadido: {articulo}"
    except Exception as e:
        return f"⚠️ Error al añadir: {e}"

@atomico
def comprado(articulo):
    """
    Elimina un artículo de la lista
    Busca por coincidencia parcial insensible a mayúsculas
    """
    try:
        nota_id, items = _cargar()
        articulo_lower = articulo.lower()
        coincidencias  = [i for i in items if articulo_lower in i.lower()]

        if not coincidencias:
            return f"⚠️ No encontré '{articulo}' en la lista."
        if len(coincidencias) > 1:
            lista = "\n".join(f"  • {i}" for i in coincidencias)
            return f"⚠️ Varias coincidencias, sé más específico:\n{lista}"

        items.remove(coincidencias[0])
        _guardar(nota_id, items)
        return f"🗑️ Eliminado: {coincidencias[0]}"
    except Exception as e:
        return f"⚠️ Error al eliminar: {e}"

@atomico
def vaciar():
    """
    Vacía la lista completa
    """
    try:
        nota_id, _ = _cargar()
        _guardar(nota_id, [])
        return "🗑️ Lista vaciada."
    except Exception as e:
        return f"⚠️ Error al vaciar la lista: {e}"