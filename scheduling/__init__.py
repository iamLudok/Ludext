# ─────────────────────────────────────────────────────────
# calendar: Conexión compartida con Nextcloud CalDAV
# ─────────────────────────────────────────────────────────

from caldav import DAVClient
from core.config import CONFIG

def get_calendars():
    """
    Abre conexión con Nextcloud y devuelve los calendarios
    """
    client = DAVClient(
        url=CONFIG["nextcloud_caldav_url"],
        username=CONFIG["nextcloud_user"],
        password=CONFIG["nextcloud_password"],
    )
    return client.principal().calendars()