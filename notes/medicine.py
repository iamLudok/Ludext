# ─────────────────────────────────────────────────────────
# medicine.py — Control de medicación diaria en Nextcloud Notes
# ─────────────────────────────────────────────────────────

from datetime import date, timedelta
from .api import obtener_o_crear_nota, actualizar_nota, atomico

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

@atomico
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

# ── Gráfico de adherencia ─────────────────────────────────

# Colores de estado (icono + color en cada celda: el color nunca va solo)
_COL_TOMADA    = "#0ca30c"
_COL_OLVIDADA  = "#d03b3b"
_COL_PENDIENTE = "#fab219"
_COL_VACIA     = "#e1e0d9"
_SUPERFICIE    = "#fcfcfb"

_MESES_ABREV = ["ene", "feb", "mar", "abr", "may", "jun",
                "jul", "ago", "sep", "oct", "nov", "dic"]

def _estado_celda(nombre, dia, hoy, cada_dias, historial, primera_toma):
    """
    Estado de una medicina en un día:
    'tomada', 'pendiente' (hoy sin tomar), 'olvidada' o 'vacia' (sin pauta/datos)
    """
    if nombre in historial.get(str(dia), set()):
        return "tomada"
    if dia == hoy:
        return "pendiente"
    if primera_toma is None or dia < primera_toma:
        return "vacia"  # antes del primer registro no sabemos si tocaba
    if cada_dias == 1:
        return "olvidada"
    return "vacia"  # ciclos de varios días: sin toma no se puede saber si tocaba

def grafico_adherencia(n_dias=30):
    """
    Gráfico calendario de adherencia: filas = medicinas, columnas = últimos
    n_dias. Cada celda lleva icono además de color (✓ tomada, ✗ olvidada,
    ! pendiente hoy). Devuelve bytes PNG, o None si no hay medicinas.
    """
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Rectangle

    config = _cargar_config()
    if not config:
        return None
    _, historial = _cargar_historial()

    hoy  = date.today()
    dias = [hoy - timedelta(days=i) for i in range(n_dias - 1, -1, -1)]

    estilo = {
        "tomada":    (_COL_TOMADA,    "✓", "white"),
        "olvidada":  (_COL_OLVIDADA,  "✗", "white"),
        "pendiente": (_COL_PENDIENTE, "!", "#0b0b0b"),
        "vacia":     (_COL_VACIA,     "",  ""),
    }

    n_meds  = len(config)
    fig_w   = max(6.0, 0.28 * n_dias + 2.2)
    fig_h   = 1.6 + 0.45 * n_meds
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=150)
    fig.patch.set_facecolor(_SUPERFICIE)
    ax.set_facecolor(_SUPERFICIE)

    glyph_size = 7 if n_dias > 21 else 9

    for fila, med in enumerate(config):
        nombre = med["nombre"]
        fechas_toma = [date.fromisoformat(f) for f, t in historial.items() if nombre in t]
        primera     = min(fechas_toma) if fechas_toma else None

        tomadas = olvidadas = 0
        for col, dia in enumerate(dias):
            estado = _estado_celda(nombre, dia, hoy, med["cada_dias"], historial, primera)
            tomadas   += estado == "tomada"
            olvidadas += estado == "olvidada"

            color, glyph, ink = estilo[estado]
            ax.add_patch(Rectangle((col + 0.07, fila + 0.07), 0.86, 0.86,
                                   facecolor=color, edgecolor="none"))
            if glyph:
                ax.text(col + 0.5, fila + 0.5, glyph, ha="center", va="center",
                        color=ink, fontsize=glyph_size)

        # Porcentaje de adherencia sobre los días con pauta conocida
        if tomadas + olvidadas > 0:
            pct = round(100 * tomadas / (tomadas + olvidadas))
            ax.text(n_dias + 0.4, fila + 0.5, f"{pct}%", ha="left", va="center",
                    color="#52514e", fontsize=9)

    # Ejes: nombres de medicinas y días del mes
    ax.set_xlim(0, n_dias + 2.2)
    ax.set_ylim(n_meds, 0)  # primera medicina arriba
    ax.set_yticks([f + 0.5 for f in range(n_meds)])
    ax.set_yticklabels([m["nombre"] for m in config], color="#52514e", fontsize=9)

    paso   = 2 if n_dias > 21 else 1
    xticks, xlabels = [], []
    for col, dia in enumerate(dias):
        # El día 1 siempre lleva etiqueta para que se vea el cambio de mes
        if dia != hoy and dia.day != 1 and col % paso != 0:
            continue
        if dia == hoy:
            etiqueta = "hoy"
        elif dia.day == 1 or col == 0:
            etiqueta = f"{dia.day} {_MESES_ABREV[dia.month - 1]}"
        else:
            etiqueta = str(dia.day)
        xticks.append(col + 0.5)
        xlabels.append(etiqueta)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels, color="#898781", fontsize=7)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_title(f"Medicinas — últimos {n_dias} días",
                 color="#0b0b0b", fontsize=13, pad=12, loc="left")

    leyenda = [
        Patch(facecolor=_COL_TOMADA,    label="✓ Tomada"),
        Patch(facecolor=_COL_OLVIDADA,  label="✗ Olvidada"),
        Patch(facecolor=_COL_PENDIENTE, label="! Pendiente hoy"),
        Patch(facecolor=_COL_VACIA,     label="Sin pauta / sin datos"),
    ]
    fig.legend(handles=leyenda, loc="lower center", ncol=4, frameon=False,
               fontsize=8, labelcolor="#52514e")

    fig.tight_layout(rect=(0, 0.08, 1, 1))
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()