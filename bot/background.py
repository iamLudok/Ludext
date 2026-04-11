# ─────────────────────────────────────────────────────────
# background.py — Hilos de fondo: alertas, medicinas, sistema
# ─────────────────────────────────────────────────────────

import time
from datetime import datetime, timedelta
from caldav import DAVClient
from core.config import CONFIG
from notes.medicine import pendientes_en_hora
from system.monitor import alertas_sistema
from .handlers import send

# UIDs de eventos para los que ya se ha mandado la alerta de 30min
_alertas_enviadas: set = set()

# Registro de avisos de medicinas ya enviados hoy { "fecha": "2026-04-10", "09:30": True, ... }
_avisos_medicina_enviados: dict = {}

def _check_medicinas():
    """
    Comprueba cada minuto si toca mandar un aviso de medicinas.
    Cada medicina define sus propias horas de aviso en medicinas.json.
    """
    while True:
        try:
            ahora = datetime.now().strftime("%H:%M")
            hoy   = datetime.now().strftime("%Y-%m-%d")

            if _avisos_medicina_enviados.get("fecha") != hoy:
                _avisos_medicina_enviados.clear()
                _avisos_medicina_enviados["fecha"] = hoy

            if ahora not in _avisos_medicina_enviados:
                sin_tomar = pendientes_en_hora(ahora)
                if sin_tomar:
                    _avisos_medicina_enviados[ahora] = True
                    nombres = ", ".join(sin_tomar)
                    send(f"💊 Recuerda tomar: {nombres}")

        except Exception as e:
            print(f"   ⚠️  Error en avisos de medicinas: {e}")

        time.sleep(60)

def _check_alertas():
    """
    Comprueba cada minuto si hay eventos que empiecen en ~30 minutos
    y manda una alerta si aún no se ha enviado para ese evento.
    """
    while True:
        try:
            ahora       = datetime.now()
            ventana_ini = ahora + timedelta(minutes=25)
            ventana_fin = ahora + timedelta(minutes=35)

            client = DAVClient(
                url=CONFIG["nextcloud_caldav_url"],
                username=CONFIG["nextcloud_user"],
                password=CONFIG["nextcloud_password"],
            )
            calendars = client.principal().calendars()

            for cal in calendars:
                try:
                    results = cal.search(
                        start=ventana_ini,
                        end=ventana_fin,
                        event=True,
                        expand=True,
                    )
                    for event in results:
                        comp    = event.icalendar_component
                        uid     = str(comp.get("UID", ""))
                        summary = str(comp.get("SUMMARY", "Sin título"))
                        dtstart = comp.get("DTSTART")

                        if dtstart and not hasattr(dtstart.dt, "hour"):
                            continue

                        if uid in _alertas_enviadas:
                            continue

                        hora_str = dtstart.dt.strftime("%H:%M") if dtstart else ""
                        send(f"⏰ En 30 minutos: {summary} a las {hora_str}")
                        _alertas_enviadas.add(uid)
                except Exception:
                    pass

            if len(_alertas_enviadas) > 200:
                _alertas_enviadas.clear()

        except Exception as e:
            print(f"   ⚠️  Error en alertas: {e}")

        time.sleep(60)

def _check_sistema():
    """
    Comprueba cada 5 minutos la temperatura, RAM y disco.
    Manda alerta si algún valor supera los umbrales definidos en monitor.py.
    """
    while True:
        try:
            for alerta in alertas_sistema():
                send(alerta)
        except Exception as e:
            print(f"   ⚠️  Error en monitor de sistema: {e}")
        time.sleep(5 * 60)