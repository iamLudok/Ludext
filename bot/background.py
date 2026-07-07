# ─────────────────────────────────────────────────────────
# background.py — Hilos de fondo: alertas, medicinas, sistema
# ─────────────────────────────────────────────────────────

import time
from datetime import datetime, timedelta
from caldav import DAVClient
from core.config import CONFIG
from notes.medicine import pendientes_en_hora
from system.monitor import alertas_sistema
from .handlers import send, teclado_medicinas

# Alertas de 30min ya enviadas: { "uid|inicio_iso": datetime_inicio }
_alertas_enviadas: dict = {}

# Cliente CalDAV cacheado: descubrir los calendarios cuesta varias peticiones
# HTTP y este hilo corre cada minuto. Se invalida si una iteración falla.
_calendarios_cache = None

def _calendarios():
    global _calendarios_cache
    if _calendarios_cache is None:
        client = DAVClient(
            url=CONFIG["nextcloud_caldav_url"],
            username=CONFIG["nextcloud_user"],
            password=CONFIG["nextcloud_password"],
        )
        _calendarios_cache = client.principal().calendars()
    return _calendarios_cache

def _check_medicinas():
    """
    Comprueba cada minuto si toca mandar un aviso de medicinas.
    Cada medicina define sus propias horas de aviso en medicinas.json.
    Revisa todos los minutos desde la última comprobación para no
    saltarse ninguno si una iteración tarda más de 60 segundos.
    """
    ultima = datetime.now()
    while True:
        try:
            ahora = datetime.now()

            # Minutos transcurridos desde la última comprobación (incluido el actual)
            minuto = ultima.replace(second=0, microsecond=0) + timedelta(minutes=1)
            pendientes_minutos = []
            while minuto <= ahora:
                pendientes_minutos.append(minuto.strftime("%H:%M"))
                minuto += timedelta(minutes=1)
            ultima = ahora

            sin_tomar = []
            for hhmm in pendientes_minutos:
                sin_tomar += [m for m in pendientes_en_hora(hhmm) if m not in sin_tomar]
            if sin_tomar:
                send(
                    f"💊 Recuerda tomar: {', '.join(sin_tomar)}",
                    reply_markup=teclado_medicinas(),
                )

        except Exception as e:
            print(f"   ⚠️  Error en avisos de medicinas: {e}")

        time.sleep(60)

def _check_alertas():
    """
    Comprueba cada minuto si hay eventos que empiecen en ~30 minutos
    y manda una alerta si aún no se ha enviado para ese evento.
    """
    global _calendarios_cache
    while True:
        try:
            ahora       = datetime.now()
            ventana_ini = ahora + timedelta(minutes=25)
            ventana_fin = ahora + timedelta(minutes=35)

            for cal in _calendarios():
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

                        if not dtstart or not hasattr(dtstart.dt, "hour"):
                            continue

                        # Los eventos recurrentes comparten UID, así que la
                        # clave incluye la fecha/hora de cada repetición
                        clave = f"{uid}|{dtstart.dt.isoformat()}"
                        if clave in _alertas_enviadas:
                            continue

                        hora_str = dtstart.dt.strftime("%H:%M")
                        send(f"⏰ En 30 minutos: {summary} a las {hora_str}")
                        _alertas_enviadas[clave] = datetime.now()
                except Exception as e:
                    # Puede ser una conexión cacheada muerta: reconectar en
                    # la siguiente iteración
                    print(f"   ⚠️  Error consultando calendario: {e}")
                    _calendarios_cache = None

            # Purga las alertas de hace más de un día
            limite = datetime.now() - timedelta(days=1)
            for clave in [k for k, v in _alertas_enviadas.items() if v < limite]:
                del _alertas_enviadas[clave]

        except Exception as e:
            print(f"   ⚠️  Error en alertas: {e}")
            _calendarios_cache = None

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