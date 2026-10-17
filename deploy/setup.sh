set -e

# Raíz del proyecto (este script vive en deploy/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "================================================"
echo "  Ludext: Private Morning Briefing"
echo "================================================"
echo ""
echo "Requirements: Nextcloud with Calendar, News and Notes apps installed."
echo "Features: daily briefing with news audio, Telegram bot, wishlist, system monitor, network scanner."

# ── 1. System dependencies ───────────────────────
echo ""
echo "📦 Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-venv curl nmap ffmpeg

# ── 2. Python virtual environment ───────────────
echo ""
echo "🐍 Creating Python virtual environment..."
python3 -m venv "$HOME/ludext-env"
source "$HOME/ludext-env/bin/activate"

pip install --upgrade pip -q
pip install -r "$SCRIPT_DIR/requirements.txt" -q

echo "   ✅ Python libraries installed"

# ── Piper voice (news audio) ─────────────────────
echo ""
echo "🎧 Downloading Spanish voice for news audio..."
VOICE_DIR="$SCRIPT_DIR/voices"
VOICE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium"
mkdir -p "$VOICE_DIR"
for f in es_ES-davefx-medium.onnx es_ES-davefx-medium.onnx.json; do
    [ -f "$VOICE_DIR/$f" ] || curl -sL -o "$VOICE_DIR/$f" "$VOICE_URL/$f"
done
echo "   ✅ Voice ready in $VOICE_DIR"

# ── nmap capabilities (MAC addresses without root) ───
echo ""
echo "🔧 Configuring nmap permissions (MAC address scanning)..."
sudo setcap cap_net_raw+ep "$(which nmap)"
echo "   ✅ nmap configured"

# ── 3. .env file ─────────────────────────────────
echo ""
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "📝 .env file created from .env.example"
    echo "   ⚠️  Edit .env with your credentials before running Ludext"
else
    echo "   ℹ️  .env already exists, skipping"
fi

# ── 4. Daily briefing cron job ───────────────────
echo ""
echo "⏰ Setting up daily cron job (every day at 7:30)..."

CRON_LINE="30 7 * * * $HOME/ludext-env/bin/python3 $SCRIPT_DIR/ludext.py >> $HOME/ludext.log 2>&1"
(crontab -l 2>/dev/null | grep -v "ludext.py"; echo "$CRON_LINE") | crontab -

echo "   ✅ Cron configured: every day at 7:30"
echo "   📝 Logs at: ~/ludext.log"

# ── 5. Telegram bot systemd service ─────────────
echo ""
echo "🤖 Installing Telegram bot service..."

SERVICE_FILE="/etc/systemd/system/ludext-bot.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Ludext Bot: Telegram task and event manager
After=network.target

[Service]
User=$USER
WorkingDirectory=$SCRIPT_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$HOME/ludext-env/bin/python3 -m bot
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
echo "     nano $SCRIPT_DIR/system/devices.json"
echo ""
echo "  3. Test the briefing manually:"
echo "     source ~/ludext-env/bin/activate"
echo "     python3 $SCRIPT_DIR/ludext.py"
echo ""
echo "  4. Use --debug to save the briefing to a file:"
echo "     python3 $SCRIPT_DIR/ludext.py --debug"
echo ""
echo "  5. Check the bot is running:"
echo "     sudo systemctl status ludext-bot"
echo ""