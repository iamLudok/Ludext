# ─────────────────────────────────────────────────────────
# car.py: Gastos del coche en Nextcloud Notes
# ─────────────────────────────────────────────────────────

import io
from datetime import date, datetime
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .api import obtener_o_crear_nota, actualizar_nota, atomico

TITULO_NOTA = "Gastos del coche"

CATEGORIAS = ("gasolina", "taller", "recambio")
COLORES    = {"gasolina": "#2a78d6", "taller": "#1baf7a", "recambio": "#eda100"}
ETIQUETAS  = {"gasolina": "Gasolina", "taller": "Taller", "recambio": "Recambios"}
SUPERFICIE = "#fcfcfb"

def _cargar():
    """
    Devuelve (nota_id, lista_de_líneas)
    """
    nota   = obtener_o_crear_nota(TITULO_NOTA)
    lineas = [l.strip() for l in nota["content"].splitlines() if l.strip()]
    return nota["id"], lineas

def _guardar(nota_id, lineas):
    """
    Guarda las líneas en la nota
    """
    actualizar_nota(nota_id, "\n".join(lineas))

def _parsear_lineas(lineas):
    """
    Convierte las líneas CSV en lista de dicts
    Devuelve solo las que se pueden parsear correctamente
    """
    gastos = []
    for linea in lineas:
        partes = linea.split(",")
        try:
            fecha = partes[0]
            tipo  = partes[1]
            if tipo == "gasolina":
                gastos.append({
                    "fecha":    fecha,
                    "tipo":     "gasolina",
                    "litros":   float(partes[2]),
                    "precio_l": float(partes[3]),
                    "total":    float(partes[4]),
                })
            elif tipo in ("taller", "recambio"):
                # La descripción puede contener comas: el importe es
                # siempre el último campo y la descripción todo lo demás
                gastos.append({
                    "fecha":       fecha,
                    "tipo":        tipo,
                    "descripcion": ",".join(partes[2:-1]),
                    "total":       float(partes[-1]),
                })
        except (IndexError, ValueError):
            pass
    return gastos

@atomico
def registrar_gasolina(litros, precio_litro):
    """
    Registra un repostaje
    Calcula el importe total automáticamente
    """
    try:
        nota_id, lineas = _cargar()
        total  = round(litros * precio_litro, 2)
        hoy    = str(date.today())
        lineas.append(f"{hoy},gasolina,{litros},{precio_litro},{total}")
        _guardar(nota_id, lineas)
        return True, f"⛽ Gasolina registrada: {litros}L × {precio_litro}€/L = {total}€"
    except Exception as e:
        return False, f"⚠️ Error: {e}"

@atomico
def registrar_taller(descripcion, importe):
    """
    Registra un gasto en el taller
    """
    try:
        nota_id, lineas = _cargar()
        hoy = str(date.today())
        lineas.append(f"{hoy},taller,{descripcion},{importe}")
        _guardar(nota_id, lineas)
        return True, f"🔧 Taller registrado: {descripcion} ({importe}€)"
    except Exception as e:
        return False, f"⚠️ Error: {e}"

@atomico
def registrar_recambio(descripcion, importe):
    """
    Registra una compra personal (recambio, accesorio, etc.)
    """
    try:
        nota_id, lineas = _cargar()
        hoy = str(date.today())
        lineas.append(f"{hoy},recambio,{descripcion},{importe}")
        _guardar(nota_id, lineas)
        return True, f"🛒 Recambio registrado: {descripcion} ({importe}€)"
    except Exception as e:
        return False, f"⚠️ Error: {e}"

def _resumen_mes(gastos, mes):
    """
    Filtra los gastos de un mes (YYYY-MM) y devuelve totales por categoría
    """
    gastos_mes = [g for g in gastos if g["fecha"].startswith(mes)]
    totales    = defaultdict(float)
    for g in gastos_mes:
        totales[g["tipo"]] += g["total"]
    return {
        "mes":      mes,
        "gasolina": round(totales["gasolina"], 2),
        "taller":   round(totales["taller"], 2),
        "recambio": round(totales["recambio"], 2),
        "total":    round(sum(totales.values()), 2),
        "n_gastos": len(gastos_mes),
    }

