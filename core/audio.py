# ─────────────────────────────────────────────────────────
# audio.py: Noticias en audio con Piper (TTS local, sin servicios externos)
# ─────────────────────────────────────────────────────────

import os
import re
import sys
import html
import subprocess
import tempfile
from .config import CONFIG

def _limpiar(texto):
    """Quita etiquetas HTML, entidades y espacios repetidos."""
    texto = html.unescape(re.sub(r"<[^>]+>", " ", texto or ""))
    return re.sub(r"\s+", " ", texto).strip()

def _recortar(texto, max_chars=350):
    """Recorta el texto al final de la última frase completa antes de max_chars."""
    if len(texto) <= max_chars:
        return texto
    corte = texto[:max_chars]
    fin   = max(corte.rfind(". "), corte.rfind("? "), corte.rfind("! "))
    return corte[:fin + 1] if fin > 0 else corte.rsplit(" ", 1)[0] + "."

def guion_noticias(articles):
    """
    Convierte la lista de artículos en el texto que se va a leer en voz alta
    Agrupa por feed para no repetir la fuente en cada noticia
    """
    if not articles:
        return ""
    partes = [f"Buenos días. Hoy tienes {len(articles)} noticias."]
    feed_actual = None
    for a in articles:
        if a["feed"] != feed_actual:
            feed_actual = a["feed"]
            partes.append(f"En {feed_actual}.")
        titulo = _limpiar(a["title"]).rstrip(".")
        partes.append(f"{titulo}.")
        resumen = _recortar(_limpiar(a.get("summary", "")))
        if resumen:
            partes.append(resumen)
    partes.append("Eso es todo por hoy.")
    return "\n".join(partes)

def generar_audio(texto):
    """
    Sintetiza el texto con Piper y lo convierte a OGG/Opus (nota de voz de Telegram)
    Devuelve los bytes del .ogg, o None si falta Piper, la voz o ffmpeg
    """
    voz = CONFIG["piper_voice"]
    if not texto:
        return None
    if not os.path.isfile(voz):
        print(f"   ⚠️  Voz de Piper no encontrada en {voz}")
        return None

    print("🎧 Generando audio de noticias...")
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "noticias.wav")
        ogg = os.path.join(tmp, "noticias.ogg")
        try:
            subprocess.run(
                # nice: que la síntesis no le quite CPU a Nextcloud mientras genera
                ["nice", "-n", "19", sys.executable, "-m", "piper", "--model", voz, "--output_file", wav],
                input=texto.encode("utf-8"), check=True, capture_output=True, timeout=900,
            )
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", wav,
                 "-c:a", "libopus", "-b:a", "32k", "-ac", "1", ogg],
                check=True, capture_output=True, timeout=300,
            )
            with open(ogg, "rb") as f:
                data = f.read()
        except FileNotFoundError as e:
            print(f"   ⚠️  Falta un programa para el audio: {e}")
            return None
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Error generando audio: {e.stderr.decode(errors='ignore')[-300:]}")
            return None
        except subprocess.TimeoutExpired:
            print("   ⚠️  La generación de audio tardó demasiado")
            return None

    print(f"   → {len(data) // 1024} KB de audio")
    return data
