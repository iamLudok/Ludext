# ─────────────────────────────────────────────────────────
# monitor.py: Monitor de sistema de la Raspberry Pi
# ─────────────────────────────────────────────────────────

import subprocess
from pathlib import Path

TEMP_CRITICA = 80.0   # °C: alerta roja
TEMP_AVISO   = 70.0   # °C: alerta amarilla
RAM_AVISO    = 85.0   # %: alerta si supera este uso
DISCO_AVISO  = 90.0   # %: alerta si supera este uso

def _temperatura():
    """
    Lee la temperatura de la CPU desde /sys
    Devuelve float en °C o None
    """
    try:
        raw = Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip()
        return round(int(raw) / 1000, 1)
    except Exception:
        return None

def _ram():
    """
    Lee /proc/meminfo y devuelve (total_mb, usado_mb, pct_uso)
    """
    try:
        info = {}
        for linea in Path("/proc/meminfo").read_text().splitlines():
            partes = linea.split()
            if len(partes) >= 2:
                info[partes[0].rstrip(":")] = int(partes[1])

        total      = info.get("MemTotal", 0)
        disponible = info.get("MemAvailable", 0)
        usado      = total - disponible
        pct        = round(usado / total * 100, 1) if total else 0
        return round(total / 1024), round(usado / 1024), pct
    except Exception:
        return None, None, None

def _disco():
    """
    Devuelve (total_gb, usado_gb, pct_uso) del disco raíz
    """
    try:
        salida = subprocess.check_output(
            ["df", "-k", "/"], stderr=subprocess.DEVNULL, text=True
        ).splitlines()[1].split()
        total = int(salida[1])
        usado = int(salida[2])
        pct   = round(usado / total * 100, 1) if total else 0
        return round(total / 1024 / 1024, 1), round(usado / 1024 / 1024, 1), pct
    except Exception:
        return None, None, None

def _uptime():
    """
    Devuelve el uptime como string legible (ej. '3d 14h 22m')
    """
    try:
        segundos = float(Path("/proc/uptime").read_text().split()[0])
        dias     = int(segundos // 86400)
        horas    = int((segundos % 86400) // 3600)
        minutos  = int((segundos % 3600) // 60)
        partes   = []
        if dias:   partes.append(f"{dias}d")
        if horas:  partes.append(f"{horas}h")
        partes.append(f"{minutos}m")
        return " ".join(partes)
    except Exception:
        return "-"

def estado_sistema():
    """
    Devuelve un string con el estado completo del sistema
    """
    temp                                = _temperatura()
    ram_total, ram_usada, ram_pct       = _ram()
    disco_total, disco_usado, disco_pct = _disco()
    uptime                              = _uptime()

    if temp is None:            temp_str = "-"
    elif temp >= TEMP_CRITICA:  temp_str = f"{temp} °C  ⚠️ CRÍTICA"
    elif temp >= TEMP_AVISO:    temp_str = f"{temp} °C  ⚠️ alta"
    else:                       temp_str = f"{temp} °C  ✅"

    if ram_pct is None:        ram_str = "-"
    elif ram_pct >= RAM_AVISO: ram_str = f"{ram_usada} / {ram_total} MB  ({ram_pct}%)  ⚠️"
    else:                      ram_str = f"{ram_usada} / {ram_total} MB  ({ram_pct}%)  ✅"

    if disco_pct is None:          disco_str = "-"
    elif disco_pct >= DISCO_AVISO: disco_str = f"{disco_usado} / {disco_total} GB  ({disco_pct}%)  ⚠️"
    else:                          disco_str = f"{disco_usado} / {disco_total} GB  ({disco_pct}%)  ✅"

    return (
        f"🖥️ Sistema: Raspberry Pi\n\n"
        f"🌡️ CPU:    {temp_str}\n"
        f"💾 RAM:    {ram_str}\n"
        f"💿 Disco:  {disco_str}\n"
        f"⏱️ Uptime: {uptime}"
    )

def alertas_sistema():
    """
    Devuelve lista de alertas si algún valor supera los umbrales
    Llamado desde el hilo de monitorización en bot.py
    """
    alertas = []
    temp = _temperatura()
    if temp is not None:
        if temp >= TEMP_CRITICA:
            alertas.append(f"🌡️ ALERTA: CPU a {temp} °C: temperatura crítica en la Raspberry Pi")
        elif temp >= TEMP_AVISO:
            alertas.append(f"🌡️ Aviso: CPU a {temp} °C: temperatura alta en la Raspberry Pi")

    _, _, ram_pct = _ram()
    if ram_pct is not None and ram_pct >= RAM_AVISO:
        alertas.append(f"💾 Aviso: RAM al {ram_pct}% de uso")

    _, _, disco_pct = _disco()
    if disco_pct is not None and disco_pct >= DISCO_AVISO:
        alertas.append(f"💿 Aviso: Disco al {disco_pct}% de uso")

    return alertas