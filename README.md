<div align="center">

# 🖥️ Remote Administration Tool

<img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=32&duration=2800&pause=2000&color=00ADD8&center=true&vCenter=true&width=940&lines=Professional+Remote+Administration;Multi-Client+Management;Privilege+Escalation+%26+UAC+Bypass;Built+with+Python" alt="Typing SVG" />

<p align="center">
  <img src="https://img.shields.io/badge/python-3.x-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python Version"/>
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg?style=for-the-badge&logo=windows&logoColor=white" alt="Platform"/>
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="License"/>
  <img src="https://img.shields.io/github/stars/palnirupam/Remote-admin-tool?style=for-the-badge&logo=github" alt="Stars"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Multi--Client-✓-success?style=flat-square" alt="Multi-Client"/>
  <img src="https://img.shields.io/badge/GUI%20Interface-✓-success?style=flat-square" alt="GUI"/>
  <img src="https://img.shields.io/badge/UAC%20Bypass-✓-red?style=flat-square" alt="UAC Bypass"/>
  <img src="https://img.shields.io/badge/GeoLocation-✓-success?style=flat-square" alt="GeoLocation"/>
  <img src="https://img.shields.io/badge/Real--time-✓-success?style=flat-square" alt="Real-time"/>
</p>

**🚀 Professional TCP-based remote administration tool with enterprise-grade features**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [📖 Complete Guide](USAGE_GUIDE.md) • [Documentation](#-documentation)

---

</div>

## 📋 Overview

<div align="center">
<img src="https://user-images.githubusercontent.com/74038190/212284100-561aa473-3905-4a80-b561-0d28506553ee.gif" width="700">
</div>

A **powerful** and **lightweight** Python-based remote administration tool that enables seamless command execution across multiple client machines through a centralized server. Built with modern architecture and professional UI design.

> 📖 **New to this tool?** Check out our [Complete Usage Guide](USAGE_GUIDE.md) for step-by-step instructions!

### ✨ Why Choose This Tool?

<table>
<tr>
<td width="50%">

#### 🎯 **For Cybersecurity Students**
- UAC bypass techniques (fodhelper)
- Privilege escalation detection
- GeoLocation & IP intelligence
- Real-world pentest workflows

</td>
<td width="50%">

#### 🏢 **For IT Admins**
- Multi-client management
- Real-time monitoring
- Cross-platform support
- Professional GUI

</td>
</tr>
</table>

---

## 🌟 Features

<div align="center">

| Feature | Description | Status |
|:-------:|:------------|:------:|
| 🔌 | **TCP Communication** - Reliable client-server architecture | ✅ |
| 👥 | **Multi-Client Support** - Manage multiple machines simultaneously | ✅ |
| 💻 | **Modular Architecture** - Thread-safe, multi-file codebase | ✅ |
| 📸 | **4K Screenshots** - High-quality screen capture with dynamic compression | ✅ |
| 📷 | **Webcam Capture** - Real-time webcam snapshot directly to GUI | ✅ |
| 📁 | **Visual File Manager** - Browse, read, edit, delete remote files with GUI | ✅ |
| 📥📤 | **File Transfer** - Upload/download with progress tracking (50MB) | ✅ |
| 💬 | **Multi-Style Popups** - INFO / WARNING / ERROR / CYBER / OVERRIDE | ✅ |
| 🖥️ | **Live Screen Monitor** - Real-time remote desktop with full mouse & keyboard control | ✅ |
| 🖱️ | **Full Mouse Control** - Click, scroll, drag-drop, move on remote screen | ✅ |
| ⌨️ | **Hotkey Support** - Ctrl+C/V/Z/A/X/S/W/T/R forwarded to remote | ✅ |
| 🎯 | **OS-Specific Commands** - Smart buttons that adapt to Windows/Linux/Mac | ✅ |
| 🛡️ | **Anti-Scanner Protection** - Ghost connection rejection | ✅ |
| 🎤 | **Live Microphone Streaming** - Toggle start/stop with auto MP3 save | ✅ |
| ⌨️ | **Live Keylog Streaming** - Real-time keystroke capture with toggle | ✅ |
| 🎯 | **Remote Task Manager** - View and kill processes on client | ✅ |
| 📊 | **Live Performance Dashboard** - Real-time CPU, RAM, Disk monitor | ✅ |
| 🗺️ | **GeoLocation Tracker** - IP-based location with Google Maps link | ✅ |
| 👑 | **Privilege Inspector** - Token integrity level + UAC status display | ✅ |
| 🔥 | **UAC Bypass** - fodhelper.exe method for privilege escalation | ✅ |

</div>

---

## 🆕 What's New?

### v2.5 — Security & Intelligence Update *(Latest)*

* **🗺️ GeoLocation Tracker:** One-click IP geolocation using `ip-api.com`. Shows Country, City, ISP, Timezone, Proxy/VPN detection, and coordinates with **"Open in Google Maps"** button. Auto-detects public IP for localhost/LAN clients.
* **👑 Privilege Inspector:** Displays the client's exact Windows token integrity level (`Low / Medium / High / System`) using `whoami /groups`. Color-coded badge (🔴🟡🟢🔵) shows privilege at a glance.
* **🔥 UAC Bypass (fodhelper):** When client is in admin group but blocked by UAC (Medium integrity), a one-click **fodhelper.exe bypass** relaunches the client as **HIGH integrity** — no UAC prompt shown.
* **🐛 File Manager Path Bug Fixed:** Remote file browser now correctly compares paths using string normalization instead of server-side `os.path.abspath()` — previously always returned empty listing.
* **🐛 PRIV_INFO Routing Fixed:** JSON responses from `PRIV_INFO` and `UAC_BYPASS` are now correctly routed through the special command handler instead of being dumped raw into the terminal.

---

### v2.4 — Live Screen Monitor Controls

* **🖱️ Mouse Scroll:** Scroll wheel forwarded to remote screen (up/down).
* **🖱️ Drag & Drop:** Click-hold-drag now works on remote screen for file/UI interactions.
* **⌨️ Hotkeys:** `Ctrl+C`, `Ctrl+V`, `Ctrl+Z`, `Ctrl+A`, `Ctrl+X`, `Ctrl+S`, `Ctrl+W`, `Ctrl+T`, `Ctrl+R` all forwarded to client.

---

### v2.3 — Bug Fix Patch

* **🔔 Popup Topmost Fix:** Dialogs now always appear on top of all windows.
* **🖥️ Screen Monitor Stop Button Fixed:** `⏹ Stop Stream` now correctly sends `LIVE_SCREEN_STOP` to client.
* **🔁 Duplicate Flag Fixed:** Single shared `_screen_stream_active` variable across all modules.
* **⚙️ Subprocess Popup Fix:** Correctly handles both `.exe` and raw Python script launch modes.
* **🔐 Persistence Fix:** Registry entry now works for both frozen `.exe` and raw `.py` modes.

---

### v2.2 — Live Streaming Update

* **🎤 Live Microphone Streaming:** Toggle start/stop. Receives WAV and auto-prompts MP3 save.
* **⌨️ Live Keylog Streaming:** Real-time keystroke stream with toggle start/stop button.

---

### v2.0 — Major Release

* **Completely Modularized Backend:** `gui_globals.py`, `gui_network.py`, `gui_features.py`, `gui_commands.py`.
* **Webcam Support**, **Multi-Style Popups**, **Zero-Delay Terminal**, **Anti-Scanner Protection**.

---

## 🚀 Quick Start

<div align="center">
<img src="https://user-images.githubusercontent.com/74038190/212257472-08e52665-c503-4bd9-aa20-f5a4dae769b5.gif" width="100">
</div>

### 📦 Installation

> 💡 **Platform Note:** On Windows use `python`, on Linux/macOS use `python3`.

```bash
# 1️⃣ Clone the repository
git clone https://github.com/palnirupam/Remote-admin-tool.git
cd Remote-admin-tool

# 2️⃣ Install dependencies
pip install -r requirements.txt       # Windows
# pip3 install -r requirements.txt    # Linux / macOS

# 3️⃣ Configure client IP in client.py
# Edit SERVER_IP = "your_server_ip"
```

### ⚙️ Configuration

<details>
<summary>📝 Click to expand configuration steps</summary>

1. Open `client.py` in your editor
2. Locate the configuration section:
   ```python
   SERVER_IP = "127.0.0.1"  # 👈 Change this
   PORT = 5000
   ```
3. Update with your server's IP:
   - **Local testing**: `127.0.0.1`
   - **Same network**: `192.168.x.x`
   - **Remote**: Your public IP

</details>

### 🛠️ Building the Client Executable (.exe / Linux Binary)

Compile `client.py` into a standalone hidden executable — no Python needed on the target machine.

```bash
python advanced_build.py          # Windows
# python3 advanced_build.py       # Linux / macOS
```

- Completely **FREE** (no accounts, cards, or passwords required)
- Automatically downloads and configures the `bore` tunnel
- Injects public IP and Port → compiles `ClientRAT_Global.exe`
- Your original `client.py` stays safely configured for localhost!

> **🎯 IMPORTANT:** Final executable will be in the **`dist`** folder!

---

## 💡 Usage

### 🎨 GUI Server (Recommended)

```bash
# Start GUI server
python server_gui.py             # Windows
# python3 server_gui.py          # Linux / macOS

# On client machine(s)
python client.py                 # Windows
# python3 client.py              # Linux / macOS
```

---

## 🔥 Advanced Features

### 🗺️ GeoLocation Tracker

Click **"🗺️ GeoLocation"** after selecting a client:

- 🌍 Country, Region, City, ZIP
- 📍 GPS Coordinates (clickable → Google Maps)
- 📡 ISP & Organization name
- 🔒 Proxy / VPN / Datacenter detection
- 📶 Mobile data detection
- 🕐 Timezone

> Auto-detects public IP for LAN/localhost clients via `api.ipify.org`.

---

### 👑 Privilege Inspector + UAC Bypass

Click **"👑 Privilege"** after selecting a client:

```
┌──────────────────────────────────────────────┐
│ 👑  PRIVILEGE INSPECTOR       🟡 MEDIUM       │
├──────────────────────────────────────────────┤
│ 👤 Username      victim                      │
│ 🛡️ Admin Group   Yes ✅                       │
│ 🔒 UAC Enabled   Yes (ON)                    │
│ 🔑 Integrity     🟡 Medium                   │
│ ⚡ Elevated       No — MEDIUM token ⚠️        │
├──────────────────────────────────────────────┤
│  [🔥 Execute UAC Bypass (fodhelper)]          │
└──────────────────────────────────────────────┘
```

**UAC Bypass flow:**
1. Writes payload to `HKCU\Software\Classes\ms-settings\shell\open\command`
2. Triggers `fodhelper.exe` (Windows auto-elevated binary)
3. Client relaunches as **HIGH integrity** — no UAC prompt
4. New elevated connection appears in client list

**Integrity levels:**
| Badge | Level | Meaning |
|-------|-------|---------|
| 🔴 | Low | Sandbox / restricted |
| 🟡 | Medium | Standard user (UAC blocking) |
| 🟢 | High | Admin — full access |
| 🔵 | System | NT AUTHORITY\SYSTEM |

---

### 🖥️ Live Screen Monitor Controls

| Action | How |
|--------|-----|
| Left/Right/Middle click | Mouse button on screen |
| Scroll up/down | Mouse wheel |
| Drag & Drop | Click-hold-move |
| Hotkeys | `Ctrl+C/V/Z/A/X/S/W/T/R` |

---

### 📁 Visual File Manager

- Browse entire remote filesystem with GUI tree
- Double-click folders to navigate
- Right-click files: **Download / Edit / Delete**
- Built-in text editor with syntax support
- Supports both Windows and Linux paths

---

### 🎯 Screenshot Capture

```bash
SCREENSHOT     # Terminal command or click 📸 button
```

- 🎨 Adaptive quality (4K/2K/HD)
- 💾 Auto-save to `screenshots/` folder
- 🔍 View at 100% original size

---

### 🎤 Microphone & ⌨️ Keylogger

```bash
MIC_START      # Start recording
MIC_STOP       # Stop & save as WAV/MP3

KEYLOG_START   # Start live keystroke stream
KEYLOG_STOP    # Stop keylog
```

---

## 🔧 Troubleshooting

<details>
<summary>❌ Connection Failed</summary>

- ✅ Verify server is running
- ✅ Check `SERVER_IP` in client.py
- ✅ Ensure firewall allows port 5000
- ✅ Test with `ping <server_ip>`

</details>

<details>
<summary>❌ Port Already in Use</summary>

**Windows:**
```powershell
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

**Linux:**
```bash
lsof -i :5000
kill -9 <process_id>
```

</details>

<details>
<summary>❌ GeoLocation Shows Wrong Location</summary>

- If client is behind **VPN/Proxy**, location will reflect VPN server, not real location
- LAN clients auto-lookup public IP via `api.ipify.org`
- `127.0.0.1` → automatically resolved to machine's real public IP

</details>

<details>
<summary>❌ UAC Bypass Not Working</summary>

- ✅ Client must be on **Windows**
- ✅ User must be a member of the **Administrators group**
- ✅ **UAC must be enabled** (if UAC is off, bypass not needed anyway)
- ❌ If `is_admin: false` → user is a standard user, bypass impossible

</details>

---

## 🛡️ Security Notice

<div align="center">

### ⚠️ Educational & Authorized Use Only

<img src="https://img.shields.io/badge/Security-Educational%20Only-red?style=for-the-badge" alt="Security"/>

</div>

<div align="center">

### ⚖️ Disclaimer

**THE AUTHOR IS NOT RESPONSIBLE FOR ANY MISUSE OR DAMAGE CAUSED BY THIS SOFTWARE.**

By using this tool, you agree to:
- Use it **only on systems you own or have explicit written permission** to access
- Not use it for any illegal, malicious, or unauthorized purposes
- Accept full responsibility for your actions
- Understand that the author bears **NO LIABILITY** for consequences of use

**Use responsibly and ethically. Always obtain proper authorization!**

</div>

---

## 📁 Project Structure

```
📦 Remote-admin-tool
 ┣ 📜 server_gui.py        # Professional GUI server (Main Entry)
 ┣ 📜 server.py            # CLI server with advanced logging
 ┣ 📜 gui_globals.py       # Shared global state & thread-safe logging
 ┣ 📜 gui_network.py       # Multi-client TCP listener & socket manager
 ┣ 📜 gui_commands.py      # Command execution, response routing & handlers
 ┣ 📜 gui_features.py      # Screenshot, webcam, mic, keylog, file manager,
 ┃                         #   screen monitor, geolocation, privilege UI
 ┣ 📜 client.py            # Smart client — auto-reconnect, all handlers,
 ┃                         #   privilege info, UAC bypass, persistence
 ┣ 📜 advanced_build.py    # Auto-tunneling & .exe/binary compiler
 ┣ 📜 requirements.txt     # Python dependencies
 ┣ 📜 .gitignore           # Git ignore rules
 ┣ 📜 README.md            # This file
 ┗ 📖 USAGE_GUIDE.md       # Complete step-by-step guide
```

---

## 🎓 Learning Objectives

<div align="center">

<img src="https://img.shields.io/badge/Socket%20Programming-✓-blue?style=flat-square" alt="Socket"/>
<img src="https://img.shields.io/badge/Multi--Threading-✓-blue?style=flat-square" alt="Threading"/>
<img src="https://img.shields.io/badge/GUI%20Development-✓-blue?style=flat-square" alt="GUI"/>
<img src="https://img.shields.io/badge/UAC%20Bypass-✓-red?style=flat-square" alt="UAC"/>
<img src="https://img.shields.io/badge/Privilege%20Escalation-✓-red?style=flat-square" alt="PrivEsc"/>
<img src="https://img.shields.io/badge/Cross--Platform-✓-blue?style=flat-square" alt="Cross-Platform"/>

</div>

Perfect for learning:
- 🔌 TCP socket programming & multi-client architecture
- 🧵 Multi-threading and concurrency
- 🎨 Tkinter GUI development
- 🔐 Windows security — UAC, token integrity, privilege escalation
- 🌐 IP intelligence & OSINT (GeoLocation, ISP, proxy detection)
- 📁 File encoding, transfer, and remote filesystem navigation
- 🔧 Process management & system control

---

## 🤝 Contributing

Contributions are welcome!

**How to contribute:**
1. 🍴 Fork the repository
2. 🌿 Create feature branch: `git checkout -b feature/AmazingFeature`
3. 💾 Commit changes: `git commit -m 'Add AmazingFeature'`
4. 📤 Push to branch: `git push origin feature/AmazingFeature`
5. 🔃 Open a Pull Request

---

## 📜 License

<div align="center">

MIT License © 2024 Nirupam Pal

<img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License"/>

[📄 View Full License](LICENSE)

</div>

---

## 👨‍💻 Author

<div align="center">

<img src="https://user-images.githubusercontent.com/74038190/212284087-bbe7e430-757e-4901-90bf-4cd2ce3e1852.gif" width="100">

### Nirupam Pal

[![GitHub](https://img.shields.io/badge/GitHub-palnirupam-181717?style=for-the-badge&logo=github)](https://github.com/palnirupam)
[![Repository](https://img.shields.io/badge/Repository-Remote--admin--tool-blue?style=for-the-badge&logo=github)](https://github.com/palnirupam/Remote-admin-tool)

</div>

---

### ⭐ If you find this project helpful, please give it a star!

<img src="https://user-images.githubusercontent.com/74038190/212284115-f47cd8ff-2ffb-4b04-b5bf-4d1c14c0247f.gif" width="1000">

**Made with ❤️ for the cybersecurity community**

</div>
