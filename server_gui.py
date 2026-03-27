import socket
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
from datetime import datetime

HOST = "0.0.0.0"
PORT = 5000

conn = None
server_socket = None
connected_clients = []
command_history = []
animation_running = False
progress_value = 0

def log_message(message, level="INFO"):
    """Add timestamped log message with fade-in animation"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
    
    if level == "INFO":
        log_text.insert(tk.END, f"ℹ️  {message}\n", "info")
    elif level == "SUCCESS":
        log_text.insert(tk.END, f"✓  {message}\n", "success")
    elif level == "ERROR":
        log_text.insert(tk.END, f"✗  {message}\n", "error")
    elif level == "WARNING":
        log_text.insert(tk.END, f"⚠  {message}\n", "warning")
    
    log_text.see(tk.END)
    log_text.update()

def update_status(text, color, icon):
    """Update status bar with icon and color"""
    status_icon.config(text=icon)
    status_text.config(text=text, foreground=color)

def animate_status_icon():
    """Animate status icon while waiting"""
    global animation_running
    icons = ["⏳", "⌛"]
    index = 0
    
    while animation_running:
        status_icon.config(text=icons[index % len(icons)])
        index += 1
        time.sleep(0.5)

def animate_progress():
    """Animate progress bar"""
    global progress_value
    
    for i in range(101):
        if not animation_running:
            break
        progress_value = i
        progress_bar['value'] = i
        root.update_idletasks()
        time.sleep(0.02)
    
    progress_bar['value'] = 0

def pulse_button(button, original_bg):
    """Create pulse effect on button"""
    colors = [original_bg, "#FFFFFF", original_bg]
    for color in colors:
        try:
            button.config(bg=color)
            root.update()
            time.sleep(0.1)
        except:
            break

def start_server():
    global conn, server_socket, animation_running
    
    if conn is not None:
        messagebox.showwarning("Connection Active", "Already connected to a client!")
        return
    
    def server_thread():
        global conn, server_socket, animation_running
        try:
            server_socket = socket.socket()
            server_socket.bind((HOST, PORT))
            server_socket.listen(1)
            
            log_message(f"Server started on {HOST}:{PORT}", "SUCCESS")
            
            # Start animations
            animation_running = True
            threading.Thread(target=animate_status_icon, daemon=True).start()
            threading.Thread(target=animate_progress, daemon=True).start()
            
            update_status("Waiting for client connection...", "#FFA726", "⏳")
            connect_btn.config(state="disabled", text="⏳ Connecting...")
            progress_bar.pack(fill="x", padx=20, pady=(0, 10))
            
            conn, addr = server_socket.accept()
            
            # Stop animations
            animation_running = False
            progress_bar.pack_forget()
            
            client_info = f"{addr[0]}:{addr[1]}"
            connected_clients.append(client_info)
            
            log_message(f"Client connected from {client_info}", "SUCCESS")
            update_status(f"Connected to {client_info}", "#66BB6A", "✓")
            
            # Pulse effect on connect button
            connect_btn.config(state="normal", text="🔌 Connected", bg="#43A047")
            threading.Thread(target=lambda: pulse_button(connect_btn, "#43A047"), daemon=True).start()
            
            disconnect_btn.config(state="normal")
            
            # Animate button activation
            for i, btn in enumerate(command_buttons):
                root.after(i * 50, lambda b=btn: b.config(state="normal"))
            
            custom_entry.config(state="normal")
            execute_btn.config(state="normal")
                
        except Exception as e:
            animation_running = False
            progress_bar.pack_forget()
            log_message(f"Server error: {str(e)}", "ERROR")
            update_status("Connection failed", "#EF5350", "✗")
            connect_btn.config(state="normal", text="🔌 Connect")
    
    threading.Thread(target=server_thread, daemon=True).start()

def send_command(cmd, cmd_name):
    if conn is None:
        messagebox.showerror("No Connection", "Please connect to a client first!")
        return
    
    try:
        output_box.delete("1.0", tk.END)
        
        # Animated typing effect for header
        header_text = "╔" + "═"*78 + "╗\n"
        for char in header_text:
            output_box.insert(tk.END, char, "border")
            output_box.update()
            time.sleep(0.001)
        
        output_box.insert(tk.END, f"  COMMAND: {cmd_name}\n", "cmd_header")
        output_box.insert(tk.END, f"  EXECUTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", "timestamp_output")
        
        footer_text = "╚" + "═"*78 + "╝\n\n"
        for char in footer_text:
            output_box.insert(tk.END, char, "border")
            output_box.update()
            time.sleep(0.001)
        
        # Show loading animation
        loading_label.config(text="⏳ Executing command...")
        loading_label.pack(pady=5)
        root.update()
        
        log_message(f"Executing command: {cmd}", "INFO")
        command_history.append({"cmd": cmd, "time": datetime.now().strftime('%H:%M:%S')})
        
        conn.send(cmd.encode())

        if cmd == "exit":
            loading_label.pack_forget()
            disconnect_client()
            return

        data = conn.recv(16384)
        output = data.decode(errors="ignore")
        
        # Hide loading animation
        loading_label.pack_forget()
        
        if output.strip():
            # Animated text insertion
            lines = output.split('\n')
            for line in lines:
                output_box.insert(tk.END, line + '\n', "output")
                output_box.see(tk.END)
                output_box.update()
                time.sleep(0.01)
            output_box.insert(tk.END, "\n")
        else:
            output_box.insert(tk.END, "(No output returned)\n\n", "no_output")
        
        # Footer with animation
        separator = "─"*80 + "\n"
        for char in separator:
            output_box.insert(tk.END, char, "separator")
            output_box.update()
            time.sleep(0.001)
        
        output_box.insert(tk.END, "✓ Command executed successfully\n", "success_msg")
        
        log_message(f"Command completed: {cmd}", "SUCCESS")

    except Exception as e:
        loading_label.pack_forget()
        output_box.insert(tk.END, f"\n\n❌ ERROR: {str(e)}\n", "error_msg")
        log_message(f"Command failed: {str(e)}", "ERROR")

def send_custom_command():
    cmd = custom_entry.get().strip()
    if not cmd:
        messagebox.showwarning("Empty Command", "Please enter a command!")
        return
    
    send_command(cmd, cmd)
    custom_entry.delete(0, tk.END)

def clear_output():
    output_box.delete("1.0", tk.END)
    log_message("Output cleared", "INFO")

def disconnect_client():
    global conn
    if conn:
        try:
            conn.send("exit".encode())
            conn.close()
        except:
            pass
        conn = None
        
        log_message("Client disconnected", "WARNING")
        update_status("Disconnected", "#FF7043", "⚠")
        
        connect_btn.config(state="normal", text="🔌 Connect", bg="#1976D2")
        disconnect_btn.config(state="disabled")
        
        for btn in command_buttons:
            btn.config(state="disabled")
        
        custom_entry.config(state="disabled")
        execute_btn.config(state="disabled")

def save_output():
    """Save output to file"""
    content = output_box.get("1.0", tk.END)
    if content.strip():
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, "w") as f:
                f.write(content)
            log_message(f"Output saved to {filename}", "SUCCESS")
    else:
        messagebox.showinfo("Empty Output", "No output to save!")

def show_about():
    """Show about dialog"""
    about_window = tk.Toplevel(root)
    about_window.title("About")
    about_window.geometry("400x300")
    about_window.configure(bg="#1E1E1E")
    about_window.resizable(False, False)
    
    tk.Label(
        about_window,
        text="🖥️",
        font=("Segoe UI", 48),
        bg="#1E1E1E",
        fg="#FFFFFF"
    ).pack(pady=20)
    
    tk.Label(
        about_window,
        text="Remote Administration Tool",
        font=("Segoe UI", 14, "bold"),
        bg="#1E1E1E",
        fg="#FFFFFF"
    ).pack()
    
    tk.Label(
        about_window,
        text="Version 2.0 Enterprise Edition",
        font=("Segoe UI", 10),
        bg="#1E1E1E",
        fg="#9E9E9E"
    ).pack(pady=5)
    
    tk.Label(
        about_window,
        text="Professional remote system management\nbuilt with Python",
        font=("Segoe UI", 9),
        bg="#1E1E1E",
        fg="#CCCCCC",
        justify="center"
    ).pack(pady=15)
    
    tk.Label(
        about_window,
        text="© 2026 Nirupam Pal\nAll rights reserved",
        font=("Segoe UI", 9),
        bg="#1E1E1E",
        fg="#757575",
        justify="center"
    ).pack(pady=10)
    
    tk.Button(
        about_window,
        text="Close",
        command=about_window.destroy,
        font=("Segoe UI", 10),
        bg="#1976D2",
        fg="white",
        relief="flat",
        padx=30,
        pady=8,
        cursor="hand2"
    ).pack(pady=15)


# Create main window
root = tk.Tk()
root.title("Remote Administration Tool - Enterprise Edition")
root.geometry("1200x800")
root.configure(bg="#F5F5F5")
root.minsize(1000, 700)

# Menu Bar
menubar = tk.Menu(root, bg="#FFFFFF", fg="#212121")
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0, bg="#FFFFFF", fg="#212121")
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Save Output", command=save_output)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

tools_menu = tk.Menu(menubar, tearoff=0, bg="#FFFFFF", fg="#212121")
menubar.add_cascade(label="Tools", menu=tools_menu)
tools_menu.add_command(label="Clear Output", command=clear_output)
tools_menu.add_command(label="Clear Logs", command=lambda: log_text.delete("1.0", tk.END))

help_menu = tk.Menu(menubar, tearoff=0, bg="#FFFFFF", fg="#212121")
menubar.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="About", command=show_about)

# Top Bar
top_bar = tk.Frame(root, bg="#1976D2", height=60)
top_bar.pack(fill="x")
top_bar.pack_propagate(False)

# Logo and Title
title_frame = tk.Frame(top_bar, bg="#1976D2")
title_frame.pack(side="left", padx=20, pady=10)

tk.Label(
    title_frame,
    text="🖥️",
    font=("Segoe UI", 24),
    bg="#1976D2",
    fg="#FFFFFF"
).pack(side="left", padx=(0, 10))

title_text_frame = tk.Frame(title_frame, bg="#1976D2")
title_text_frame.pack(side="left")

tk.Label(
    title_text_frame,
    text="Remote Administration Tool",
    font=("Segoe UI", 16, "bold"),
    bg="#1976D2",
    fg="#FFFFFF"
).pack(anchor="w")

tk.Label(
    title_text_frame,
    text="Enterprise Edition v2.0",
    font=("Segoe UI", 9),
    bg="#1976D2",
    fg="#BBDEFB"
).pack(anchor="w")

# Connection Controls
connection_frame = tk.Frame(top_bar, bg="#1976D2")
connection_frame.pack(side="right", padx=20)

connect_btn = tk.Button(
    connection_frame,
    text="🔌 Connect",
    command=start_server,
    font=("Segoe UI", 10, "bold"),
    bg="#1976D2",
    fg="white",
    activebackground="#1565C0",
    activeforeground="white",
    relief="solid",
    bd=2,
    padx=20,
    pady=8,
    cursor="hand2",
    highlightthickness=0
)
connect_btn.pack(side="left", padx=5)

disconnect_btn = tk.Button(
    connection_frame,
    text="🔌 Disconnect",
    command=disconnect_client,
    font=("Segoe UI", 10),
    bg="#E53935",
    fg="white",
    activebackground="#C62828",
    activeforeground="white",
    relief="solid",
    bd=2,
    padx=20,
    pady=8,
    cursor="hand2",
    state="disabled",
    highlightthickness=0
)
disconnect_btn.pack(side="left", padx=5)

# Status Bar
status_bar = tk.Frame(root, bg="#FFFFFF", height=40, relief="flat", bd=1)
status_bar.pack(fill="x")
status_bar.pack_propagate(False)

status_left = tk.Frame(status_bar, bg="#FFFFFF")
status_left.pack(side="left", padx=15, pady=8)

status_icon = tk.Label(
    status_left,
    text="⚪",
    font=("Segoe UI", 12),
    bg="#FFFFFF"
)
status_icon.pack(side="left", padx=(0, 8))

status_text = tk.Label(
    status_left,
    text="Not Connected",
    font=("Segoe UI", 10),
    bg="#FFFFFF",
    fg="#757575"
)
status_text.pack(side="left")

status_right = tk.Frame(status_bar, bg="#FFFFFF")
status_right.pack(side="right", padx=15, pady=8)

tk.Label(
    status_right,
    text=f"Port: {PORT}",
    font=("Segoe UI", 9),
    bg="#FFFFFF",
    fg="#757575"
).pack(side="left", padx=10)

tk.Label(
    status_right,
    text="●",
    font=("Segoe UI", 12),
    bg="#FFFFFF",
    fg="#66BB6A"
).pack(side="left", padx=5)

tk.Label(
    status_right,
    text="Server Ready",
    font=("Segoe UI", 9),
    bg="#FFFFFF",
    fg="#757575"
).pack(side="left")

# Main Container
main_container = tk.Frame(root, bg="#F5F5F5")
main_container.pack(fill="both", expand=True, padx=0, pady=0)

# Left Panel - Commands
left_panel = tk.Frame(main_container, bg="#FFFFFF", width=350, relief="flat", bd=1)
left_panel.pack(side="left", fill="both", padx=(10, 5), pady=10)
left_panel.pack_propagate(False)

# Commands Header
tk.Label(
    left_panel,
    text="QUICK COMMANDS",
    font=("Segoe UI", 11, "bold"),
    bg="#FFFFFF",
    fg="#424242"
).pack(anchor="w", padx=20, pady=(20, 15))

# Progress bar for connection (hidden by default)
progress_bar = ttk.Progressbar(
    left_panel,
    mode='determinate',
    length=300
)

# Command Buttons Container
commands_container = tk.Frame(left_panel, bg="#FFFFFF")
commands_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

command_buttons = []

commands = [
    ("Network Configuration", "ipconfig", "🌐", "#2196F3"),
    ("Current User Info", "whoami", "👤", "#9C27B0"),
    ("Directory Listing", "dir", "📁", "#FF9800"),
    ("System Information", "systeminfo", "💻", "#4CAF50"),
    ("Running Processes", "tasklist", "📊", "#00BCD4"),
    ("Network Statistics", "netstat -an", "📡", "#3F51B5"),
    ("Environment Variables", "set", "⚙️", "#795548"),
    ("Disk Information", "wmic logicaldisk get name,size,freespace", "💾", "#607D8B")
]

for i, (text, cmd, icon, color) in enumerate(commands):
    btn_frame = tk.Frame(commands_container, bg="#FFFFFF")
    btn_frame.pack(fill="x", pady=4)
    
    btn = tk.Button(
        btn_frame,
        text=f"{icon}  {text}",
        command=lambda c=cmd, t=text: send_command(c, t),
        font=("Segoe UI", 10),
        bg=color,
        fg="white",
        activebackground=color,
        activeforeground="white",
        relief="flat",
        padx=15,
        pady=12,
        cursor="hand2",
        state="disabled",
        anchor="w"
    )
    btn.pack(fill="x")
    command_buttons.append(btn)

# Custom Command Section
custom_section = tk.Frame(left_panel, bg="#F5F5F5", relief="flat")
custom_section.pack(fill="x", padx=15, pady=(10, 20))

tk.Label(
    custom_section,
    text="CUSTOM COMMAND",
    font=("Segoe UI", 9, "bold"),
    bg="#F5F5F5",
    fg="#424242"
).pack(anchor="w", padx=10, pady=(10, 8))

custom_entry = tk.Entry(
    custom_section,
    font=("Consolas", 10),
    bg="#FFFFFF",
    fg="#212121",
    insertbackground="#1976D2",
    relief="solid",
    bd=1,
    state="disabled"
)
custom_entry.pack(fill="x", padx=10, pady=(0, 10), ipady=8)
custom_entry.bind("<Return>", lambda e: send_custom_command())

execute_btn = tk.Button(
    custom_section,
    text="▶  Execute Command",
    command=send_custom_command,
    font=("Segoe UI", 10, "bold"),
    bg="#4CAF50",
    fg="white",
    activebackground="#45A049",
    activeforeground="white",
    relief="flat",
    padx=15,
    pady=10,
    cursor="hand2",
    state="disabled"
)
execute_btn.pack(fill="x", padx=10, pady=(0, 10))


# Right Panel - Output and Logs
right_panel = tk.Frame(main_container, bg="#F5F5F5")
right_panel.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)

# Output Section
output_section = tk.Frame(right_panel, bg="#FFFFFF", relief="flat", bd=1)
output_section.pack(fill="both", expand=True, pady=(0, 10))

output_header = tk.Frame(output_section, bg="#FAFAFA", height=45)
output_header.pack(fill="x")
output_header.pack_propagate(False)

tk.Label(
    output_header,
    text="COMMAND OUTPUT",
    font=("Segoe UI", 10, "bold"),
    bg="#FAFAFA",
    fg="#424242"
).pack(side="left", padx=20, pady=12)

tk.Button(
    output_header,
    text="💾 Save",
    command=save_output,
    font=("Segoe UI", 9),
    bg="#FAFAFA",
    fg="#1976D2",
    activebackground="#EEEEEE",
    relief="flat",
    padx=15,
    pady=5,
    cursor="hand2"
).pack(side="right", padx=5)

tk.Button(
    output_header,
    text="🗑️ Clear",
    command=clear_output,
    font=("Segoe UI", 9),
    bg="#FAFAFA",
    fg="#757575",
    activebackground="#EEEEEE",
    relief="flat",
    padx=15,
    pady=5,
    cursor="hand2"
).pack(side="right", padx=5)

output_box = scrolledtext.ScrolledText(
    output_section,
    font=("Consolas", 10),
    bg="#1E1E1E",
    fg="#D4D4D4",
    insertbackground="white",
    relief="flat",
    wrap="word",
    padx=15,
    pady=15
)
output_box.pack(fill="both", expand=True)

# Loading label (hidden by default)
loading_label = tk.Label(
    output_section,
    text="",
    font=("Segoe UI", 10),
    bg="#1E1E1E",
    fg="#FFA726"
)

# Configure output text tags
output_box.tag_config("border", foreground="#61AFEF", font=("Consolas", 10))
output_box.tag_config("cmd_header", foreground="#E5C07B", font=("Consolas", 11, "bold"))
output_box.tag_config("timestamp_output", foreground="#56B6C2", font=("Consolas", 9))
output_box.tag_config("output", foreground="#D4D4D4")
output_box.tag_config("separator", foreground="#4B5263")
output_box.tag_config("success_msg", foreground="#98C379", font=("Consolas", 10, "bold"))
output_box.tag_config("error_msg", foreground="#E06C75", font=("Consolas", 10, "bold"))
output_box.tag_config("no_output", foreground="#5C6370", font=("Consolas", 9, "italic"))

# Activity Log Section
log_section = tk.Frame(right_panel, bg="#FFFFFF", height=180, relief="flat", bd=1)
log_section.pack(fill="x")
log_section.pack_propagate(False)

log_header = tk.Frame(log_section, bg="#FAFAFA", height=40)
log_header.pack(fill="x")
log_header.pack_propagate(False)

tk.Label(
    log_header,
    text="ACTIVITY LOG",
    font=("Segoe UI", 10, "bold"),
    bg="#FAFAFA",
    fg="#424242"
).pack(side="left", padx=20, pady=10)

log_text = scrolledtext.ScrolledText(
    log_section,
    font=("Segoe UI", 9),
    bg="#FAFAFA",
    fg="#424242",
    relief="flat",
    wrap="word",
    padx=15,
    pady=10,
    height=8
)
log_text.pack(fill="both", expand=True)

# Configure log text tags
log_text.tag_config("timestamp", foreground="#757575", font=("Segoe UI", 9))
log_text.tag_config("info", foreground="#1976D2")
log_text.tag_config("success", foreground="#388E3C")
log_text.tag_config("error", foreground="#D32F2F")
log_text.tag_config("warning", foreground="#F57C00")

# Initial log message
log_message("Application started", "SUCCESS")
log_message(f"Server initialized on {HOST}:{PORT}", "INFO")

root.mainloop()
