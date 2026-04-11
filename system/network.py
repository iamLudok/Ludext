# ─────────────────────────────────────────────────────────
# network.py — Dispositivos conectados a la red local
# ─────────────────────────────────────────────────────────

import json
import re
import subprocess
from pathlib import Path

_DEVICES_JSON = Path(__file__).parent / "devices.json"
_INTERFACES_EXCLUIDAS = {"tailscale0", "tun0", "tun1", "wg0", "lo"}
_PREFIJOS_EXCLUIDOS   = ("127.", "169.254.")
_PREFIJOS_ETHERNET    = ("eth", "enp")
_RUTA_RE              = re.compile(r"(\d+\.\d+\.\d+\.\d+/\d+)\s+dev\s+(\S+)")

def _cargar_nombres():
    """
    Carga el mapeo MAC/IP → nombre desde devices.json
    """
    try:
        data = json.loads(_DEVICES_JSON.read_text())
        macs = {k.upper(): v for k, v in data.get("macs", {}).items()}
        ips  = data.get("ips", {})
        return macs, ips
    except Exception:
        return {}, {}

def _es_ruta_valida(red, iface):
    return (
        iface not in _INTERFACES_EXCLUIDAS
        and not any(red.startswith(p) for p in _PREFIJOS_EXCLUIDOS)
    )

def _parsear_rutas(salida):
    candidatas = []
    for linea in salida.splitlines():
        m = _RUTA_RE.match(linea)
        if m and _es_ruta_valida(m.group(1), m.group(2)):
            candidatas.append((m.group(1), m.group(2)))
    return candidatas

def _elegir_subred(candidatas):
    for red, iface in candidatas:
        if iface.startswith(_PREFIJOS_ETHERNET):
            return red
    return candidatas[0][0] if candidatas else None

def _subred_local():
    """
    Devuelve la subred local en formato CIDR (ej. '192.168.1.0/24')
    Usa 'ip route' ignorando interfaces VPN/Tailscale y priorizando ethernet
    """
    try:
        salida = subprocess.check_output(
            ["ip", "route", "show"], stderr=subprocess.DEVNULL, text=True
        )
        return _elegir_subred(_parsear_rutas(salida))
    except Exception:
        return None

def _tabla_arp():
    """
    Lee la tabla ARP del kernel y devuelve un dict {ip: mac}
    Funciona sin privilegios; nmap puebla esta tabla al hacer el ping sweep
    """
    macs = {}
    try:
        with open("/proc/net/arp") as f:
            for linea in f.readlines()[1:]:
                partes = linea.split()
                if len(partes) >= 4 and partes[3] != "00:00:00:00:00:00":
                    macs[partes[0]] = partes[3].upper()
    except OSError:
        pass
    return macs

def _escanear_nmap(subred):
    """
    Ejecuta 'nmap -sn <subred>' y cruza con la tabla ARP para obtener MACs
    """
    try:
        salida = subprocess.check_output(
            ["nmap", "-sn", subred],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        return None

    dispositivos = []
    actual = {}
    for linea in salida.splitlines():
        m = re.match(r"Nmap scan report for (.+)", linea)
        if m:
            if actual:
                dispositivos.append(actual)
            info = m.group(1).strip()
            m2 = re.match(r"(.+)\s+\((\d+\.\d+\.\d+\.\d+)\)", info)
            if m2:
                actual = {"hostname": m2.group(1), "ip": m2.group(2), "mac": ""}
            else:
                actual = {"hostname": "", "ip": info, "mac": ""}
    if actual:
        dispositivos.append(actual)

    macs = _tabla_arp()
    for d in dispositivos:
        d["mac"] = macs.get(d["ip"], "")

    return dispositivos

def _leer_arp():
    """
    Fallback: devuelve la tabla ARP como lista de dispositivos
    Solo muestra hosts con los que la Pi ha comunicado recientemente
    """
    macs = _tabla_arp()
    return [{"ip": ip, "hostname": "", "mac": mac} for ip, mac in sorted(macs.items())]

def dispositivos_conectados():
    """
    Devuelve un string con los dispositivos conectados a la red local
    """
    subred = _subred_local()

    if subred:
        dispositivos = _escanear_nmap(subred)
    else:
        dispositivos = None

    metodo = "nmap"
    if dispositivos is None:
        dispositivos = _leer_arp()
        metodo = "arp"

    if not dispositivos:
        return "📡 No se encontraron dispositivos en la red local."

    nombres_mac, nombres_ip = _cargar_nombres()

    lineas = [f"📡 Dispositivos en la red ({metodo}):"]
    if subred and metodo == "nmap":
        lineas[0] += f"\n    Subred: {subred}"

    for d in dispositivos:
        mac      = d["mac"].upper() if d["mac"] else ""
        etiqueta = nombres_mac.get(mac) or nombres_ip.get(d["ip"]) or d["hostname"] or ""
        mac_str  = mac or "—"
        lineas.append(f"\n  • {d['ip']}" + (f"  ({etiqueta})" if etiqueta else ""))
        lineas.append(f"    MAC: {mac_str}")

    lineas.append(f"\nTotal: {len(dispositivos)} dispositivos")
    return "\n".join(lineas)