# ─────────────────────────────────────────────────────────
# medicine.py — Control de medicación diaria en Nextcloud Notes
# ─────────────────────────────────────────────────────────

from datetime import date
from .api import obtener_o_crear_nota, actualizar_nota

TITULO_CONFIG    = "Medicinas Config"
TITULO_HISTORIAL = "Medicinas"

def _cargar_config():
    """
    Lee la nota "Medicinas Config" y devuelve la lista de medicinas
    Formato de cada línea: nombre,cada_dias,hora_toma,aviso1,aviso2,...
    """
    nota = obtener_o_crear_nota(
        TITULO_CONFIG,
        contenido_inicial=(
            "# Una medicina por línea:\n"
            "# nombre,cada_dias,hora_toma,aviso1,aviso2,...\n"
        ),
    )
    medicinas = []
    for linea in nota["content"].splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        partes = [p.strip() for p in linea.split(",")]
        if len(partes) < 3:
            continue
        medicinas.append({
            "nombre":    partes[0],
            "cada_dias": int(partes[1]),
            "hora":      partes[2],
            "avisos":    partes[3:],
        })
    return medicinas

def _cargar_historial():
    """
    Lee la nota "Medicinas" y devuelve (nota_id, historial)
    historial = { "2026-04-10": {"Medicina A", "Medicina B"}, ... }
    """
    nota      = obtener_o_crear_nota(TITULO_HISTORIAL)
    historial = {}
    for linea in nota["content"].splitlines():
        linea = linea.strip()
        if not linea:
            continue
        partes  = linea.split(",")
        fecha   = partes[0]
        tomadas = {p.strip() for p in partes[1:] if p.strip()}
        historial[fecha] = tomadas
    return nota["id"], historial

def _guardar_historial(nota_id, historial):
    """
    Serializa el historial y lo guarda en la nota
    """
    lineas = [
        f"{fecha},{','.join(sorted(tomadas))}"
        for fecha, tomadas in sorted(historial.items())
        if tomadas
    ]
    actualizar_nota(nota_id, "\n".join(lineas))

def _ultima_toma(nombre, historial):
    """
    Busca la última fecha en que se tomó una medicina
    """
    for fecha_str in sorted(historial.keys(), reverse=True):
        if nombre in historial[fecha_str]:
            return date.fromisoformat(fecha_str)
    return None

def _toca_hoy(medicina, historial):
    """
    Determina si una medicina corresponde tomarse hoy
    Para ciclos de varios días lo calcula desde el historial
    """
    if medicina["cada_dias"] == 1:
        return True
    ultima = _ultima_toma(medicina["nombre"], historial)
    if not ultima:
        return True
    return (date.today() - ultima).days % medicina["cada_dias"] == 0

def medicinas_de_hoy():
    """
    Devuelve las medicinas que corresponden hoy con su estado
    Formato: [{"nombre": ..., "hora": ..., "avisos": [...], "tomada": False}]
    """
    hoy          = str(date.today())
    _, historial = _cargar_historial()
    tomadas_hoy  = historial.get(hoy, set())
    return [
        {
            "nombre": m["nombre"],
            "hora":   m["hora"],
            "avisos": m["avisos"],
            "tomada": m["nombre"] in tomadas_hoy,
        }
        for m in _cargar_config()
        if _toca_hoy(m, historial)
    ]

def marcar_tomada(nombre):
    """
    Marca una medicina como tomada hoy
    Devuelve (ok, mensaje)
    """
    hoy                = str(date.today())
    config             = _cargar_config()
    nota_id, historial = _cargar_historial()

    medicina = next((m for m in config if m["nombre"].lower() == nombre.lower()), None)
    if not medicina:
        nombres = ", ".join(m["nombre"] for m in config)
        return False, f"⚠️ No conozco esa medicina. Opciones: {nombres}"

    if not _toca_hoy(medicina, historial):
        return False, f"ℹ️ Las {medicina['nombre']} no tocan hoy."

    tomadas_hoy = historial.get(hoy, set())
    if medicina["nombre"] in tomadas_hoy:
        return False, f"ℹ️ Las {medicina['nombre']} ya estaban marcadas hoy."

    tomadas_hoy.add(medicina["nombre"])
    historial[hoy] = tomadas_hoy
    _guardar_historial(nota_id, historial)
    return True, f"✅ {medicina['nombre']} marcadas como tomadas."

def resumen_medicinas():
    """
    Texto con el estado de las medicinas de hoy
    Usado en el briefing matutino
    """
    medicinas = medicinas_de_hoy()
    if not medicinas:
        return "💊 No tienes medicinas hoy."
    lineas = ["💊 Medicinas de hoy:"]
    for m in medicinas:
        estado = "✅" if m["tomada"] else "⏳"
        lineas.append(f"  {estado} {m['nombre']} — {m['hora']}")
    return "\n".join(lineas)

def pendientes_en_hora(hora_actual):
    """
    Devuelve medicinas no tomadas que tienen hora_actual en sus avisos
    """
    return [
        m["nombre"]
        for m in medicinas_de_hoy()
        if not m["tomada"] and hora_actual in m["avisos"]
    ]