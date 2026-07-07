# ─────────────────────────────────────────────────────────
# indexer.py — Indexa fotos de Nextcloud usando CLIP
# Almacenamiento: numpy array + JSON (sin Docker)
# ─────────────────────────────────────────────────────────

import io
import os
import json
import numpy as np
import requests
import xml.etree.ElementTree as ET
from urllib.parse import unquote
from core.config import CONFIG

PHOTO_EXTS    = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_DB_DIR       = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "photos_db")
_VECTORS_FILE = os.path.join(_DB_DIR, "vectors.npy")
_META_FILE    = os.path.join(_DB_DIR, "metadata.json")

_clip_model = None


def _get_clip_model():
    global _clip_model
    if _clip_model is None:
        from sentence_transformers import SentenceTransformer
        print("   📥 Cargando modelo CLIP (primera vez puede tardar)...")
        _clip_model = SentenceTransformer("clip-ViT-B-32")
    return _clip_model


def embed_image(image_bytes: bytes) -> np.ndarray | None:
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return _get_clip_model().encode(img)
    except Exception as e:
        print(f"   ⚠️  embed_image: {e}")
        return None


def embed_text(text: str) -> np.ndarray | None:
    try:
        return _get_clip_model().encode(text)
    except Exception as e:
        print(f"   ⚠️  embed_text: {e}")
        return None


# ── Base de datos local ───────────────────────────────────

def _load_db() -> tuple[np.ndarray | None, list[dict]]:
    if not os.path.exists(_VECTORS_FILE) or not os.path.exists(_META_FILE):
        return None, []
    try:
        vectors = np.load(_VECTORS_FILE)
        with open(_META_FILE, "r") as f:
            meta = json.load(f)
        return vectors, meta
    except Exception as e:
        print(f"   ⚠️  _load_db: {e}")
        return None, []


def _save_db(vectors: np.ndarray, meta: list[dict]):
    os.makedirs(_DB_DIR, exist_ok=True)
    np.save(_VECTORS_FILE, vectors.astype(np.float32))
    with open(_META_FILE, "w") as f:
        json.dump(meta, f)


def get_indexed_paths() -> set:
    _, meta = _load_db()
    return {m["webdav_path"] for m in meta}


def add_points(nuevos: list[tuple[str, str, np.ndarray]]):
    """Añade varias fotos a la base de una vez: [(webdav_path, filename, embedding), ...]"""
    if not nuevos:
        return
    vectors, meta = _load_db()
    vecs = np.vstack([e.reshape(1, -1).astype(np.float32) for _, _, e in nuevos])
    vectors = vecs if vectors is None else np.vstack([vectors, vecs])
    meta.extend({"webdav_path": p, "filename": f} for p, f, _ in nuevos)
    _save_db(vectors, meta)


# ── WebDAV ────────────────────────────────────────────────

def _auth() -> tuple:
    return CONFIG["nextcloud_user"], CONFIG["nextcloud_password"]


def _photos_url() -> str:
    return f"{CONFIG['nextcloud_url']}/remote.php/dav/files/{CONFIG['nextcloud_user']}/Photos"


def _parse_propfind(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    ns = {"d": "DAV:"}
    results = []
    for response in root.findall("d:response", ns):
        href_el = response.find("d:href", ns)
        if href_el is None:
            continue
        href = unquote(href_el.text)
        if response.find(".//d:resourcetype/d:collection", ns) is not None:
            continue
        ext = "." + href.rsplit(".", 1)[-1].lower() if "." in href else ""
        if ext in PHOTO_EXTS:
            results.append({"webdav_path": href, "filename": href.rsplit("/", 1)[-1]})
    return results


def _list_depth1_recursive(url: str) -> list[dict]:
    print(f"   📁 {url.split('/Photos')[-1] or '/Photos'}")
    body = '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:resourcetype/></d:prop></d:propfind>'
    try:
        r = requests.request("PROPFIND", url, auth=_auth(),
                             headers={"Depth": "1", "Content-Type": "application/xml"},
                             data=body, timeout=15)
    except Exception as e:
        print(f"   ⚠️  PROPFIND Depth:1 falló en {url}: {e}")
        return []
    root = ET.fromstring(r.text)
    ns = {"d": "DAV:"}
    files, dirs = [], []
    for response in root.findall("d:response", ns):
        href_el = response.find("d:href", ns)
        if href_el is None:
            continue
        href = unquote(href_el.text)
        if response.find(".//d:resourcetype/d:collection", ns) is not None:
            child_url = CONFIG["nextcloud_url"] + href
            if child_url.rstrip("/") != url.rstrip("/"):
                dirs.append(child_url)
        else:
            ext = "." + href.rsplit(".", 1)[-1].lower() if "." in href else ""
            if ext in PHOTO_EXTS:
                files.append({"webdav_path": href, "filename": href.rsplit("/", 1)[-1]})
    for d in dirs:
        files.extend(_list_depth1_recursive(d))
    return files


def list_photos_webdav() -> list[dict]:
    url = _photos_url()
    body = '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:resourcetype/></d:prop></d:propfind>'
    try:
        r = requests.request("PROPFIND", url, auth=_auth(),
                             headers={"Depth": "infinity", "Content-Type": "application/xml"},
                             data=body, timeout=60)
        if r.status_code in (403, 500, 501):
            print("   ℹ️  Depth:infinity bloqueado, usando recursión Depth:1")
            return _list_depth1_recursive(url)
        r.raise_for_status()
        return _parse_propfind(r.text)
    except Exception as e:
        print(f"   ⚠️  list_photos_webdav: {e}")
        return []


def download_photo_bytes(webdav_path: str) -> bytes | None:
    try:
        r = requests.get(CONFIG["nextcloud_url"] + webdav_path, auth=_auth(), timeout=30)
        r.raise_for_status()
        return r.content
    except Exception as e:
        print(f"   ⚠️  download {webdav_path}: {e}")
        return None


# ── Pipeline principal ────────────────────────────────────

def run_indexing(progress_callback=None) -> dict:
    _get_clip_model()

    all_photos = list_photos_webdav()
    if not all_photos:
        raise RuntimeError("No se encontraron fotos en Nextcloud Photos/")

    indexed    = get_indexed_paths()
    new_photos = [p for p in all_photos if p["webdav_path"] not in indexed]
    total      = len(all_photos)
    done       = 0
    failed     = 0
    lote       = []  # embeddings pendientes de guardar (guardado por lotes)

    for photo in new_photos:
        try:
            img_bytes = download_photo_bytes(photo["webdav_path"])
            if img_bytes is None:
                failed += 1
                continue

            vector    = embed_image(img_bytes)
            img_bytes = None  # liberar memoria

            if vector is None:
                failed += 1
                continue

            lote.append((photo["webdav_path"], photo["filename"], vector))
            done += 1

            if len(lote) >= 20:
                add_points(lote)
                lote = []

            if progress_callback and (done % 5 == 0 or done == len(new_photos)):
                progress_callback(done, len(new_photos), photo["filename"])

        except Exception as e:
            print(f"   ⚠️  {photo['filename']}: {e}")
            failed += 1

    add_points(lote)
    return {"total": total, "new": done, "failed": failed}