def resumen(mes=None):
    """
    Muestra el resumen de gastos del mes indicado (YYYY-MM)
    Si no se especifica, usa el mes actual con comparación al anterior
    """
    try:
        _, lineas = _cargar()
        gastos    = _parsear_lineas(lineas)

        if not mes:
            mes = datetime.now().strftime("%Y-%m")

        año, m  = int(mes[:4]), int(mes[5:])
        m_ant   = m - 1 if m > 1 else 12
        año_ant = año if m > 1 else año - 1
        mes_ant = f"{año_ant}-{m_ant:02d}"

        actual   = _resumen_mes(gastos, mes)
        anterior = _resumen_mes(gastos, mes_ant)

        def diff(a, b):
            d = round(a - b, 2)
            if d > 0:   return f" (+{d}€)"
            elif d < 0: return f" ({d}€)"
            return ""

        lineas_out = [f"🚗 Gastos del coche: {mes}"]

        if actual["n_gastos"] == 0:
            lineas_out.append("  Sin gastos registrados este mes.")
        else:
            lineas_out.append(f"  ⛽ Gasolina:  {actual['gasolina']}€{diff(actual['gasolina'], anterior['gasolina'])}")
            lineas_out.append(f"  🔧 Taller:    {actual['taller']}€{diff(actual['taller'], anterior['taller'])}")
            lineas_out.append(f"  🛒 Recambios: {actual['recambio']}€{diff(actual['recambio'], anterior['recambio'])}")
            lineas_out.append(f"  ─────────────────────")
            lineas_out.append(f"  Total:        {actual['total']}€{diff(actual['total'], anterior['total'])}")

        if anterior["n_gastos"] > 0:
            lineas_out.append(f"\n  (mes anterior {mes_ant}: {anterior['total']}€)")

        return "\n".join(lineas_out)
    except Exception as e:
        return f"⚠️ Error al generar resumen: {e}"

def _ultimos_meses(n):
    """
    Devuelve una lista de 'YYYY-MM' de los últimos n meses (incluye el actual),
    en orden cronológico.
    """
    hoy = date.today()
    año, mes = hoy.year, hoy.month
    meses = []
    for _ in range(n):
        meses.append(f"{año}-{mes:02d}")
        mes -= 1
        if mes == 0:
            mes, año = 12, año - 1
    return list(reversed(meses))

def grafico_gastos(n_meses=6):
    """
    Genera un gráfico de barras apiladas con los gastos del coche por
    categoría de los últimos n_meses. Devuelve bytes PNG, o None si no
    hay ningún gasto registrado en ese periodo.
    """
    _, lineas = _cargar()
    gastos = _parsear_lineas(lineas)

    meses     = _ultimos_meses(n_meses)
    resumenes = {m: _resumen_mes(gastos, m) for m in meses}

    if all(r["n_gastos"] == 0 for r in resumenes.values()):
        return None

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    fig.patch.set_facecolor(SUPERFICIE)
    ax.set_facecolor(SUPERFICIE)

    x      = range(len(meses))
    bottom = [0.0] * len(meses)
    for tipo in CATEGORIAS:
        valores = [resumenes[m][tipo] for m in meses]
        ax.bar(
            x, valores, bottom=bottom, width=0.5,
            color=COLORES[tipo], label=ETIQUETAS[tipo],
            edgecolor=SUPERFICIE, linewidth=2,
        )
        bottom = [b + v for b, v in zip(bottom, valores)]

    max_total = max(bottom) or 1
    for i, m in enumerate(meses):
        total = resumenes[m]["total"]
        if total > 0:
            ax.text(
                i, bottom[i] + max_total * 0.02, f"{total:.0f}€",
                ha="center", va="bottom", color="#0b0b0b", fontsize=10,
            )

    ax.set_xticks(list(x))
    ax.set_xticklabels(
        [datetime.strptime(m, "%Y-%m").strftime("%b %y") for m in meses],
        color="#52514e",
    )
    ax.tick_params(axis="y", colors="#898781")
    ax.set_ylabel("€", color="#52514e")

    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")

    ax.yaxis.grid(True, color="#e1e0d9", linewidth=1)
    ax.set_axisbelow(True)

    ax.set_title(f"Gastos del coche: últimos {n_meses} meses", color="#0b0b0b", fontsize=13, pad=15)
    ax.legend(loc="upper left", frameon=False, labelcolor="#52514e")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()