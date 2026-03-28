# 📖 Complete Usage Guide - Step by Step

## 🎯 Table of Contents
- [Windows Setup](#-windows-setup)
- [Linux Setup](#-linux-setup)
- [Using CLI Server](#-using-cli-server)
- [Using GUI Server](#-using-gui-server)
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
pip install pillow mss
```

### Step 4: Configure Firewall

Open Command Prompt as Administrator and run:
```cmd
netsh advfirewall firewall add rule name="Remote Admin Tool" dir=in action=allow protocol=TCP localport=5000
```

### Step 5: Configure Client IP

1. Open `client.py` in Notepad
2. Find this line:
   ```python
   SERVER_IP = "127.0.0.1"
   ```
3. Change to your server's IP:
   - **Same PC testing**: Keep `127.0.0.1`
   - **Same network**: Use `192.168.x.x` (your server's local IP)
   - **Remote**: Use your public IP

4. Save the file

### Step 6: Find Your Server IP

**For local network:**
```cmd
ipconfig
```
Look for "IPv4 Address" under your active network adapter (e.g., `192.168.1.100`)

### Step 7: Run the Server

**Option A: CLI Server**
```cmd
python server.py
```

**Option B: GUI Server (Recommended)**
```cmd
python server_gui.py
```
Then click "🚀 Start Server" button

### Step 8: Run the Client

On the client machine (or another Command Prompt):
```cmd
python client.py
```

You should see: `✓ Connected to server`

### Step 9: Execute Commands

**In CLI Server:**
Type commands directly:
```cmd
Remote-Admin> whoami
Remote-Admin> dir
Remote-Admin> ipconfig
```

**In GUI Server:**
- Click command buttons OR
- Type directly in the terminal

---

## 🐧 Linux Setup

### Step 1: Install Python

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 python3-pip
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip
```

Verify installation:
```bash
python3 --version
```

### Step 2: Download the Tool

```bash
git clone https://github.com/palnirupam/Remote-admin-tool.git
cd Remote-admin-tool
```

### Step 3: Install Dependencies

**Ubuntu/Debian:**
```bash
pip3 install pillow mss
# OR
sudo apt install python3-pil python3-mss
```

**Fedora:**
```bash
pip3 install pillow mss
```

**Arch:**
```bash
pip3 install pillow mss
```

### Step 4: Configure Firewall

**Using UFW (Ubuntu/Debian):**
```bash
sudo ufw allow 5000/tcp
sudo ufw reload
```

**Using firewalld (Fedora/RHEL):**
```bash
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

**Using iptables:**
```bash
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo iptables-save
```

### Step 5: Configure Client IP

```bash
nano client.py
# OR
vim client.py
# OR
gedit client.py
```

Find and change:
```python
SERVER_IP = "127.0.0.1"  # Change this
```

To your server's IP:
- **Same PC**: Keep `127.0.0.1`
- **Same network**: Use `192.168.x.x`
- **Remote**: Use public IP

Save: `Ctrl+O`, `Enter`, `Ctrl+X` (nano)

### Step 6: Find Your Server IP

```bash
# Modern Linux
ip addr show

# OR older systems
ifconfig
```

Look for `inet` address (e.g., `192.168.1.100`)

### Step 7: Run the Server

**Option A: CLI Server**
```bash
python3 server.py
```

**Option B: GUI Server**
```bash
python3 server_gui.py
```
Then click "🚀 Start Server"

### Step 8: Run the Client

On client machine:
```bash
python3 client.py
```

You should see: `✓ Connected to server`

### Step 9: Execute Commands

**In CLI Server:**
```bash
Remote-Admin> whoami
Remote-Admin> ls -la
Remote-Admin> ps aux
```

**In GUI Server:**
- Click command buttons OR
- Type directly in terminal

---

## 💻 Using CLI Server

### Starting the Server

```bash
# Windows
python server.py

# Linux
python3 server.py
```

### Available Commands

| Command | Description |
|---------|-------------|
| `menu` | Show command menu |
| `clients` | List all connected clients |
| `switch` | Switch to different client |
| `info` | Show current client info |
| `screenshot` | Capture client screenshot |
| `download` | Download file from client |
| `upload` | Upload file to client |
| `exit` | Disconnect current client |

### Quick Command Shortcuts

| Shortcut | Command |
|----------|---------|
| `1` | ipconfig (Windows) / ifconfig (Linux) |
| `2` | whoami |
| `3` | dir (Windows) / ls (Linux) |
| `4` | systeminfo (Windows) / uname -a (Linux) |
| `5` | tasklist (Windows) / ps aux (Linux) |
| `6` | cd (show current directory) |

### Example Session

```bash
Remote-Admin> 2
DESKTOP-ABC\User

Remote-Admin> 3
 Volume in drive C is Windows
 Directory of C:\Users\User
...

Remote-Admin> screenshot
📸 Requesting screenshot...
  Receiving... 512KB
✓ Screenshot saved: screenshots/screenshot_DESKTOP-ABC_20240315_143022.png (2.45MB)

Remote-Admin> clients
================================================================================
CONNECTED CLIENTS (2/10):
================================================================================
  [1] 🟢 ACTIVE DESKTOP-ABC - 192.168.1.100:54321
      OS: Windows 10 | User: User
      Connected: 2024-03-15 14:25:30
  [2] ⚪ LAPTOP-XYZ - 192.168.1.101:54322
      OS: Linux | User: admin
      Connected: 2024-03-15 14:26:15
================================================================================

Remote-Admin> switch
Select client number: 2
✓ Switched to: LAPTOP-XYZ (192.168.1.101)

Remote-Admin> exit
✓ Disconnecting client...
```

---

## 🎨 Using GUI Server

### Starting the GUI

```bash
# Windows
python server_gui.py

# Linux
python3 server_gui.py
```

### Step-by-Step GUI Usage

#### 1. Start the Server

1. Click **"🚀 Start Server"** button (top right)
2. Status bar will show: `Server listening...`
3. Button changes to: `✓ Server Running` (green)

#### 2. Connect Clients

On each client machine, run:
```bash
python client.py    # Windows
python3 client.py   # Linux
```

Clients will appear in the **"CONNECTED CLIENTS"** list automatically.

#### 3. Select a Client

- Click on any client in the list
- Selected client shows 🟢 green indicator
- All command buttons become enabled

#### 4. Execute Commands

**Method 1: Click Buttons**
- Click any command button (e.g., "🌐 Network Info")
- Output appears in terminal instantly

**Method 2: Type in Terminal**
- Click in the terminal area
- Type command directly: `whoami`
- Press `Enter` to execute

#### 5. Use Advanced Features

**Screenshot:**
1. Click **"📸 Screenshot"** button
2. Wait for capture (progress shown)
3. Screenshot window opens automatically
4. Click **"💾 Save 4K"** to save
5. Click **"🔍 100% Size"** for original resolution

**Download File:**
1. Click **"📥 Download File"** button
2. Enter file path on client:
   - Windows: `C:\Users\User\file.txt`
   - Linux: `/home/user/file.txt`
3. Choose save location
4. File downloads to `downloads/` folder

**Upload File:**
1. Click **"📤 Upload File"** button
2. Select file from your computer
3. File uploads to client's current directory
4. Confirmation appears in terminal

#### 6. System Control

**Restart Client:**
1. Click **"🔄 Restart System"**
2. Confirm: Click "Yes"
3. Client PC restarts immediately

**Shutdown Client:**
1. Click **"⏻ Shutdown System"**
2. Confirm: Click "Yes"
3. Client PC shuts down

**Lock Screen:**
1. Click **"🔒 Lock Workstation"**
2. Client screen locks immediately

#### 7. Process Management

**Find Process:**
1. Click **"🔍 Find Process"**
2. Enter process name (e.g., `notepad`)
3. Results show in terminal

**Kill Process:**
1. Click **"❌ Kill Process"**
2. Enter process name (e.g., `notepad.exe`)
3. Confirm: Click "Yes"
4. Process terminates

#### 8. Switch Between Clients

- Click any client in the list
- Active client changes instantly
- Commands automatically adapt to client's OS

#### 9. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `↑` `↓` | Navigate command history |
| `Tab` | Auto-complete commands |
| `Ctrl+C` | Copy selection / Clear input |
| `Ctrl+V` | Paste |
| `Ctrl+L` | Clear terminal |
| `Ctrl+A` | Select all |
| `Ctrl+K` | Kill line |
| `Ctrl+U` | Clear line |

#### 10. Stop the Server

1. Click **"⏹ Stop Server"** button
2. Confirm: Click "Yes"
3. All clients disconnect
4. Server stops

---

## 📝 Common Commands

### Windows Commands

```cmd
# Network Information
ipconfig
ipconfig /all
netstat -an

# System Information
systeminfo
whoami
hostname

# File Operations
dir
cd C:\Users
mkdir newfolder
copy file.txt backup.txt
del file.txt

# Process Management
tasklist
tasklist | findstr notepad
taskkill /F /IM notepad.exe

# System Control
shutdown /r /t 0    # Restart
shutdown /s /t 0    # Shutdown
```

### Linux Commands

```bash
# Network Information
ifconfig
ip addr
netstat -tuln

# System Information
uname -a
whoami
hostname
lsb_release -a

# File Operations
ls -la
cd /home/user
mkdir newfolder
cp file.txt backup.txt
rm file.txt

# Process Management
ps aux
ps aux | grep firefox
kill -9 <PID>
killall firefox

# System Control
reboot              # Restart
shutdown -h now     # Shutdown
```

### Cross-Platform Commands

These work on both Windows and Linux (auto-converted):

```bash
whoami              # Current user
cd                  # Current directory
screenshot          # Capture screen
download            # Download file
upload              # Upload file
sysinfo             # System information
```

---

## 🔧 Troubleshooting

### Problem: Client Can't Connect

**Check 1: Server Running?**
```bash
# Make sure server is running
python server.py
# OR
python server_gui.py
```

**Check 2: Correct IP?**
```python
# In client.py, verify:
SERVER_IP = "192.168.1.100"  # Your server's IP
```

**Check 3: Firewall?**
```bash
# Windows - Check firewall rule exists
netsh advfirewall firewall show rule name="Remote Admin Tool"

# Linux - Check port is open
sudo ufw status
```

**Check 4: Network Connection?**
```bash
# Test connectivity
ping 192.168.1.100
```

### Problem: Port Already in Use

**Windows:**
```cmd
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process
taskkill /PID <process_id> /F
```

**Linux:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <process_id>
```

### Problem: Screenshot Not Working

**Solution 1: Install Dependencies**
```bash
# Windows
pip install pillow mss

# Linux
pip3 install pillow mss
# OR
sudo apt install python3-pil python3-mss
```

**Solution 2: Check Display Access**
- Linux: Ensure client has X11 display access
- Windows: Run as Administrator if needed

### Problem: File Transfer Fails

**Check 1: File Path Correct?**
```bash
# Windows - Use backslashes
C:\Users\User\file.txt

# Linux - Use forward slashes
/home/user/file.txt
```

**Check 2: File Size?**
- Maximum file size: 50MB
- Larger files will be rejected

**Check 3: Permissions?**
- Ensure client has read/write permissions
- Linux: Check with `ls -l filename`

### Problem: Commands Not Working

**Check 1: Client OS?**
- Windows commands won't work on Linux client
- Linux commands won't work on Windows client
- Use cross-platform commands when possible

**Check 2: Command Syntax?**
```bash
# Correct
tasklist

# Incorrect
tasklist /svc /fi "STATUS eq running"  # Too complex
```

### Problem: GUI Not Opening

**Solution 1: Install Tkinter**
```bash
# Ubuntu/Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Windows - Already included with Python
```

**Solution 2: Check Display**
```bash
# Linux - Ensure DISPLAY is set
echo $DISPLAY
export DISPLAY=:0
```

---

## 🎓 Tips & Best Practices

### Security Tips

1. **Use on trusted networks only**
2. **Change default port** if needed:
   ```python
   PORT = 5000  # Change to any available port
   ```
3. **Monitor server.log** for suspicious activity
4. **Don't use on public networks** without VPN

### Performance Tips

1. **Close unused clients** to free resources
2. **Use CLI server** for better performance
3. **Limit screenshot frequency** (large data transfer)
4. **Keep file transfers under 50MB**

### Usage Tips

1. **Test locally first** (127.0.0.1)
2. **Use GUI for beginners**, CLI for advanced users
3. **Check logs** when troubleshooting
4. **Use Tab completion** in GUI terminal
5. **Save important outputs** using menu options

---

## 📞 Getting Help

If you encounter issues:

1. **Check this guide** first
2. **Review server.log** for errors
3. **Check GitHub Issues**: https://github.com/palnirupam/Remote-admin-tool/issues
4. **Open new issue** with:
   - Your OS (Windows/Linux)
   - Python version
   - Error message
   - Steps to reproduce

---

<div align="center">

**Happy Remote Administration! 🚀**

Made with ❤️ by [Nirupam Pal](https://github.com/palnirupam)

</div>
