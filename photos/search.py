# ─────────────────────────────────────────────────────────
# search.py: Búsqueda semántica de fotos con CLIP + numpy
# ─────────────────────────────────────────────────────────

import numpy as np
from photos.indexer import embed_text, download_photo_bytes, _load_db


def search_photos(query: str, top_k: int = 3) -> list[dict]:
    vectors, meta = _load_db()
    if vectors is None or len(meta) == 0:
        return []

    query_vec = embed_text(query)
    if query_vec is None:
        return []

    # Similitud coseno: normalizar y multiplicar
    q = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-10
    scores = (vectors / norms) @ q

    top_indices = np.argsort(scores)[::-1][:top_k]
    return [
        {
            "webdav_path": meta[i]["webdav_path"],
            "filename":    meta[i]["filename"],
            "score":       float(scores[i]),
        }
        for i in top_indices
    ]


def download_photo_for_telegram(webdav_path: str) -> bytes | None:
    return download_photo_bytes(webdav_path)