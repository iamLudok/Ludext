# ─────────────────────────────────────────────────────────
# api.py — Interfaz con Nextcloud Notes
# ─────────────────────────────────────────────────────────

import requests
from core.config import CONFIG

BASE = f"{CONFIG['nextcloud_url']}/apps/notes/api/v1"
AUTH = (CONFIG["nextcloud_user"], CONFIG["nextcloud_password"])

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