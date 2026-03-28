<div align="center">

# 🖥️ Remote Administration Tool

<img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=32&duration=2800&pause=2000&color=00ADD8&center=true&vCenter=true&width=940&lines=Professional+Remote+Administration;Multi-Client+Management;Cross-Platform+Support;Built+with+Python" alt="Typing SVG" />

<p align="center">
  <img src="https://img.shields.io/badge/python-3.x-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python Version"/>
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg?style=for-the-badge&logo=windows&logoColor=white" alt="Platform"/>
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="License"/>
  <img src="https://img.shields.io/github/stars/palnirupam/Remote-admin-tool?style=for-the-badge&logo=github" alt="Stars"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Multi--Client-✓-success?style=flat-square" alt="Multi-Client"/>
  <img src="https://img.shields.io/badge/GUI%20Interface-✓-success?style=flat-square" alt="GUI"/>
  <img src="https://img.shields.io/badge/Screenshot-4K-success?style=flat-square" alt="Screenshot"/>
  <img src="https://img.shields.io/badge/File%20Transfer-✓-success?style=flat-square" alt="File Transfer"/>
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

#### 🎯 **For Developers**
- Clean, readable Python code
- Excellent learning resource
- Easy to customize
- Well-documented

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
| 💻 | **Dual Interface** - CLI and professional GUI options | ✅ |
| 📸 | **4K Screenshots** - High-quality screen capture | ✅ |
| 📁 | **File Transfer** - Upload/download with progress tracking | ✅ |
| ⚙️ | **System Control** - Restart, shutdown, lock operations | ✅ |
| 🎯 | **Process Management** - Find and terminate processes | ✅ |
| 📊 | **Activity Logging** - Complete audit trail | ✅ |
| ⌨️ | **Interactive Terminal** - Full keyboard shortcuts | ✅ |
| 🌐 | **Cross-Platform** - Windows & Linux support | ✅ |

</div>

---

## � Quick Start

<div align="center">
<img src="https://user-images.githubusercontent.com/74038190/212257472-08e52665-c503-4bd9-aa20-f5a4dae769b5.gif" width="100">
</div>

### 📦 Installation

```bash
# 1️⃣ Clone the repository
git clone https://github.com/palnirupam/Remote-admin-tool.git
cd Remote-admin-tool

# 2️⃣ Install dependencies (for GUI with screenshots)
pip install pillow mss

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

---

## 💡 Usage

### 🖥️ Option 1: CLI Server

<div align="center">
<img src="https://img.shields.io/badge/Terminal-000000?style=for-the-badge&logo=windows-terminal&logoColor=white" alt="Terminal"/>
</div>

```bash
# Start CLI server
python server.py

# On client machine
python client.py
```

**Features:**
- ⚡ Lightweight and fast
- 📝 Detailed logging to `server.log`
- 🔄 Auto-reconnect support
- 💾 Progress tracking for file transfers

---

### 🎨 Option 2: GUI Server (Recommended)

<div align="center">
<img src="https://img.shields.io/badge/GUI-Professional-blue?style=for-the-badge&logo=windows&logoColor=white" alt="GUI"/>
</div>

```bash
# Start GUI server
python server_gui.py

# On client machine(s)
python client.py
```

#### 🎯 GUI Features

<table>
<tr>
<td width="33%" align="center">

### 👥 Multi-Client
<img src="https://img.shields.io/badge/Clients-10%20Max-blue?style=flat-square" alt="Clients"/>

Manage up to 10 clients simultaneously with easy switching

</td>
<td width="33%" align="center">

### 📸 Screenshots
<img src="https://img.shields.io/badge/Quality-4K-green?style=flat-square" alt="4K"/>

Capture high-quality screenshots up to 4K resolution

</td>
<td width="33%" align="center">

### 📁 File Transfer
<img src="https://img.shields.io/badge/Size-50MB-orange?style=flat-square" alt="Size"/>

Upload/download files with progress tracking

</td>
</tr>
</table>

#### ⌨️ Keyboard Shortcuts

<div align="center">

| Shortcut | Action | Shortcut | Action |
|:--------:|:-------|:--------:|:-------|
| `↑` `↓` | Command history | `Tab` | Auto-complete |
| `Ctrl+C` | Copy/Clear | `Ctrl+V` | Paste |
| `Ctrl+L` | Clear terminal | `Ctrl+A` | Select all |
| `Ctrl+K` | Kill line | `Ctrl+U` | Clear line |

</div>

---

## 🖥️ Platform Support

<div align="center">
<img src="https://user-images.githubusercontent.com/74038190/212257454-16e3712e-945a-4ca2-b238-408ad0bf87e6.gif" width="100">
</div>

### 🪟 Windows

<details>
<summary>🔧 Click for Windows setup</summary>

**Firewall Configuration:**
```powershell
netsh advfirewall firewall add rule name="Remote Admin Tool" dir=in action=allow protocol=TCP localport=5000
```

**Common Commands:**
```bash
ipconfig          # Network information
whoami            # Current user
dir               # List files
systeminfo        # System details
tasklist          # Running processes
netstat -an       # Network connections
```

</details>

### 🐧 Linux

<details>
<summary>🔧 Click for Linux setup</summary>

**Firewall Configuration:**
```bash
# Using UFW
sudo ufw allow 5000/tcp

# Using iptables
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

**Common Commands:**
```bash
ifconfig          # Network information
whoami            # Current user
ls -la            # List files
uname -a          # System details
ps aux            # Running processes
netstat -tuln     # Network connections
```

**Auto-Install Dependencies:**
Client automatically installs required packages on first run!

</details>

