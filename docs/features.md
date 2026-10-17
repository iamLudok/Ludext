# Features: Detailed Documentation

## Medication Reminders

Ludok Home tracks your medicines and reminds you to take them via Telegram. All configuration and history is stored in **Nextcloud Notes**, so you can view and edit it from any device.

### Setup

On first run, Ludok Home automatically creates two notes in Nextcloud:

- **"Medicinas Config"**: one medicine per line, edit this to add or remove medicines
- **"Medicinas"**: daily history of what you've taken (managed automatically)

The format in "Medicinas Config" is:

```
nombre,cada_dias,hora_toma,aviso1,aviso2,...
```

Example:

```
MiMedicina,1,08:00,09:30,13:00
```

| Field | Description |
|---|---|
| `nombre` | Medicine name: used in `/medicina <name>` |
| `cada_dias` | `1` = every day, `2` = every other day, etc. |
| `hora_toma` | Time you should take it (shown in the daily briefing) |
| `aviso1`, `aviso2`... | Times to send a Telegram alert if not yet taken |

### How it works

- The daily briefing includes which medicines you need to take that day
- Send `/medicina MiMedicina` to mark it as taken
- At each alert time, if the medicine hasn't been marked, you get a Telegram reminder
- For every-other-day medicines, Ludok Home automatically calculates which days it's due based on your history

---

## Shopping List

The shopping list is stored in a Nextcloud Note called **"Lista de la compra"**, accessible from any device.

```
/compra           → show current list
/compra leche     → add "leche" to the list
/comprado leche   → remove "leche" from the list
/vaciarcompra     → clear everything
```

---

## Car Expenses

Car expenses are stored in a Nextcloud Note called **"Gastos del coche"** and organised by date. You can view the raw data from any device, and use `/coche` to get monthly summaries with comparisons.

```
/gasolina 45 1.72           → logs 45L × 1.72€/L = 77.40€
/taller Cambio aceite 85    → workshop expense
/recambio Bombillas H4 12   → personal purchase
/coche                      → current month summary vs previous month
/coche 2026-03              → summary for March 2026
```

---

## Wishlist

The wishlist is stored in a Nextcloud Note called **"Wishlist"**, accessible from any device.

```
/wishlist                                     → show your wishlist
/wish Auriculares Sony | https://amazon.es/…  → add a product with its link
/unwish Auriculares                           → remove a product
```

---

## Gift Ideas

Gift ideas are stored in a Nextcloud Note called **"Regalos"**, accessible from any device.

```
/regalos                                     → show your gift ideas
/regalo Libro de cocina | https://…          → add an idea with its link
/regalado Libro                              → bought it, remove from the list
```

---

## Event Reminders

The bot checks your Nextcloud calendar every minute and sends a Telegram notification about 30 minutes before each event starts.

---

## System Monitor

The `/pi` command shows the current state of the Raspberry Pi:

```
🖥️ Sistema: Raspberry Pi

🌡️ CPU:    52.3 °C  ✅
💾 RAM:    1823 / 3828 MB  (47.6%)  ✅
💿 Disco:  12.4 / 29.7 GB  (41.8%)  ✅
⏱️ Uptime: 3d 14h 22m
```

The bot also monitors the system every 5 minutes in the background and sends an automatic Telegram alert if any threshold is exceeded. Thresholds are configurable at the top of [system/monitor.py](../system/monitor.py):

| Variable | Default | Description |
|---|---|---|
| `TEMP_AVISO` | 70 °C | Warning alert |
| `TEMP_CRITICA` | 80 °C | Critical alert |
| `RAM_AVISO` | 85 % | RAM usage alert |
| `DISCO_AVISO` | 90 % | Disk usage alert |

---

## Network Devices

The `/red` command scans your home network and lists all connected devices with their IPs and MAC addresses.

Requires `nmap` installed on the Pi:

```bash
sudo apt install nmap
```

To label your devices by name, edit `system/devices.json`:

```json
{
  "macs": {
    "AA:BB:CC:DD:EE:FF": "Móvil",
    "11:22:33:44:55:66": "Smart TV"
  },
  "ips": {
    "192.168.1.1":  "Router",
    "192.168.1.50": "Raspberry Pi"
  }
}
```

---

## Customizing the Daily Briefing

To adjust how each section of the briefing is formatted (how many headlines, etc.), edit the section functions in [core/ai.py](../core/ai.py). The number of news items per feed is `max_per_feed` in `get_news()` ([core/sources.py](../core/sources.py)), and what the voice note says is built in `guion_noticias()` ([core/audio.py](../core/audio.py)).

The news voice note is generated locally with [Piper](https://github.com/OHF-Voice/piper1-gpl). To use another voice, download any `.onnx` + `.onnx.json` pair from [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) and set `PIPER_VOICE` in `.env`. If Piper or the voice is missing, the briefing is still sent as text.

To change the briefing time, edit your crontab:

```bash
crontab -e
```
