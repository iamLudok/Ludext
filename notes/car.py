# ─────────────────────────────────────────────────────────
# car.py — Gastos del coche en Nextcloud Notes
# ─────────────────────────────────────────────────────────

from datetime import date, datetime
from collections import defaultdict
from .api import obtener_o_crear_nota, actualizar_nota

TITULO_NOTA = "Gastos del coche"

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
                gastos.append({
                    "fecha":       fecha,
                    "tipo":        tipo,
                    "descripcion": partes[2],
                    "total":       float(partes[3]),
                })
        except (IndexError, ValueError):
            pass
    return gastos

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

def registrar_taller(descripcion, importe):
    """
    Registra un gasto en el taller
    """
    try:
        nota_id, lineas = _cargar()
        hoy = str(date.today())
        lineas.append(f"{hoy},taller,{descripcion},{importe}")
        _guardar(nota_id, lineas)
        return True, f"🔧 Taller registrado: {descripcion} — {importe}€"
    except Exception as e:
        return False, f"⚠️ Error: {e}"

def registrar_recambio(descripcion, importe):
    """
    Registra una compra personal (recambio, accesorio, etc.)
    """
    try:
        nota_id, lineas = _cargar()
        hoy = str(date.today())
        lineas.append(f"{hoy},recambio,{descripcion},{importe}")
        _guardar(nota_id, lineas)
        return True, f"🛒 Recambio registrado: {descripcion} — {importe}€"
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

        lineas_out = [f"🚗 Gastos del coche — {mes}"]

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