---

## 📸 Advanced Features

<div align="center">
<img src="https://user-images.githubusercontent.com/74038190/212257465-7ce8d493-cac5-494e-982a-5a9deb852c4b.gif" width="100">
</div>

### 🎯 Screenshot Capture

```bash
# In terminal or click 📸 button
SCREENSHOT
```

**Features:**
- 🎨 Adaptive quality (4K/2K/HD)
- 💾 Auto-save to `screenshots/` folder
- 🔍 View at 100% original size
- 📊 Memory-safe for large captures

### 📁 File Transfer

**Download from client:**
```bash
# Windows
DOWNLOAD:C:\path\to\file.txt

# Linux
DOWNLOAD:/home/user/file.txt
```

**Upload to client:**
- Use GUI button for easy file selection
- Supports files up to 50MB
- Progress tracking included

### ⚙️ System Control

<table>
<tr>
<td width="50%">

**Windows:**
```bash
shutdown /r /t 0    # Restart
shutdown /s /t 0    # Shutdown
rundll32.exe user32.dll,LockWorkStation  # Lock
```

</td>
<td width="50%">

**Linux:**
```bash
reboot              # Restart
shutdown -h now     # Shutdown
gnome-screensaver-command -l  # Lock
```

</td>
</tr>
</table>

---

## 🔧 Troubleshooting

<div align="center">
<img src="https://user-images.githubusercontent.com/74038190/212257468-1e9a91f1-b626-4baa-b15d-5c385dfa7ed2.gif" width="100">
</div>

<details>
<summary>❌ Connection Failed</summary>

**Solutions:**
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
<summary>❌ Screenshot Not Working</summary>

**Solutions:**
- ✅ Install: `pip install pillow mss`
- ✅ Linux: `sudo apt install python3-pil python3-mss`
- ✅ Check display access permissions

</details>

---

## 🛡️ Security Notice

<div align="center">

### ⚠️ Educational Use Only

<img src="https://img.shields.io/badge/Security-Educational%20Only-red?style=for-the-badge" alt="Security"/>

</div>

**Current Limitations:**
- 🔓 No encryption (plain text)
- 🔓 No authentication
- 🔓 No input validation

**For Production Use:**
- ✅ SSH (Secure Shell)
- ✅ Ansible
- ✅ PowerShell Remoting

---

## 📁 Project Structure

```
📦 Remote-admin-tool
 ┣ 📜 server.py          # CLI server with advanced logging
 ┣ 📜 server_gui.py      # Professional GUI server
 ┣ 📜 client.py          # Smart client with auto-reconnect
 ┣ 📜 requirements.txt   # Python dependencies
 ┣ 📜 .gitignore         # Git ignore rules
 ┣ 📜 README.md          # This file
 ┗ 📖 USAGE_GUIDE.md     # Complete step-by-step guide
```

> 📖 **Need help?** Check [USAGE_GUIDE.md](USAGE_GUIDE.md) for detailed instructions!

---

## 🎓 Learning Objectives

<div align="center">

<img src="https://img.shields.io/badge/Socket%20Programming-✓-blue?style=flat-square" alt="Socket"/>
<img src="https://img.shields.io/badge/Multi--Threading-✓-blue?style=flat-square" alt="Threading"/>
<img src="https://img.shields.io/badge/GUI%20Development-✓-blue?style=flat-square" alt="GUI"/>
<img src="https://img.shields.io/badge/Cross--Platform-✓-blue?style=flat-square" alt="Cross-Platform"/>
<img src="https://img.shields.io/badge/File%20I%2FO-✓-blue?style=flat-square" alt="File IO"/>
<img src="https://img.shields.io/badge/Error%20Handling-✓-blue?style=flat-square" alt="Error Handling"/>

</div>

Perfect for learning:
- 🔌 TCP socket programming
- 🧵 Multi-threading and concurrency
- 🎨 Tkinter GUI development
- 🖥️ Cross-platform compatibility
- 📁 File encoding and transfer
- 🔧 Process management
- 📝 Logging and debugging

---

## 🤝 Contributing

<div align="center">
<img src="https://user-images.githubusercontent.com/74038190/212257460-738ff738-247f-4445-a718-cdd0ca76e2db.gif" width="100">
</div>

Contributions are welcome! 

**How to contribute:**
1. 🍴 Fork the repository
2. 🌿 Create feature branch: `git checkout -b feature/AmazingFeature`
3. 💾 Commit changes: `git commit -m 'Add AmazingFeature'`
4. 📤 Push to branch: `git push origin feature/AmazingFeature`
5. 🔃 Open a Pull Request

**Ideas for contributions:**
- 🔐 Add SSL/TLS encryption
- 🔑 Implement authentication system
- 🌐 Add web-based interface
- 📱 Mobile client support
- 🎨 Theme customization
- 📊 Performance dashboard

---

## 📊 Statistics

<div align="center">

<img src="https://github-readme-stats.vercel.app/api/pin/?username=palnirupam&repo=Remote-admin-tool&theme=tokyonight" alt="Repo Stats"/>

</div>

---

## 📜 License

<div align="center">

MIT License © 2024 Nirupam Pal

<img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License"/>

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

<div align="center">

### 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=palnirupam/Remote-admin-tool&type=Date)](https://star-history.com/#palnirupam/Remote-admin-tool&Date)

---

### ⭐ If you find this project helpful, please give it a star!

<img src="https://user-images.githubusercontent.com/74038190/212284115-f47cd8ff-2ffb-4b04-b5bf-4d1c14c0247f.gif" width="1000">

**Made with ❤️ for the developer community**

</div>
