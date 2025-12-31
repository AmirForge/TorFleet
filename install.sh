#!/bin/bash

# ==========================================
# TorFleet - One-Line Installer
# GitHub: https://github.com/AmirForge/TorFleet
# Telegram: https://t.me/dusty_mesa
# ==========================================

set -e

echo "=========================================="
echo "TorFleet - Automatic Installer"
echo "=========================================="
echo ""

# --- Root check ---
if [ "$EUID" -ne 0 ]; then
    echo "[!] Please run as root (use sudo)"
    exit 1
fi

# --- Variables ---
REPO_URL="https://github.com/AmirForge/TorFleet.git"
INSTALL_DIR="/root/TorFleet"

# --- Update system ---
echo "[1/6] Updating system packages..."
apt update -y

# --- Install system dependencies ---
echo "[2/6] Installing system dependencies..."
apt install -y \
    tor \
    python3 \
    python3-pip \
    python3-requests \
    python3-schedule \
    python3-socks \
    git \
    curl \
    wget \
    obfs4proxy

# --- Verify Tor installation ---
if ! command -v tor &>/dev/null; then
    echo "[✗] Tor installation failed"
    exit 1
fi
echo "[✓] Tor installed successfully"

# --- Clone or update TorFleet ---
echo "[3/6] Installing TorFleet..."

if [ -d "$INSTALL_DIR" ]; then
    echo "    Existing installation found, updating repository..."
    cd "$INSTALL_DIR"
    git pull
else
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# --- Install Python requirements ---
echo "[4/6] Installing Python requirements..."
if [ -f "requirements.txt" ]; then
    pip3 install --break-system-packages -r requirements.txt || \
    pip3 install -r requirements.txt || true
fi

# --- Permissions ---
chmod +x TorFleet.py

# --- Prepare Tor directories ---
echo "[5/6] Preparing Tor directories..."
mkdir -p /root/tor
chmod 755 /root/tor

# --- Create launcher script ---
echo "[6/6] Creating launcher..."
cat > /usr/local/bin/torfleet << 'EOF'
#!/bin/bash
cd /root/TorFleet
exec python3 TorFleet.py
EOF

chmod +x /usr/local/bin/torfleet

# --- Installation complete ---
echo ""
echo "=========================================="
echo "✓ TorFleet installed successfully!"
echo "=========================================="
echo ""
echo "To start TorFleet, run:"
echo ""
echo "    torfleet"
echo ""
echo "GitHub: https://github.com/AmirForge/TorFleet"
echo "Telegram: https://t.me/dusty_mesa"
echo "=========================================="