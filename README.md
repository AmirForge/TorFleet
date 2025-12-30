# 🧅 TorFleet

**TorFleet** is a powerful Python-based CLI tool for managing multiple Tor instances,  
optimizing exit nodes by country, and automatically selecting the fastest available Tor routes.

It provides a **complete Tor management solution** with speed testing, bridge support,
persistent configuration, and scheduled re-testing — all from a single interface.

---

## ✨ Features

- 🚀 Run multiple Tor instances simultaneously
- 🌍 Country-based exit node selection
- ⚡ Automatic speed & latency testing
- 🧠 Smart retries to find the fastest circuits
- 🧅 Full Tor bridge support:
  - obfs4
  - snowflake
- ⏱ Scheduled automatic testing
- 💾 Persistent configuration storage
- 🖥 Interactive CLI + command-line flags
- 🔌 SOCKS5 proxy output ready to use

---

## 📦 System Requirements

- Linux (Ubuntu / Debian recommended)
- Python **3.8+**
- Root access (required to manage Tor)
- Internet access

---

## ⚙️ One-Step Prerequisites Installation (Recommended)

TorFleet includes an **automatic installer script** that installs **all required system and Python dependencies**, including:

- Tor
- Python3 & required libraries
- obfs4proxy (for bridges)
- Required directories and permissions
