# 🧅 TorFleet

**TorFleet** is a powerful Python-based CLI tool for managing multiple Tor instances,
optimizing exit nodes by country, and automatically selecting the fastest available Tor routes.

It provides a complete Tor management solution with speed testing, bridge support,
persistent configuration, and scheduled re-testing — all from a single interface.

---

## ✨ Features
- 🚀 Run multiple Tor instances simultaneously
- 🌍 Country-based exit node selection
- ⚡ Automatic speed & latency testing
- 🧠 Smart retries to find the fastest circuits
- 🧅 Tor bridge support:
  - obfs4
  - snowflake
- ⏱ Scheduled automatic testing
- 💾 Persistent configuration storage
- 🖥 Interactive CLI + command-line flags
- 🔌 SOCKS5 proxy output ready to use

---

## 📦 System Requirements
- Linux (Ubuntu / Debian recommended)
- Python 3.8+
- Root access (required to manage Tor)
- Internet access

---

## 🚀 Quick Start & Installation

### 1️⃣ One-Line Install (Recommended)
This single command will:
- Install all required system dependencies
- Install Tor and bridge support (obfs4proxy)
- Download TorFleet into /root/TorFleet
- Install Python requirements
- Create a global torfleet command

curl -sSL https://raw.githubusercontent.com/AmirForge/TorFleet/main/install.sh | sudo bash

After installation completes, start TorFleet:
torfleet

---

### 2️⃣ Manual Installation
If you prefer to review the installation script first:

wget https://raw.githubusercontent.com/AmirForge/TorFleet/main/install.sh
chmod +x install.sh
sudo ./install.sh

Then start TorFleet:
torfleet

---

### 3️⃣ Interactive Menu Overview
When TorFleet starts, you will see:

1. Add Tor instance(s)
2. Remove Tor instance
3. List instances
4. Configure bridges
5. Start all (find best IPs)
6. Test running instances
7. Setup scheduling
8. Run scheduled tests
9. Set attempts per country
10. Save and exit
0. Exit without saving

---

### 4️⃣ Add a New Tor Instance
Menu → 1

You will be asked for:
- Instance name (example: tor-us)
- Country code (US, DE, FR, ...)
- SOCKS port (9050, 9051, ...)

Each instance runs independently in its own directory.

---

### 5️⃣ Find the Fastest Tor Routes
Menu → 5

TorFleet will automatically:
- Create new Tor circuits
- Verify exit country
- Test speed & latency
- Select the fastest available IP

Note:
If no suitable IP is found during 5. Start all (find best IPs),
use 8. Run scheduled tests to perform periodic testing.
This allows TorFleet to discover the best available IPs over time.

---

### 6️⃣ Configure Tor Bridges (Optional)
Menu → 4

Supported bridges:
- obfs4
- snowflake

Get bridges from:
https://bridges.torproject.org/

---

### 7️⃣ Run Without Menu (Auto Mode)
Start TorFleet using saved configuration:
torfleet

Or run directly:
cd /root/TorFleet
sudo python3 TorFleet.py -y

---

### 8️⃣ Test or List Instances (CLI)
sudo python3 TorFleet.py --test
sudo python3 TorFleet.py --list

---

### 9️⃣ SOCKS5 Proxy Usage
Each Tor instance provides a local SOCKS5 proxy:

socks5://127.0.0.1:<PORT>

Example:
socks5://127.0.0.1:9050

TorFleet can also be used as an outbound SOCKS proxy for VPN setups.
VPN traffic can be routed through TorFleet’s SOCKS5 proxies,
allowing multi-country outbound routing without purchasing additional servers.

---

## 🖥 Run TorFleet in Background (tmux)

tmux new -d -s torfleet "torfleet"
tmux attach -t torfleet
tmux kill-session -t torfleet

This allows TorFleet to keep running after disconnecting from the server.

---

## 🔗 Links
GitHub:
https://github.com/AmirForge/TorFleet

Telegram:
https://t.me/dusty_mesa

---

## 🛡 Security Notes
- TorFleet does not log user traffic
- External services are used only for IP detection and speed testing
- Always use trusted Tor bridges

---

## 🚧 Disclaimer
This project is intended for educational and research purposes only.
You are responsible for complying with local laws and regulations.

---

## ⭐ Support
If you find TorFleet useful, please consider giving it a star on GitHub.
