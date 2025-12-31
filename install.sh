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

# --- Fix line endings if needed ---
echo "[0/6] Fixing line endings..."
apt update -y
apt install -y dos2unix
dos2unix "$0" 2>/dev/null || sed -i 's/\r$//' "$0"

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
pip3 install --break-system-packages -r requirements.txt || \
apt install -y python3-requests python3-schedule python3-socks

# --- Permissions ---
chmod +x TorFleet.py

# --- Prepare Tor directories ---
echo "[5/6] Preparing Tor directories..."
mkdir -p /root/tor
chmod 755 /root/tor

# --- Run TorFleet ---
echo "[6/6] Starting TorFleet..."
echo "=========================================="
echo ""

cd "$INSTALL_DIR"
python3 TorFleet.py
