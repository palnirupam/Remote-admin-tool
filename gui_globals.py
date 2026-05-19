"""
gui_globals.py - Shared global state for Remote Admin Tool GUI
All modules import from here to avoid circular imports.
"""
import threading

# ── Network Config ──────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 5000

# ── Shared State ────────────────────────────────────────────────
clients = {}               # {client_id: {conn, addr, info}}
active_client_id = None
clients_lock = threading.Lock()
server_running = False
server_socket = None
stop_monitoring = False
command_history = []
history_index = -1

# ── Keylog Live-Stream State ──────────────────────────────────
keylog_active = False
keylog_button = None

# ── Microphone Live-Stream State ──────────────────────────────
mic_active = False
mic_button = None

# ── Widget References (set by server_gui.py after creation) ─────
root = None
terminal_output = None
log_text = None
client_listbox = None
status_icon = None
status_text = None
connect_btn = None
stop_server_btn = None
disconnect_btn = None
command_buttons = []
advanced_buttons = []
commands_container = None


# ── Global Logging Function ──
import tkinter as tk
import threading
from datetime import datetime

def log_message(message, level="INFO"):
    """Thread-safe global logger."""
    if not log_text:
        return
    if threading.current_thread() != threading.main_thread():
        root.after(0, lambda: log_message(message, level))
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    log_text.config(state="normal")
    log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")

    if level == "INFO":
        log_text.insert(tk.END, f"{message}\n", "info")
    elif level == "SUCCESS":
        log_text.insert(tk.END, f"{message}\n", "success")
    elif level == "ERROR":
        log_text.insert(tk.END, f"{message}\n", "error")
    elif level == "WARNING":
        log_text.insert(tk.END, f"{message}\n", "warning")

    log_text.see(tk.END)
    log_text.config(state="disabled")
