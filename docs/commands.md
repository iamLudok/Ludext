# Telegram Bot — Command Reference

## Tasks

| Command | Description |
|---|---|
| `/tareas` | List all pending tasks |
| `/nueva <title>` | Create a new task |
| `/nueva <title> <dd/mm>` | Create a task with due date |
| `/borrar <title>` | Delete a task |
| `/editar <old> \| <new>` | Rename a task |

## Calendar

| Command | Description |
|---|---|
| `/agenda` | Show today and tomorrow's events |
| `/evento <title> <dd/mm>` | Create an all-day event |
| `/evento <title> <dd/mm> <HH:MM>` | Create an event with time |
| `/borrarevent <title>` | Delete an event |
| `/editarevent <old> \| <new>` | Rename an event |

## Medicines

| Command | Description |
|---|---|
| `/medicinas` | Show today's medicines with one-tap buttons to mark them as taken |
| `/medicina <name>` | Mark a medicine as taken (reminders also include a ✅ button) |
| `/graficomedicinas` | Adherence chart for the last 30 days |
| `/graficomedicinas <days>` | Adherence chart for the last N days (7-90) |

## Shopping List

| Command | Description |
|---|---|
| `/compra` | Show the shopping list |
| `/compra <item>` | Add an item to the list |
| `/comprado <item>` | Remove an item from the list |
| `/vaciarcompra` | Clear the entire list |

## Car Expenses

| Command | Description |
|---|---|
| `/gasolina <litres> <price/L>` | Log a fuel stop (total calculated automatically) |
| `/taller <description> <amount>` | Log a workshop expense |
| `/recambio <description> <amount>` | Log a personal purchase (parts, accessories) |
| `/coche` | Monthly expense summary with comparison to previous month |
| `/coche <YYYY-MM>` | Summary for a specific month |
| `/graficocoche` | Stacked bar chart of expenses by category, last 6 months |
| `/graficocoche <months>` | Chart for a custom number of months |

## Wishlist

| Command | Description |
|---|---|
| `/wishlist` | Show your wishlist |
| `/wish <name> \| <url>` | Add a product with its link |
| `/unwish <name>` | Remove a product |

## System & Network

| Command | Description |
|---|---|
| `/pi` | CPU temperature, RAM, disk usage and uptime |
| `/red` | Show devices connected to the home router |

## On-demand Summaries

| Command | Description |
|---|---|
| `/correos` | Summarize unread emails right now |
| `/resume` | Generate the full briefing on demand |
| `/ayuda` | Show all available commands |

## Automatic Alerts

- Telegram notification 30 minutes before any calendar event
- Medicine reminders if not marked as taken by the configured alert times
- CPU temperature alert at 70 °C (warning) and 80 °C (critical)
- RAM alert above 85% usage
- Disk alert above 90% usage
