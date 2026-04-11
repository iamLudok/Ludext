# ─────────────────────────────────────────────────────────
# sources.py — Datos de Gmail, Nextcloud y noticias
# ─────────────────────────────────────────────────────────

import imaplib
import email
import re
from email.header import decode_header
from datetime import date, timedelta
import requests
from .config import CONFIG
from scheduling.tasks import fetch as _fetch_tasks
from scheduling.events import fetch as _fetch_events

def get_emails(max_emails=10):
    """
    Devuelve hasta 10 correos no leídos
    Primero mira las últimas 24h; si no llega a 10, completa con más antiguos
    """
    print("📧 Leyendo correos...")
    emails = []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(CONFIG["gmail_user"], CONFIG["gmail_app_password"])
        mail.select("inbox")

        since = (date.today() - timedelta(days=1)).strftime("%d-%b-%Y")
        _, data = mail.search(None, f'(UNSEEN SINCE "{since}")')
        ids = data[0].split()

        if len(ids) < max_emails:
            _, data_all = mail.search(None, "UNSEEN")
            all_ids = data_all[0].split()
            extra   = [i for i in all_ids if i not in ids]
            ids     = extra[-(max_emails - len(ids)):] + ids

        ids = ids[-max_emails:]

        for uid in ids:
            _, msg_data = mail.fetch(uid, "(BODY.PEEK[])")
            msg = email.message_from_bytes(msg_data[0][1])

            subject_raw, enc = decode_header(msg["Subject"] or "Sin asunto")[0]
            subject = subject_raw.decode(enc or "utf-8") if isinstance(subject_raw, bytes) else subject_raw
            sender  = msg.get("From", "Desconocido")

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode("utf-8", errors="ignore")[:400]
                        except Exception:
                            pass
                        break
            else:
                try:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")[:400]
                except Exception:
                    pass

            emails.append({"from": sender, "subject": subject, "body": body.strip()})

        mail.logout()
        print(f"   → {len(emails)} correos no leídos")
    except Exception as e:
        print(f"   ⚠️  Error en correos: {e}")
    return emails

def get_calendar_events():
    """
    Devuelve los eventos del calendario de hoy y mañana
    """
    print("📅 Leyendo calendario...")
    events = _fetch_events()
    print(f"   → {len(events)} eventos")
    return events

def get_tasks():
    """
    Devuelve hasta 20 tareas pendientes de Decs
    """
    print("✅ Leyendo tareas...")
    tasks = _fetch_tasks()
    print(f"   → {len(tasks)} tareas pendientes")
    return tasks


def get_news(max_items=30):
    """
    Devuelve los últimos artículos no leídos de Nextcloud News
    """
    print("📰 Leyendo noticias...")
    articles = []
    try:
        url = f"{CONFIG['nextcloud_url']}/index.php/apps/news/api/v1-3/items"
        resp = requests.get(
            url,
            auth=(CONFIG["nextcloud_user"], CONFIG["nextcloud_password"]),
            params={"batchSize": max_items, "offset": 0, "type": 3, "id": 0, "getRead": False},
            timeout=15,
        )
        resp.raise_for_status()

        for item in resp.json().get("items", []):
            body_clean = re.sub(r"<[^>]+>", "", item.get("body", ""))[:300]
            articles.append({
                "title":   item.get("title", ""),
                "summary": body_clean.strip(),
                "feed":    item.get("feedTitle", ""),
            })

        print(f"   → {len(articles)} artículos")
    except Exception as e:
        print(f"   ⚠️  Error en noticias: {e}")
    return articles