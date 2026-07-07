# ─────────────────────────────────────────────────────────
# handlers.py — Función send(), parsers y handlers de comandos
# ─────────────────────────────────────────────────────────

import requests
import threading
import time
from datetime import datetime
from core.config import CONFIG
from photos.indexer import run_indexing
from photos.search import search_photos, download_photo_for_telegram
from scheduling.tasks import crear_tarea, borrar_tarea, editar_tarea, listar_tareas
from scheduling.events import crear_evento, borrar_evento, editar_evento
from core.sources import get_emails, get_calendar_events, get_tasks, get_news
from core.ai import build_briefing
from notes.medicine import marcar_tomada, resumen_medicinas, medicinas_de_hoy, grafico_adherencia
from notes.shopping import listar, añadir, comprado, vaciar
from notes.car import registrar_gasolina, registrar_taller, registrar_recambio, resumen, grafico_gastos
from system.network import dispositivos_conectados
from system.monitor import estado_sistema
from notes.wishlist import añadir_wish, listar_wish, borrar_wish
from notes.gf_gifts import añadir_regalo, listar_regalos, borrar_regalo

BASE_URL = f"https://api.telegram.org/bot{CONFIG['telegram_token']}"
CHAT_ID  = str(CONFIG["telegram_chat_id"])
AYUDA = """🤖 Comandos disponibles:

📋 TAREAS
/tareas — lista tus tareas pendientes
/nueva <título> — crea una tarea
/nueva <título> <dd/mm> — con fecha de vencimiento
/borrar <título> — elimina una tarea
/editar <viejo> | <nuevo> — renombra una tarea

📅 EVENTOS
/agenda — muestra eventos de hoy y mañana
/evento <título> <dd/mm> — crea evento (día completo)
/evento <título> <dd/mm> <HH:MM> — crea evento con hora
/borrarevent <título> — elimina un evento
/editarevent <viejo> | <nuevo> — renombra un evento

💊 MEDICINAS
/medicinas — estado de hoy, con botones para marcar
/medicina <nombre> — marca una medicina como tomada
/graficomedicinas — gráfico de adherencia (30 días)
/graficomedicinas <días> — gráfico de los últimos N días
(los avisos llegan con botón "✅ He tomado...")

🎁 WISHLIST
/wishlist — ver tu lista de deseos
/wish <nombre> | <url> — añadir producto
/unwish <nombre> — eliminar producto

💝 REGALOS NOVIA
/novia — ver la lista de ideas de regalo
/regalo <nombre> — añadir una idea
/regalo <nombre> | <url> — añadir idea con enlace
/regalado <nombre> — marcar como comprado y eliminar

🛒 LISTA DE LA COMPRA
/compra — muestra la lista
/compra <artículo> — añade un artículo
/comprado <artículo> — elimina un artículo
/vaciarcompra — vacía la lista entera

🖥️ SISTEMA
/pi — estado del sistema (CPU, RAM, disco, uptime)

📡 RED
/red — dispositivos conectados al router

🚗 GASTOS DEL COCHE
/gasolina <litros> <precio/L> — registra un repostaje
/taller <descripción> <importe> — gasto en taller
/recambio <descripción> <importe> — compra personal
/coche — resumen del mes actual
/coche <YYYY-MM> — resumen de un mes concreto
/graficocoche — gráfico de gastos (últimos 6 meses)
/graficocoche <meses> — gráfico de los últimos N meses

📷 FOTOS
/buscarfoto <texto> — busca fotos por descripción natural
/indexarfotos — indexa (o actualiza) las fotos de Nextcloud

📬 RESUMEN
/correos — resumen de correos no leídos
/resume — genera el briefing completo ahora

/ayuda — muestra este mensaje"""

def _post_con_reintentos(endpoint, intentos=3, **kwargs):
    """
    POST a la API de Telegram con reintentos.
    Respeta el retry_after de los errores 429 (rate limit).
    Devuelve True si se envió, False si se agotaron los intentos.
    """
    for intento in range(intentos):
        try:
            resp = requests.post(f"{BASE_URL}/{endpoint}", **kwargs)
            if resp.status_code == 429:
                espera = resp.json().get("parameters", {}).get("retry_after", 3)
                time.sleep(espera)
                continue
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"   ⚠️  {endpoint} (intento {intento + 1}/{intentos}): {e}")
            if intento < intentos - 1:
                time.sleep(2 ** intento)  # 1s, 2s
    return False

