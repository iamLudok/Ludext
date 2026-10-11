# ─────────────────────────────────────────────────────────
# api.py: Interfaz con Nextcloud Notes
# ─────────────────────────────────────────────────────────

import threading
from functools import wraps
import requests
from core.config import CONFIG

BASE = f"{CONFIG['nextcloud_url']}/apps/notes/api/v1"
AUTH = (CONFIG["nextcloud_user"], CONFIG["nextcloud_password"])

# Los comandos del bot corren en hilos: dos operaciones leer-modificar-guardar
# simultáneas sobre una nota podrían pisarse. Este lock las serializa.
_LOCK = threading.RLock()

def atomico(fn):
    """Decorador: ejecuta la función en exclusión mutua con las demás escrituras."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with _LOCK:
            return fn(*args, **kwargs)
    return wrapper

def _get(endpoint):
    resp = requests.get(f"{BASE}{endpoint}", auth=AUTH, timeout=10)
    resp.raise_for_status()
    return resp.json()

def _post(endpoint, data):
    resp = requests.post(f"{BASE}{endpoint}", auth=AUTH, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()

def _put(endpoint, data):
    resp = requests.put(f"{BASE}{endpoint}", auth=AUTH, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()

def buscar_nota(titulo):
    """
    Busca una nota por título exacto
    Devuelve el objeto nota o None si no existe
    """
    notas = _get("/notes")
    return next((n for n in notas if n["title"] == titulo), None)

def obtener_o_crear_nota(titulo, contenido_inicial=""):
    """
    Devuelve la nota con ese título
    Si no existe, la crea con el contenido inicial dado
    """
    nota = buscar_nota(titulo)
    if nota:
        return nota
    return _post("/notes", {"title": titulo, "content": contenido_inicial, "category": "Ludext"})

def actualizar_nota(nota_id, contenido):
    """
    Sobreescribe el contenido de una nota existente
    """
    return _put(f"/notes/{nota_id}", {"content": contenido})