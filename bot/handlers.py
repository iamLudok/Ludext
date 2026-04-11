# ─────────────────────────────────────────────────────────
# handlers.py — Función send(), parsers y handlers de comandos
# ─────────────────────────────────────────────────────────

import requests
from datetime import datetime
from core.config import CONFIG
from scheduling.tasks import crear_tarea, borrar_tarea, editar_tarea, listar_tareas
from scheduling.events import crear_evento, borrar_evento, editar_evento
from core.sources import get_emails, get_calendar_events, get_tasks, get_news
from core.ai import build_prompt, ask_ollama
from notes.medicine import marcar_tomada, resumen_medicinas
from notes.shopping import listar, añadir, comprado, vaciar
from notes.car import registrar_gasolina, registrar_taller, registrar_recambio, resumen
from system.network import dispositivos_conectados
from system.monitor import estado_sistema
from notes.wishlist import añadir_wish, listar_wish, borrar_wish

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
/medicinas — estado de las medicinas de hoy
/medicina <nombre> — marca una medicina como tomada

🎁 WISHLIST
/wishlist — ver tu lista de deseos
/wish <nombre> | <url> — añadir producto
/unwish <nombre> — eliminar producto

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

📬 RESUMEN
/correos — resumen de correos no leídos
/resume — genera el briefing completo ahora

/ayuda — muestra este mensaje"""

def send(text):
    """Envía un mensaje de texto al chat configurado."""
    try:
        requests.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text},
            timeout=10,
        )
    except Exception as e:
        print(f"   ⚠️  Error enviando mensaje: {e}")

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
    """Genera un resumen de los correos no leídos con Ollama."""
    send("📧 Leyendo correos... (puede tardar unos minutos)")
    emails = get_emails()
    if not emails:
        return "📧 No tienes correos no leídos."

    hoy = datetime.now().strftime("%A %d de %B")
    lineas = [
        f"Hoy es {hoy}. Resume en español estos correos no leídos.",
        "Destaca solo los que requieren acción. Ignora newsletters y spam.",
        "---",
    ]
    for e in emails:
        lineas.append(f"- De: {e['from'][:50]} | Asunto: {e['subject'][:80]}")
        if e['body']:
            lineas.append(f"  {e['body'][:200]}")
    lineas.append("---")
    lineas.append("Sé conciso. Máximo 200 palabras.")

    resumen_correos = ask_ollama("\n".join(lineas))
    return resumen_correos or "⚠️ Error al generar resumen de correos."

def cmd_medicinas():
    """Muestra el estado de las medicinas de hoy."""
    return resumen_medicinas()

def cmd_medicina(args):
    """
    /medicina <nombre> — marca una medicina como tomada.
    También acepta /medicina sola para mostrar el resumen.
    """
    if not args:
        return resumen_medicinas()
    _, msg = marcar_tomada(args)
    return msg

def cmd_wish(args):
    """/wish <nombre> | <url> — añade un producto a la wishlist."""
    return añadir_wish(args)

def cmd_wishlist():
    """/wishlist — muestra la wishlist."""
    return listar_wish()

def cmd_unwish(args):
    """/unwish <nombre> — elimina un producto de la wishlist."""
    return borrar_wish(args)

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

def cmd_resume():
    """Genera el briefing completo ahora mismo."""
    send("🌅 Generando briefing... (puede tardar varios minutos)")
    emails   = get_emails()
    events   = get_calendar_events()
    tasks    = get_tasks()
    articles = get_news()

    prompt  = build_prompt(emails, events, tasks, articles, resumen_medicinas())
    summary = ask_ollama(prompt)

    if not summary:
        summary = "⚠️ No se pudo generar el resumen. Revisa que Ollama esté corriendo."

    return f"🌅 Ludext — {datetime.now().strftime('%A %d/%m/%Y')}\n\n{summary}"

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
        "/compra":       lambda: cmd_compra(args),
        "/comprado":     lambda: cmd_comprado(args),
        "/vaciarcompra": lambda: vaciar(),
        "/gasolina":     lambda: cmd_gasolina(args),
        "/taller":       lambda: cmd_taller(args),
        "/recambio":     lambda: cmd_recambio(args),
        "/coche":        lambda: cmd_coche(args),
        "/wishlist":     lambda: cmd_wishlist(),
        "/wish":         lambda: cmd_wish(args),
        "/unwish":       lambda: cmd_unwish(args),
        "/pi":           lambda: cmd_pi(),
        "/red":          lambda: cmd_red(),
        "/correos":      lambda: cmd_correos(),
        "/resume":       lambda: cmd_resume(),
        "/ayuda":        lambda: AYUDA,
        "/start":        lambda: AYUDA,
        "/help":         lambda: AYUDA,
    }

    handler = routes.get(cmd)
    return handler() if handler else None