def send(text, reply_markup=None):
    """Envía un mensaje de texto al chat configurado, opcionalmente con botones."""
    payload = {"chat_id": CHAT_ID, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return _post_con_reintentos("sendMessage", json=payload, timeout=10)

def _answer_callback(callback_id, text=""):
    """Responde a un click de botón (toast en el móvil)."""
    try:
        requests.post(
            f"{BASE_URL}/answerCallbackQuery",
            json={"callback_query_id": callback_id, "text": text},
            timeout=10,
        )
    except Exception as e:
        print(f"   ⚠️  Error respondiendo callback: {e}")

def _edit_message(message_id, text, reply_markup=None):
    """Edita un mensaje ya enviado (texto y botones)."""
    payload = {"chat_id": CHAT_ID, "message_id": message_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{BASE_URL}/editMessageText", json=payload, timeout=10)
    except Exception as e:
        print(f"   ⚠️  Error editando mensaje: {e}")

def send_photo(photo_bytes: bytes, caption: str = ""):
    """Envía una foto al chat via multipart/form-data."""
    endpoint = "sendPhoto" if len(photo_bytes) < 9_000_000 else "sendDocument"
    field    = "photo" if endpoint == "sendPhoto" else "document"
    return _post_con_reintentos(
        endpoint,
        data={"chat_id": CHAT_ID, "caption": caption},
        files={field: ("foto.jpg", photo_bytes, "image/jpeg")},
        timeout=60,
    )

def _parse_fecha(texto):
    """
    Intenta interpretar un texto como fecha dd/mm.
    Si la fecha ya pasó este año, asume el año que viene.
    Devuelve un objeto date o None si no es una fecha válida.
    """
    try:
        año = datetime.now().year
        fecha = datetime.strptime(f"{texto}/{año}", "%d/%m/%Y").date()
        if fecha < datetime.now().date():
            fecha = fecha.replace(year=año + 1)
        return fecha
    except ValueError:
        return None

def _parse_hora(texto):
    """Intenta interpretar un texto como hora HH:MM. Devuelve time o None."""
    try:
        return datetime.strptime(texto, "%H:%M").time()
    except ValueError:
        return None

def cmd_tareas():
    return listar_tareas()

def cmd_nueva(args):
    """
    /nueva <título>
    /nueva <título> <dd/mm>
    """
    if not args:
        return "⚠️ Uso: /nueva <título> o /nueva <título> <dd/mm>"

    partes = args.rsplit(" ", 1)
    fecha  = None
    titulo = args

    if len(partes) == 2:
        fecha_candidata = _parse_fecha(partes[1])
        if fecha_candidata:
            fecha  = fecha_candidata
            titulo = partes[0].strip()

    _, msg = crear_tarea(titulo, fecha)
    return msg

def cmd_borrar(args):
    """/borrar <título>"""
    if not args:
        return "⚠️ Uso: /borrar <título>"
    _, msg = borrar_tarea(args)
    return msg

def cmd_editar(args):
    """/editar <viejo> | <nuevo>"""
    if "|" not in args:
        return "⚠️ Uso: /editar <título actual> | <título nuevo>"
    partes = args.split("|", 1)
    _, msg = editar_tarea(partes[0].strip(), partes[1].strip())
    return msg

def cmd_agenda():
    """Lista los eventos de hoy y mañana."""
    events = get_calendar_events()
    if not events:
        return "📅 No tienes eventos hoy ni mañana."
    lineas = ["📅 Agenda de hoy y mañana:"]
    for ev in events:
        hora = f" a las {ev['time']}" if ev['time'] else ""
        lineas.append(f"  • {ev['title']}{hora}")
    return "\n".join(lineas)

def cmd_evento(args):
    """
    /evento <título> <dd/mm>
    /evento <título> <dd/mm> <HH:MM>
    """
    if not args:
        return "⚠️ Uso: /evento <título> <dd/mm> o /evento <título> <dd/mm> <HH:MM>"

    partes = args.split()
    hora   = None
    fecha  = None

    if len(partes) >= 2:
        hora_candidata = _parse_hora(partes[-1])
        if hora_candidata:
            hora   = hora_candidata
            partes = partes[:-1]

    if len(partes) >= 2:
        fecha_candidata = _parse_fecha(partes[-1])
        if fecha_candidata:
            fecha  = fecha_candidata
            partes = partes[:-1]

    if not fecha:
        return "⚠️ Indica la fecha. Uso: /evento <título> <dd/mm> o /evento <título> <dd/mm> <HH:MM>"

    titulo = " ".join(partes)
    _, msg = crear_evento(titulo, fecha, hora)
    return msg

def cmd_borrarevent(args):
    """/borrarevent <título>"""
    if not args:
        return "⚠️ Uso: /borrarevent <título>"
    _, msg = borrar_evento(args)
    return msg

def cmd_editarevent(args):
    """/editarevent <viejo> | <nuevo>"""
    if "|" not in args:
        return "⚠️ Uso: /editarevent <título actual> | <título nuevo>"
    partes = args.split("|", 1)
    _, msg = editar_evento(partes[0].strip(), partes[1].strip())
    return msg

def cmd_correos():
    emails = get_emails()
    if not emails:
        return "📧 No tienes correos no leídos."
    lineas = ["📧 Correos no leídos:"]
    for e in emails:
        lineas.append(f"  • {e['from'][:50]} — {e['subject'][:80]}")
    return "\n".join(lineas)

def teclado_medicinas():
    """
    Teclado inline con un botón por medicina pendiente de hoy.
    Devuelve None si no queda ninguna pendiente.
    """
    try:
        pendientes = [m["nombre"] for m in medicinas_de_hoy() if not m["tomada"]]
    except Exception as e:
        print(f"   ⚠️  Error generando teclado de medicinas: {e}")
        return None
    if not pendientes:
        return None
    return {
        "inline_keyboard": [
            [{"text": f"✅ He tomado {n}", "callback_data": f"med:{n}"}]
            for n in pendientes
        ]
    }

def cmd_medicinas():
    """Muestra el estado de las medicinas de hoy con botones para marcarlas."""
    send(resumen_medicinas(), reply_markup=teclado_medicinas())
    return None

def cmd_medicina(args):
    """
    /medicina <nombre> — marca una medicina como tomada.
    También acepta /medicina sola para mostrar el resumen.
    """
    if not args:
        return cmd_medicinas()
    _, msg = marcar_tomada(args)
    return msg

def cmd_graficomedicinas(args):
    """
    /graficomedicinas          → adherencia de los últimos 30 días
    /graficomedicinas <días>   → adherencia de los últimos N días (7-90)
    """
    n_dias = 30
    if args:
        try:
            n_dias = int(args.strip())
            if not 7 <= n_dias <= 90:
                raise ValueError
        except ValueError:
            return "⚠️ Uso: /graficomedicinas <días entre 7 y 90>\nEjemplo: /graficomedicinas 30"

    try:
        png = grafico_adherencia(n_dias)
    except Exception as e:
        return f"⚠️ Error al generar el gráfico: {e}"

    if not png:
        return "💊 No hay medicinas configuradas en la nota 'Medicinas Config'."

    send_photo(png, caption=f"💊 Adherencia de medicinas — últimos {n_dias} días")
    return None

def cmd_wish(args):
    """/wish <nombre> | <url> — añade un producto a la wishlist."""
    return añadir_wish(args)

def cmd_wishlist():
    """/wishlist — muestra la wishlist."""
    return listar_wish()

def cmd_unwish(args):
    """/unwish <nombre> — elimina un producto de la wishlist."""
    return borrar_wish(args)

def cmd_novia():
    """/novia — muestra la lista de regalos para la novia."""
    return listar_regalos()

def cmd_regalo(args):
    """/regalo <nombre> o /regalo <nombre> | <url> — añade una idea de regalo."""
    return añadir_regalo(args)

def cmd_regalado(args):
    """/regalado <nombre> — elimina un regalo de la lista (ya comprado)."""
    if not args:
        return "⚠️ Uso: /regalado <nombre>"
    return borrar_regalo(args)

def cmd_compra(args):
    """
    /compra          → muestra la lista
    /compra <item>   → añade un artículo
    """
    if not args:
        return listar()
    return añadir(args)

def cmd_comprado(args):
    """/comprado <item> — elimina un artículo de la lista."""
    if not args:
        return "⚠️ Uso: /comprado <artículo>"
    return comprado(args)

def cmd_pi():
    """Muestra el estado del sistema de la Raspberry Pi."""
    return estado_sistema()

def cmd_red():
    """Muestra los dispositivos conectados a la red local."""
    send("📡 Escaneando la red... (puede tardar hasta 30 segundos)")
    return dispositivos_conectados()

def cmd_gasolina(args):
    """/gasolina <litros> <precio/L>"""
    partes = args.split()
    if len(partes) != 2:
        return "⚠️ Uso: /gasolina <litros> <precio por litro>\nEjemplo: /gasolina 45 1.72"
    try:
        litros       = float(partes[0])
        precio_litro = float(partes[1])
    except ValueError:
        return "⚠️ Los valores deben ser números. Ejemplo: /gasolina 45 1.72"
    _, msg = registrar_gasolina(litros, precio_litro)
    return msg

def cmd_taller(args):
    """/taller <descripción> <importe>"""
    partes = args.rsplit(" ", 1)
    if len(partes) != 2:
        return "⚠️ Uso: /taller <descripción> <importe>\nEjemplo: /taller Cambio aceite 85"
    try:
        importe = float(partes[1])
    except ValueError:
        return "⚠️ El importe debe ser un número. Ejemplo: /taller Cambio aceite 85"
    _, msg = registrar_taller(partes[0].strip(), importe)
    return msg

def cmd_recambio(args):
    """/recambio <descripción> <importe>"""
    partes = args.rsplit(" ", 1)
    if len(partes) != 2:
        return "⚠️ Uso: /recambio <descripción> <importe>\nEjemplo: /recambio Bombillas H4 12.50"
    try:
        importe = float(partes[1])
    except ValueError:
        return "⚠️ El importe debe ser un número. Ejemplo: /recambio Bombillas H4 12.50"
    _, msg = registrar_recambio(partes[0].strip(), importe)
    return msg

def cmd_coche(args):
    """
    /coche          → resumen del mes actual
    /coche 2026-03  → resumen de un mes concreto
    """
    mes = args.strip() if args else None
    return resumen(mes)

def cmd_graficocoche(args):
    """
    /graficocoche          → gráfico de los últimos 6 meses
    /graficocoche <meses>  → gráfico de los últimos N meses
    """
    n_meses = 6
    if args:
        try:
            n_meses = int(args.strip())
            if n_meses <= 0:
                raise ValueError
        except ValueError:
            return "⚠️ Uso: /graficocoche <número de meses>\nEjemplo: /graficocoche 6"

    try:
        png = grafico_gastos(n_meses)
    except Exception as e:
        return f"⚠️ Error al generar el gráfico: {e}"

    if not png:
        return "📊 No hay gastos registrados en ese periodo."

    send_photo(png, caption=f"🚗 Gastos del coche — últimos {n_meses} meses")
    return None

def cmd_buscarfoto(query: str):
    """/buscarfoto <texto> — busca fotos por descripción natural."""
    if not query:
        return "⚠️ Uso: /buscarfoto <descripción>\nEjemplo: /buscarfoto boarding pass islandia"

    send(f"🔍 Buscando fotos: {query}...")
    try:
        results = search_photos(query, top_k=3)
    except Exception as e:
        return f"⚠️ Error en la búsqueda: {e}"

    if not results:
        return "📷 No encontré fotos que coincidan con tu búsqueda."

    sent = 0
    for r in results:
        photo_bytes = download_photo_for_telegram(r["webdav_path"])
        if photo_bytes:
            score_pct = round(r["score"] * 100)
            caption   = f"📸 {r['filename']} (similitud: {score_pct}%)"
            send_photo(photo_bytes, caption)
            sent += 1

    if sent == 0:
        return "⚠️ Encontré resultados pero no pude descargar las fotos."
    return None  # las fotos ya fueron enviadas


def cmd_indexarfotos():
    """/indexarfotos — indexa (o actualiza) las fotos de Nextcloud en segundo plano."""
    def _progress(done, total, filename):
        send(f"📸 Indexando... {done}/{total} — {filename}")

    def _run():
        try:
            result = run_indexing(progress_callback=_progress)
            send(
                f"✅ Indexación completada.\n"
                f"  Total en Nextcloud: {result['total']}\n"
                f"  Nuevas indexadas: {result['new']}\n"
                f"  Fallos: {result['failed']}"
            )
        except Exception as e:
            send(f"⚠️ Error durante la indexación: {e}")

    threading.Thread(target=_run, daemon=True).start()
    return "📸 Iniciando indexación en segundo plano...\n(recibirás actualizaciones de progreso)"


def cmd_resume():
    send("🌅 Generando briefing...")
    emails   = get_emails()
    events   = get_calendar_events()
    tasks    = get_tasks()
    articles = get_news()
    return build_briefing(emails, events, tasks, articles, resumen_medicinas())

def handle(text):
    """Enruta el comando al handler correspondiente."""
    text = text.strip()
    cmd, _, args = text.partition(" ")
    cmd  = cmd.lower()
    args = args.strip()

    routes = {
        "/tareas":       lambda: cmd_tareas(),
        "/nueva":        lambda: cmd_nueva(args),
        "/borrar":       lambda: cmd_borrar(args),
        "/editar":       lambda: cmd_editar(args),
        "/agenda":       lambda: cmd_agenda(),
        "/evento":       lambda: cmd_evento(args),
        "/borrarevent":  lambda: cmd_borrarevent(args),
        "/editarevent":  lambda: cmd_editarevent(args),
        "/medicinas":    lambda: cmd_medicinas(),
        "/medicina":     lambda: cmd_medicina(args),
        "/graficomedicinas": lambda: cmd_graficomedicinas(args),
        "/compra":       lambda: cmd_compra(args),
        "/comprado":     lambda: cmd_comprado(args),
        "/vaciarcompra": lambda: vaciar(),
        "/gasolina":     lambda: cmd_gasolina(args),
        "/taller":       lambda: cmd_taller(args),
        "/recambio":     lambda: cmd_recambio(args),
        "/coche":        lambda: cmd_coche(args),
        "/graficocoche": lambda: cmd_graficocoche(args),
        "/wishlist":     lambda: cmd_wishlist(),
        "/wish":         lambda: cmd_wish(args),
        "/unwish":       lambda: cmd_unwish(args),
        "/novia":        lambda: cmd_novia(),
        "/regalo":       lambda: cmd_regalo(args),
        "/regalado":     lambda: cmd_regalado(args),
        "/pi":           lambda: cmd_pi(),
        "/red":          lambda: cmd_red(),
        "/buscarfoto":   lambda: cmd_buscarfoto(args),
        "/indexarfotos": lambda: cmd_indexarfotos(),
        "/correos":      lambda: cmd_correos(),
        "/resume":       lambda: cmd_resume(),
        "/ayuda":        lambda: AYUDA,
        "/start":        lambda: AYUDA,
        "/help":         lambda: AYUDA,
    }

    handler = routes.get(cmd)
    return handler() if handler else None

def handle_callback(callback):
    """
    Gestiona el click de un botón inline.
    Formato de callback_data: "med:<nombre>" para marcar una medicina.
    """
    data       = callback.get("data", "")
    message_id = callback.get("message", {}).get("message_id")

    if not data.startswith("med:"):
        _answer_callback(callback["id"])
        return

    nombre = data[len("med:"):]
    try:
        _, msg = marcar_tomada(nombre)
    except Exception as e:
        msg = f"⚠️ Error: {e}"
    _answer_callback(callback["id"], msg)

    # Actualiza el mensaje original: estado al día y solo botones de las pendientes
    if message_id:
        _edit_message(message_id, resumen_medicinas(), teclado_medicinas())