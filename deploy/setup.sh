set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================================"
echo "  Ludext — Private AI Morning Briefing"
echo "================================================"
echo ""
echo "Requirements: Nextcloud with Calendar, News and Notes apps installed."
echo "Features: daily briefing, Telegram bot, wishlist, system monitor, network scanner."

# ── 1. System dependencies ───────────────────────
echo ""
echo "📦 Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-venv curl nmap

# ── 2. Python virtual environment ───────────────
echo ""
echo "🐍 Creating Python virtual environment..."
python3 -m venv "$HOME/ludext-env"
source "$HOME/ludext-env/bin/activate"

pip install --upgrade pip -q
pip install \
    caldav \
    requests \
    icalendar \
    python-dotenv \
    -q

echo "   ✅ Python libraries installed"

# ── nmap capabilities (MAC addresses without root) ───
echo ""
echo "🔧 Configuring nmap permissions (MAC address scanning)..."
sudo setcap cap_net_raw+ep "$(which nmap)"
echo "   ✅ nmap configured"

# ── 3. Ollama ────────────────────────────────────
echo ""
echo "🤖 Installing Ollama..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "   ✅ Ollama installed"
else
    echo "   ℹ️  Ollama already installed"
fi

sudo systemctl enable ollama
sudo systemctl start ollama
sleep 3

# ── 4. Download AI model ─────────────────────────
echo ""
echo "⬇️  Downloading Llama 3.2 3B model (~2 GB, this may take a while)..."
ollama pull llama3.2:3b
echo "   ✅ Model ready"

# ── 5. .env file ─────────────────────────────────
echo ""
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "📝 .env file created from .env.example"
    echo "   ⚠️  Edit .env with your credentials before running Ludext"
else
    echo "   ℹ️  .env already exists, skipping"
fi

# ── 6. Daily briefing cron job ───────────────────
echo ""
echo "⏰ Setting up daily cron job (every day at 7:30)..."

CRON_LINE="30 7 * * * $HOME/ludext-env/bin/python3 $SCRIPT_DIR/ludext.py >> $HOME/ludext.log 2>&1"
(crontab -l 2>/dev/null | grep -v "ludext.py"; echo "$CRON_LINE") | crontab -

echo "   ✅ Cron configured: every day at 7:30"
echo "   📝 Logs at: ~/ludext.log"

# ── 7. Telegram bot systemd service ─────────────
echo ""
echo "🤖 Installing Telegram bot service..."

SERVICE_FILE="/etc/systemd/system/ludext-bot.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Ludext Bot — Telegram task and event manager
After=network.target

[Service]
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$HOME/ludext-env/bin/python3 $SCRIPT_DIR/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ludext-bot
sudo systemctl start ludext-bot

echo "   ✅ Bot service installed and started"

# ── Done ─────────────────────────────────────────
echo ""
echo "================================================"
echo "  ✅ Installation complete"
echo "================================================"
echo ""
echo "NEXT STEPS:"
echo "  1. Edit .env with your credentials:"
echo "     nano $SCRIPT_DIR/.env"
echo ""
echo "  2. Label your network devices (optional):"
echo "     nano $SCRIPT_DIR/dispositivos.json"
echo ""
echo "  3. Test the briefing manually:"
echo "     source ~/ludext-env/bin/activate"
echo "     python3 $SCRIPT_DIR/ludext.py"
echo ""
echo "  4. Use --debug to inspect the AI prompt:"
echo "     python3 $SCRIPT_DIR/ludext.py --debug"
echo ""
echo "  5. Check the bot is running:"
echo "     sudo systemctl status ludext-bot"
echo ""