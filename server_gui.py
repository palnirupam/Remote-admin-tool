import socket
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import threading
import time
import json
import base64
import os
import io
from datetime import datetime
from PIL import Image, ImageTk
# Performance optimizations for Linux
import sys
if sys.platform.startswith('linux'):
    # Disable tkinter busy waiting on Linux
    os.environ['TK_SILENCE_DEPRECATION'] = '1'

def debounce_update(widget, delay=50):
    """Debounce UI updates for smoother rendering"""
    if hasattr(widget, '_update_job'):
        widget.after_cancel(widget._update_job)
    widget._update_job = widget.after(delay, lambda: widget.update_idletasks())

HOST = "0.0.0.0"
PORT = 5000

clients = {}  # {client_id: {"conn": conn, "addr": addr, "info": {}}}
active_client_id = None
command_history = []
history_index = -1
server_running = False
server_socket = None

def log_message(message, level="INFO"):
    """Add timestamped log - optimized"""
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
    
    # Use debounced update for smoother UI
    if hasattr(log_text, '_update_job'):
        log_text.after_cancel(log_text._update_job)
    log_text._update_job = log_text.after(50, lambda: log_text.see(tk.END))

def update_status(text, color, icon):
    """Update status bar"""
    status_icon.config(text=icon)
    status_text.config(text=text, foreground=color)

def update_client_list():
    """Update client listbox"""
    client_listbox.delete(0, tk.END)
    for client_id, client_data in clients.items():
        info = client_data.get("info", {})
        hostname = info.get("hostname", "Unknown")
        ip = client_data["addr"][0]
        status = "🟢" if client_id == active_client_id else "⚪"
        client_listbox.insert(tk.END, f"{status} {hostname} ({ip})")

def start_server():
    """Start server and accept multiple clients"""
    global server_running, server_socket
    
    if server_running:
        messagebox.showwarning("Server Running", "Server is already running!")
        return
    
    def server_thread():
        global server_running, server_socket
        try:
            server_socket = socket.socket()
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((HOST, PORT))
            server_socket.listen(5)
            server_socket.settimeout(1.0)  # Non-blocking with timeout
            
            server_running = True
            
            log_message(f"Server started on {HOST}:{PORT}", "SUCCESS")
            update_status("Server listening...", "#66BB6A", "✓")
            
            connect_btn.config(state="disabled", text="✓ Server Running", bg="#43A047")
            stop_server_btn.config(state="normal")
            disconnect_btn.config(state="disabled")
            
            while server_running:
                try:
                    conn, addr = server_socket.accept()
                    
                    # Receive client info
                    try:
                        data = conn.recv(4096).decode()
                        client_info = json.loads(data)
                    except:
                        client_info = {"hostname": "Unknown", "os": "Unknown"}
                    
                    client_id = f"{addr[0]}:{addr[1]}"
                    clients[client_id] = {
                        "conn": conn,
                        "addr": addr,
                        "info": client_info
                    }
                    
                    log_message(f"Client connected: {client_info.get('hostname', 'Unknown')} from {addr[0]}", "SUCCESS")
                    
                    update_client_list()
                    
                    # Auto-select first client
                    if len(clients) == 1:
                        select_client(0)
                
                except socket.timeout:
                    continue  # Keep checking if server should stop
                except Exception as e:
                    if server_running:
                        log_message(f"Accept error: {str(e)}", "ERROR")
        
        except Exception as e:
            log_message(f"Server error: {str(e)}", "ERROR")
            server_running = False
        
        finally:
            if server_socket:
                try:
                    server_socket.close()
                except:
                    pass
            server_running = False
            connect_btn.config(state="normal", text="🚀 Start Server", bg="#1976D2")
            stop_server_btn.config(state="disabled")
            disconnect_btn.config(state="disabled")
    
    threading.Thread(target=server_thread, daemon=True).start()

def stop_server():
    """Stop server and disconnect all clients"""
    global server_running, active_client_id
    
    if not server_running:
        return
    
    if messagebox.askyesno("Stop Server", "Stop server and disconnect all clients?"):
        server_running = False
        
        # Disconnect all clients
        for client_id in list(clients.keys()):
            try:
                clients[client_id]["conn"].close()
            except:
                pass
        
        clients.clear()
        active_client_id = None
        
        update_client_list()
        update_status("Server stopped", "#FF7043", "⚠")
        
        log_message("Server stopped", "WARNING")
        log_message("All clients disconnected", "WARNING")
        
        for btn in command_buttons:
            btn.config(state="disabled")
        connect_btn.config(state="normal", text="🚀 Start Server", bg="#1976D2")
        stop_server_btn.config(state="disabled")
        disconnect_btn.config(state="disabled")
        terminal_output.config(state="disabled")
        
        terminal_output.insert(tk.END, "\n⚠ Server stopped\n\n", "warning")
        terminal_output.see(tk.END)

def select_client(index):
    """Select active client"""
    global active_client_id
    
    if index < 0 or index >= len(clients):
        return
    
    active_client_id = list(clients.keys())[index]
    update_client_list()
    
    client_data = clients[active_client_id]
    info = client_data.get("info", {})
    
    update_status(f"Active: {info.get('hostname', 'Unknown')} ({client_data['addr'][0]})", "#66BB6A", "✓")
    
    # Enable controls
    for btn in command_buttons:
        btn.config(state="normal")
    disconnect_btn.config(state="normal")
    terminal_output.config(state="normal")
    terminal_output.focus()
    
    # Show client info in terminal
    terminal_output.insert(tk.END, f"\n{'='*80}\n", "separator")
    terminal_output.insert(tk.END, f"✓ Selected Client: {info.get('hostname', 'Unknown')}\n", "success")
    terminal_output.insert(tk.END, f"  OS: {info.get('os', 'Unknown')}\n", "output")
    terminal_output.insert(tk.END, f"  IP: {client_data['addr'][0]}\n", "output")
    terminal_output.insert(tk.END, f"  User: {info.get('user', 'Unknown')}\n", "output")
    terminal_output.insert(tk.END, f"{'='*80}\n\n", "separator")
    terminal_output.insert(tk.END, "Remote-Admin> ", "prompt")
    terminal_output.mark_set("input_start", "end-1c")
    terminal_output.see(tk.END)

def on_client_select(event):
    """Handle client selection from listbox"""
    selection = client_listbox.curselection()
    if selection:
        select_client(selection[0])

def send_command_from_button(cmd, cmd_name):
    """Send command from button"""
    if not active_client_id:
        messagebox.showerror("No Client", "Please select a client first!")
        return
    
    # Clear any existing input after prompt
    terminal_output.delete("input_start", "end")
    terminal_output.insert(tk.END, f"{cmd}\n", "command")
    terminal_output.mark_set("input_start", "end-1c")
    terminal_output.see(tk.END)
    execute_command(cmd, cmd_name)

def execute_command(cmd, cmd_name):
    """Execute command on active client"""
    try:
        conn = clients[active_client_id]["conn"]
        
        log_message(f"Executing: {cmd}", "INFO")
        
        conn.send(cmd.encode())
        
        if cmd.lower() == "exit":
            terminal_output.insert(tk.END, "\n✓ Disconnecting client...\n\n", "success")
            terminal_output.see(tk.END)
            disconnect_active_client()
            return
        
        terminal_output.insert(tk.END, "⏳ Executing...\n", "loading")
        terminal_output.see(tk.END)
        # Use update_idletasks instead of update for smoother UI
        root.update_idletasks()
        
        data = conn.recv(2097152)  # 2MB buffer for large screenshots
        output = data.decode(errors="ignore")
        
        # Remove loading
        terminal_output.delete("end-2l", "end-1l")
        
        # Check if JSON response (special commands)
        try:
            response = json.loads(output)
            handle_special_response(response)
        except json.JSONDecodeError as e:
            # Not JSON, display as regular output
            if output.strip():
                terminal_output.insert(tk.END, output + "\n", "output")
        except Exception as e:
            # JSON parsing failed for other reasons
            log_message(f"Screenshot handling error: {str(e)}", "ERROR")
            if output.strip():
                terminal_output.insert(tk.END, output[:500] + "...\n", "output")
            else:
                terminal_output.insert(tk.END, "(No output)\n", "no_output")
        
        terminal_output.insert(tk.END, "\n", "output")
        log_message(f"Completed: {cmd}", "SUCCESS")
        
    except Exception as e:
        terminal_output.insert(tk.END, f"\n❌ ERROR: {str(e)}\n\n", "error")
        log_message(f"Failed: {str(e)}", "ERROR")
    
    terminal_output.insert(tk.END, "Remote-Admin> ", "prompt")
    terminal_output.mark_set("input_start", "end-1c")
    terminal_output.see(tk.END)

def handle_special_response(response):
    """Handle special command responses"""
    resp_type = response.get("type", "")
    
    if resp_type == "SCREENSHOT":
        if response.get("status") == "success":
            show_screenshot(response.get("data"))
        else:
            terminal_output.insert(tk.END, f"❌ Screenshot failed: {response.get('message')}\n", "error")
    
    elif resp_type == "DOWNLOAD":
        if response.get("status") == "success":
            save_downloaded_file(response.get("filename"), response.get("data"))
        else:
            terminal_output.insert(tk.END, f"❌ Download failed: {response.get('message')}\n", "error")
    
    elif resp_type == "UPLOAD":
        if response.get("status") == "success":
            terminal_output.insert(tk.END, f"✓ {response.get('message')}\n", "success")
        else:
            terminal_output.insert(tk.END, f"❌ Upload failed: {response.get('message')}\n", "error")
    
    elif resp_type == "SYSINFO":
        terminal_output.insert(tk.END, json.dumps(response, indent=2) + "\n", "output")

def show_screenshot(img_data_b64):
    """Display screenshot in new window"""
    try:
        img_data = base64.b64decode(img_data_b64)
        image = Image.open(io.BytesIO(img_data))
        
        # Resize for display
        max_size = (1200, 800)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Create window
        screenshot_window = tk.Toplevel(root)
        screenshot_window.title("📸 Client Screenshot")
        screenshot_window.configure(bg="#1E1E1E")
        screenshot_window.geometry("1000x750")
        
        # Store PIL image for saving
        screenshot_window.pil_image = image
        
        # Save function
        def save_img():
            # Detect format from image data
            img_format = "PNG"
            filename_ext = ".png"
            
            # Check if it's JPEG (starts with /9j/ in base64)
            if img_data_b64.startswith('/9j/'):
                img_format = "JPEG"
                filename_ext = ".jpg"
            
            filename = filedialog.asksaveasfilename(
                defaultextension=filename_ext, 
                filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png"), ("All files", "*.*")],
                initialfile=f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}{filename_ext}"
            )
            if filename:
                try:
                    screenshot_window.pil_image.save(filename, img_format)
                    log_message(f"Screenshot saved: {filename} ({img_format})", "SUCCESS")
                    messagebox.showinfo("Success", f"Screenshot saved successfully!\n\nFormat: {img_format}\nFile: {filename}")
                except Exception as e:
                    log_message(f"Error saving screenshot: {e}", "ERROR")
                    messagebox.showerror("Error", f"Failed to save screenshot:\n{str(e)}")
        
        # Header with save button
        header = tk.Frame(screenshot_window, bg="#263238", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Left side - title
        tk.Label(header, text="📸 Client Screenshot", font=("Segoe UI", 14, "bold"), bg="#263238", fg="#FFFFFF").pack(side="left", padx=20, pady=15)
        
        # Right side - save and close buttons
        btn_frame = tk.Frame(header, bg="#263238")
        btn_frame.pack(side="right", padx=20, pady=10)
        
        tk.Button(btn_frame, text="💾 Save", command=save_img, font=("Segoe UI", 11, "bold"), bg="#4CAF50", fg="white", relief="flat", padx=25, pady=8, cursor="hand2").pack(side="left", padx=5)
        tk.Button(btn_frame, text="✗ Close", command=screenshot_window.destroy, font=("Segoe UI", 11), bg="#757575", fg="white", relief="flat", padx=25, pady=8, cursor="hand2").pack(side="left", padx=5)
        
        # Image container
        img_container = tk.Frame(screenshot_window, bg="#1E1E1E")
        img_container.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        
        photo = ImageTk.PhotoImage(image)
        
        label = tk.Label(img_container, image=photo, bg="#1E1E1E")
        label.image = photo
        label.pack()
        
        terminal_output.insert(tk.END, "✓ Screenshot captured and displayed\n", "success")
        log_message("Screenshot captured", "SUCCESS")
        
    except Exception as e:
        terminal_output.insert(tk.END, f"❌ Error displaying screenshot: {str(e)}\n", "error")
        log_message(f"Error displaying screenshot: {e}", "ERROR")

def save_downloaded_file(filename, data_b64):
    """Save downloaded file"""
    try:
        save_path = filedialog.asksaveasfilename(initialfile=filename, defaultextension=".*")
        if save_path:
            file_data = base64.b64decode(data_b64)
            with open(save_path, 'wb') as f:
                f.write(file_data)
            terminal_output.insert(tk.END, f"✓ File downloaded: {save_path}\n", "success")
            log_message(f"File downloaded: {save_path}", "SUCCESS")
    except Exception as e:
        terminal_output.insert(tk.END, f"❌ Save failed: {str(e)}\n", "error")

def capture_screenshot():
    """Request screenshot from client"""
    if not active_client_id:
        messagebox.showerror("No Client", "Please select a client!")
        return
    
    terminal_output.delete("input_start", "end")
    terminal_output.insert(tk.END, "SCREENSHOT\n", "command")
    terminal_output.mark_set("input_start", "end-1c")
    execute_command("SCREENSHOT", "Capture Screenshot")

def download_file_from_client():
    """Download file from client"""
    if not active_client_id:
        messagebox.showerror("No Client", "Please select a client!")
        return
    
    filepath = tk.simpledialog.askstring("Download File", "Enter file path on client:\n(e.g., C:\\Users\\file.txt)")
    if filepath:
        terminal_output.delete("input_start", "end")
        terminal_output.insert(tk.END, f"DOWNLOAD:{filepath}\n", "command")
        terminal_output.mark_set("input_start", "end-1c")
        execute_command(f"DOWNLOAD:{filepath}", f"Download: {filepath}")

def upload_file_to_client():
    """Upload file to client"""
    if not active_client_id:
        messagebox.showerror("No Client", "Please select a client!")
        return
    
    filepath = filedialog.askopenfilename(title="Select file to upload")
    if filepath:
        try:
            with open(filepath, 'rb') as f:
                file_data = base64.b64encode(f.read()).decode()
            
            filename = os.path.basename(filepath)
            cmd = f"UPLOAD:{filename}:{file_data}"
            
            terminal_output.delete("input_start", "end")
            terminal_output.insert(tk.END, f"Uploading {filename}...\n", "command")
            terminal_output.mark_set("input_start", "end-1c")
            execute_command(cmd, f"Upload: {filename}")
            
        except Exception as e:
            messagebox.showerror("Upload Error", str(e))

def clear_terminal():
    """Clear terminal"""
    terminal_output.delete("1.0", tk.END)
    terminal_output.insert(tk.END, "Remote-Admin> ", "prompt")
    terminal_output.mark_set("input_start", "end-1c")
    log_message("Terminal cleared", "INFO")

def disconnect_active_client():
    """Disconnect active client"""
    global active_client_id
    
    if active_client_id and active_client_id in clients:
        try:
            clients[active_client_id]["conn"].close()
        except:
            pass
        
        hostname = clients[active_client_id].get("info", {}).get("hostname", "Unknown")
        del clients[active_client_id]
        
        log_message(f"Client disconnected: {hostname}", "WARNING")
        
        active_client_id = None
        update_client_list()
        
        if clients:
            select_client(0)
        else:
            update_status("No clients connected", "#FF7043", "⚠")
            for btn in command_buttons:
                btn.config(state="disabled")
            terminal_output.config(state="disabled")
        
        terminal_output.insert(tk.END, "\n⚠ Client disconnected\n\n", "warning")
        terminal_output.see(tk.END)

def save_terminal():
    """Save terminal output"""
    content = terminal_output.get("1.0", tk.END)
    if content.strip():
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt"), ("Log", "*.log")])
        if filename:
            with open(filename, "w") as f:
                f.write(content)
            log_message(f"Saved: {filename}", "SUCCESS")

def show_about():
    """About dialog"""
    about = tk.Toplevel(root)
    about.title("About Remote Admin Tool")
    about.geometry("500x450")
    about.configure(bg="#1E1E1E")
    about.resizable(False, False)
    
    tk.Label(about, text="🖥️", font=("Segoe UI", 56), bg="#1E1E1E", fg="#FFFFFF").pack(pady=25)
    tk.Label(about, text="Remote Administration Tool", font=("Segoe UI", 18, "bold"), bg="#1E1E1E", fg="#FFFFFF").pack()
    tk.Label(about, text="Enterprise Edition v2.0", font=("Segoe UI", 11), bg="#1E1E1E", fg="#9E9E9E").pack(pady=8)
    tk.Label(about, text="Professional remote system management", font=("Segoe UI", 10), bg="#1E1E1E", fg="#CCCCCC").pack(pady=15)
    
    features = tk.Text(about, font=("Segoe UI", 10), bg="#2D2D30", fg="#CCCCCC", height=7, relief="flat", borderwidth=0)
    features.pack(pady=15, padx=40, fill="x")
    features.insert("1.0", "✓ Multiple Client Support\n✓ Screenshot Capture\n✓ File Transfer (Upload/Download)\n✓ Interactive Terminal\n✓ System Control\n✓ Process Management\n✓ Real-time Activity Logging")
    features.config(state="disabled")
    
    tk.Label(about, text="© 2026 Nirupam Pal", font=("Segoe UI", 10), bg="#1E1E1E", fg="#757575").pack(pady=15)
    tk.Button(about, text="Close", command=about.destroy, font=("Segoe UI", 11, "bold"), bg="#1976D2", fg="white", relief="flat", padx=40, pady=10, cursor="hand2").pack(pady=15)

def confirm_system_command(cmd, name):
    """Confirm dangerous commands"""
    if messagebox.askyesno("⚠️ Confirm", f"Execute on client:\n\n{name}\n\nThis will affect the client immediately!"):
        send_command_from_button(cmd, name)

def prompt_process_operation(cmd_prefix, operation_name):
    """Prompt for process operations"""
    if not active_client_id:
        messagebox.showerror("No Client", "Please select a client!")
        return
    
    dialog = tk.Toplevel(root)
    dialog.title(operation_name)
    dialog.geometry("500x200")
    dialog.configure(bg="#FFFFFF")
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()
    
    tk.Label(dialog, text=operation_name, font=("Segoe UI", 14, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=20)
    
    input_frame = tk.Frame(dialog, bg="#FFFFFF")
    input_frame.pack(fill="x", padx=40, pady=10)
    
    if "Find" in operation_name:
        tk.Label(input_frame, text="Process Name:", font=("Segoe UI", 11), bg="#FFFFFF", fg="#424242").pack(anchor="w", pady=(0, 5))
        entry = tk.Entry(input_frame, font=("Segoe UI", 11), width=40, relief="solid", borderwidth=1)
        entry.pack(fill="x", pady=5, ipady=5)
        entry.focus()
        
        def execute():
            name = entry.get().strip()
            if name:
                send_command_from_button(f"{cmd_prefix} {name}", f"Find: {name}")
                dialog.destroy()
    
    elif "Kill" in operation_name:
        tk.Label(input_frame, text="Process Name (e.g., notepad.exe):", font=("Segoe UI", 11), bg="#FFFFFF", fg="#424242").pack(anchor="w", pady=(0, 5))
        entry = tk.Entry(input_frame, font=("Segoe UI", 11), width=40, relief="solid", borderwidth=1)
        entry.pack(fill="x", pady=5, ipady=5)
        entry.focus()
        
        def execute():
            name = entry.get().strip()
            if name:
                if messagebox.askyesno("Confirm", f"Kill process: {name}?"):
                    send_command_from_button(f"{cmd_prefix} {name}", f"Kill: {name}")
                    dialog.destroy()
    
    btn_frame = tk.Frame(dialog, bg="#FFFFFF")
    btn_frame.pack(pady=20)
    
    tk.Button(btn_frame, text="✓ Execute", command=execute, font=("Segoe UI", 11, "bold"), bg="#4CAF50", fg="white", relief="flat", padx=30, pady=10, cursor="hand2").pack(side="left", padx=8)
    tk.Button(btn_frame, text="✗ Cancel", command=dialog.destroy, font=("Segoe UI", 11), bg="#757575", fg="white", relief="flat", padx=30, pady=10, cursor="hand2").pack(side="left", padx=8)
    
    entry.bind("<Return>", lambda e: execute())


# Main Window
root = tk.Tk()
root.title("🖥️ Remote Administration Tool - Enterprise Edition v2.0")
root.geometry("1600x950")
root.configure(bg="#F5F5F5")
root.minsize(1400, 800)

# Menu Bar
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="📥 Download from Client", command=download_file_from_client)
file_menu.add_command(label="📤 Upload to Client", command=upload_file_to_client)
file_menu.add_separator()
file_menu.add_command(label="💾 Save Terminal", command=save_terminal)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

edit_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Edit", menu=edit_menu)
edit_menu.add_command(label="Clear Terminal", command=clear_terminal)
edit_menu.add_command(label="Clear Logs", command=lambda: log_text.delete("1.0", tk.END))

tools_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Tools", menu=tools_menu)
tools_menu.add_command(label="📸 Capture Screenshot", command=capture_screenshot)
tools_menu.add_command(label="📊 System Info", command=lambda: send_command_from_button("SYSINFO", "System Info"))

help_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="About", command=show_about)

# Top Bar
top_bar = tk.Frame(root, bg="#0D47A1", height=70)
top_bar.pack(fill="x")
top_bar.pack_propagate(False)

title_frame = tk.Frame(top_bar, bg="#0D47A1")
title_frame.pack(side="left", padx=25, pady=15)

tk.Label(title_frame, text="🖥️", font=("Segoe UI", 28), bg="#0D47A1", fg="#FFFFFF").pack(side="left", padx=(0, 15))

title_text = tk.Frame(title_frame, bg="#0D47A1")
title_text.pack(side="left")

tk.Label(title_text, text="Remote Administration Tool", font=("Segoe UI", 18, "bold"), bg="#0D47A1", fg="#FFFFFF").pack(anchor="w")
tk.Label(title_text, text="Enterprise Edition v2.0 - Multi-Client Support", font=("Segoe UI", 9), bg="#0D47A1", fg="#90CAF9").pack(anchor="w")

# Connection Controls
conn_frame = tk.Frame(top_bar, bg="#0D47A1")
conn_frame.pack(side="right", padx=25)

connect_btn = tk.Button(conn_frame, text="🚀 Start Server", command=start_server, font=("Segoe UI", 11, "bold"), bg="#1976D2", fg="white", relief="flat", padx=25, pady=10, cursor="hand2")
connect_btn.pack(side="left", padx=5)

stop_server_btn = tk.Button(conn_frame, text="⏹ Stop Server", command=stop_server, font=("Segoe UI", 11), bg="#D32F2F", fg="white", relief="flat", padx=25, pady=10, cursor="hand2", state="disabled")
stop_server_btn.pack(side="left", padx=5)

disconnect_btn = tk.Button(conn_frame, text="🔌 Disconnect Client", command=disconnect_active_client, font=("Segoe UI", 11), bg="#FF6F00", fg="white", relief="flat", padx=20, pady=10, cursor="hand2", state="disabled")
disconnect_btn.pack(side="left", padx=5)

# Status Bar
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

tk.Label(status_right, text=f"🌐 Port: {PORT}", font=("Segoe UI", 10), bg="#FFFFFF", fg="#757575").pack(side="left", padx=15)
tk.Label(status_right, text="●", font=("Segoe UI", 14), bg="#FFFFFF", fg="#66BB6A").pack(side="left", padx=5)
tk.Label(status_right, text="Ready", font=("Segoe UI", 10), bg="#FFFFFF", fg="#757575").pack(side="left")

# Main Container
main_container = tk.Frame(root, bg="#F5F5F5")
main_container.pack(fill="both", expand=True)

# Left Panel - Clients & Commands (with scrolling)
left_panel_container = tk.Frame(main_container, bg="#FFFFFF", width=380, relief="flat", bd=1)
left_panel_container.pack(side="left", fill="y", padx=(15, 8), pady=15)
left_panel_container.pack_propagate(False)

# Create canvas and scrollbar for left panel
left_canvas = tk.Canvas(left_panel_container, bg="#FFFFFF", highlightthickness=0)
left_scrollbar = tk.Scrollbar(left_panel_container, orient="vertical", command=left_canvas.yview)
left_panel = tk.Frame(left_canvas, bg="#FFFFFF")

left_scrollbar.pack(side="right", fill="y")
left_canvas.pack(side="left", fill="both", expand=True)
left_canvas.configure(yscrollcommand=left_scrollbar.set)

# Create window in canvas
canvas_frame = left_canvas.create_window((0, 0), window=left_panel, anchor="nw")

# Configure scroll region
def configure_scroll_region(event=None):
    left_canvas.configure(scrollregion=left_canvas.bbox("all"))
    # Update canvas window width to match canvas width
    canvas_width = left_canvas.winfo_width()
    left_canvas.itemconfig(canvas_frame, width=canvas_width)

left_panel.bind("<Configure>", configure_scroll_region)
left_canvas.bind("<Configure>", configure_scroll_region)

# Mouse wheel scrolling - only for left panel area
def on_left_mousewheel(event):
    left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def bind_mousewheel(event):
    left_canvas.bind_all("<MouseWheel>", on_left_mousewheel)

def unbind_mousewheel(event):
    left_canvas.unbind_all("<MouseWheel>")

# Bind mouse wheel only when mouse is over left panel
left_panel_container.bind("<Enter>", bind_mousewheel)
left_panel_container.bind("<Leave>", unbind_mousewheel)

# Client List Section
tk.Label(left_panel, text="👥 CONNECTED CLIENTS", font=("Segoe UI", 11, "bold"), bg="#FFFFFF", fg="#424242").pack(anchor="w", padx=20, pady=(20, 10))

client_list_frame = tk.Frame(left_panel, bg="#F5F5F5", relief="flat")
client_list_frame.pack(fill="x", padx=15, pady=(0, 20))

client_listbox = tk.Listbox(client_list_frame, font=("Segoe UI", 10), bg="#FAFAFA", fg="#212121", height=6, relief="flat", selectbackground="#1976D2", selectforeground="white", borderwidth=0, highlightthickness=1, highlightbackground="#E0E0E0")
client_listbox.pack(fill="x", padx=5, pady=5)
client_listbox.bind("<<ListboxSelect>>", on_client_select)

tk.Label(client_list_frame, text="Click to select active client", font=("Segoe UI", 9), bg="#F5F5F5", fg="#757575").pack(pady=(5, 10))

# Quick Commands
tk.Label(left_panel, text="⚡ QUICK COMMANDS", font=("Segoe UI", 11, "bold"), bg="#FFFFFF", fg="#424242").pack(anchor="w", padx=20, pady=(15, 10))

commands_container = tk.Frame(left_panel, bg="#FFFFFF")
commands_container.pack(fill="x", padx=15)

command_buttons = []

commands = [
    ("Network Info", "NETWORK_INFO", "🌐", "#2196F3"),
    ("Current User", "whoami", "👤", "#9C27B0"),
    ("List Files", "LIST_FILES", "📁", "#FF9800"),
    ("System Info", "SYSTEM_INFO", "💻", "#4CAF50"),
    ("Processes", "PROCESSES", "📊", "#00BCD4"),
    ("Current Path", "cd", "📍", "#E91E63")
]

for text, cmd, icon, color in commands:
    btn = tk.Button(commands_container, text=f"{icon}  {text}", command=lambda c=cmd, t=text: send_command_from_button(c, t), font=("Segoe UI", 11, "bold"), bg=color, fg="white", relief="flat", padx=18, pady=12, cursor="hand2", state="disabled", anchor="w", activebackground=color, activeforeground="white")
    btn.pack(fill="x", pady=4)
    command_buttons.append(btn)

# Advanced Features
adv_frame = tk.Frame(left_panel, bg="#E8EAF6", relief="flat")
adv_frame.pack(fill="x", padx=15, pady=(15, 10))

tk.Label(adv_frame, text="🚀 ADVANCED", font=("Segoe UI", 10, "bold"), bg="#E8EAF6", fg="#283593").pack(anchor="w", padx=12, pady=(12, 10))

adv_btns = [
    ("📸 Screenshot", capture_screenshot, "#5E35B1"),
    ("📥 Download File", download_file_from_client, "#00897B"),
    ("📤 Upload File", upload_file_to_client, "#6A1B9A")
]

for text, cmd, color in adv_btns:
    btn = tk.Button(adv_frame, text=text, command=cmd, font=("Segoe UI", 11, "bold"), bg=color, fg="white", relief="flat", padx=18, pady=12, cursor="hand2", state="disabled", anchor="w", activebackground=color, activeforeground="white")
    btn.pack(fill="x", padx=10, pady=4)
    command_buttons.append(btn)

tk.Label(adv_frame, text="", bg="#E8EAF6").pack(pady=5)  # Bottom padding

# System Control
sys_frame = tk.Frame(left_panel, bg="#FFEBEE", relief="flat")
sys_frame.pack(fill="x", padx=15, pady=(15, 10))

tk.Label(sys_frame, text="⚙️ SYSTEM CONTROL", font=("Segoe UI", 10, "bold"), bg="#FFEBEE", fg="#C62828").pack(anchor="w", padx=12, pady=(12, 10))

sys_btns = [
    ("🔄 Restart System", "RESTART", "#FF5722"),
    ("⏻ Shutdown System", "SHUTDOWN", "#D32F2F"),
    ("🔒 Lock Workstation", "LOCK", "#F57C00")
]

for text, cmd, color in sys_btns:
    btn = tk.Button(sys_frame, text=text, command=lambda c=cmd, t=text: confirm_system_command(c, t), font=("Segoe UI", 10, "bold"), bg=color, fg="white", relief="flat", padx=18, pady=11, cursor="hand2", state="disabled", anchor="w", activebackground=color, activeforeground="white")
    btn.pack(fill="x", padx=10, pady=4)
    command_buttons.append(btn)

tk.Label(sys_frame, text="", bg="#FFEBEE").pack(pady=5)  # Bottom padding

# Process Control
proc_frame = tk.Frame(left_panel, bg="#E1F5FE", relief="flat")
proc_frame.pack(fill="x", padx=15, pady=(15, 20))

tk.Label(proc_frame, text="🎯 PROCESS CONTROL", font=("Segoe UI", 10, "bold"), bg="#E1F5FE", fg="#01579B").pack(anchor="w", padx=12, pady=(12, 10))

proc_btns = [
    ("🔍 Find Process", "FIND_PROCESS:", "#0288D1"),
    ("❌ Kill Process", "KILL_PROCESS:", "#D32F2F")
]

for text, cmd_prefix, color in proc_btns:
    btn = tk.Button(proc_frame, text=text, command=lambda cp=cmd_prefix, t=text: prompt_process_operation(cp, t), font=("Segoe UI", 10, "bold"), bg=color, fg="white", relief="flat", padx=18, pady=11, cursor="hand2", state="disabled", anchor="w", activebackground=color, activeforeground="white")
    btn.pack(fill="x", padx=10, pady=4)
    command_buttons.append(btn)

tk.Label(proc_frame, text="", bg="#E1F5FE").pack(pady=5)  # Bottom padding


# Right Panel - Terminal
right_panel = tk.Frame(main_container, bg="#F5F5F5")
right_panel.pack(side="right", fill="both", expand=True, padx=(8, 15), pady=15)

# Configure grid weights
right_panel.grid_rowconfigure(0, weight=3)  # Terminal gets 75% space
right_panel.grid_rowconfigure(1, weight=1)  # Log gets 25% space
right_panel.grid_columnconfigure(0, weight=1)

# Terminal Section
terminal_section = tk.Frame(right_panel, bg="#FFFFFF", relief="solid", bd=2)
terminal_section.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

terminal_header = tk.Frame(terminal_section, bg="#263238", height=55)
terminal_header.pack(fill="x")
terminal_header.pack_propagate(False)

tk.Label(terminal_header, text="💻 INTERACTIVE TERMINAL", font=("Segoe UI", 12, "bold"), bg="#263238", fg="#FFFFFF").pack(side="left", padx=20, pady=15)
tk.Label(terminal_header, text="Type commands | ↑↓ history | Enter to execute", font=("Segoe UI", 10), bg="#263238", fg="#90A4AE").pack(side="left", padx=10)

tk.Button(terminal_header, text="💾", command=save_terminal, font=("Segoe UI", 12), bg="#263238", fg="#90CAF9", relief="flat", padx=12, cursor="hand2", borderwidth=0).pack(side="right", padx=8)
tk.Button(terminal_header, text="🗑️", command=clear_terminal, font=("Segoe UI", 12), bg="#263238", fg="#90CAF9", relief="flat", padx=12, cursor="hand2", borderwidth=0).pack(side="right", padx=8)

# Terminal Output (editable like real terminal)
terminal_output = scrolledtext.ScrolledText(terminal_section, font=("Consolas", 11), bg="#0D1117", fg="#C9D1D9", insertbackground="#58A6FF", relief="flat", wrap="word", padx=25, pady=20, state="normal")
terminal_output.pack(fill="both", expand=True)

# Terminal tags
terminal_output.tag_config("prompt", foreground="#58A6FF", font=("Consolas", 12, "bold"))
terminal_output.tag_config("command", foreground="#79C0FF", font=("Consolas", 12, "bold"))
terminal_output.tag_config("output", foreground="#C9D1D9", font=("Consolas", 11))
terminal_output.tag_config("success", foreground="#3FB950", font=("Consolas", 12, "bold"))
terminal_output.tag_config("error", foreground="#F85149", font=("Consolas", 12, "bold"))
terminal_output.tag_config("warning", foreground="#D29922", font=("Consolas", 12))
terminal_output.tag_config("separator", foreground="#30363D", font=("Consolas", 11))
terminal_output.tag_config("loading", foreground="#FFA657", font=("Consolas", 11, "italic"))
terminal_output.tag_config("no_output", foreground="#6E7681", font=("Consolas", 11, "italic"))
terminal_output.tag_config("readonly", foreground="#C9D1D9", font=("Consolas", 11))

# Welcome
terminal_output.insert(tk.END, "╔" + "═"*78 + "╗\n", "separator")
terminal_output.insert(tk.END, "  REMOTE ADMINISTRATION TOOL - Enterprise Edition v2.0\n", "success")
terminal_output.insert(tk.END, "  Features: Multi-Client | Screenshot | File Transfer | Full Control\n", "output")
terminal_output.insert(tk.END, "╚" + "═"*78 + "╝\n\n", "separator")
terminal_output.insert(tk.END, "Click 'Start Server' to begin accepting client connections.\n", "output")
terminal_output.insert(tk.END, "All OS commands supported: mkdir, ls/dir, cd, cat/type, cp/copy, rm/del, etc.\n\n", "output")
terminal_output.insert(tk.END, "Remote-Admin> ", "prompt")

# Mark all existing content as readonly
terminal_output.mark_set("input_start", "end-1c")
terminal_output.mark_gravity("input_start", "left")

# Bind keys to terminal output for direct typing
def on_terminal_key(event):
    """Handle key press in terminal"""
    if not active_client_id:
        return "break"
    
    # Allow typing only after the prompt
    if terminal_output.index("insert") < terminal_output.index("input_start"):
        terminal_output.mark_set("insert", "end")
        return "break"
    
    if event.keysym == "Return":
        # Get command from current line
        cmd = terminal_output.get("input_start", "end-1c").strip()
        
        if cmd:
            command_history.append(cmd)
            global history_index
            history_index = len(command_history)
            
            terminal_output.insert(tk.END, "\n")
            execute_command(cmd, cmd)
        else:
            terminal_output.insert(tk.END, "\n")
            terminal_output.insert(tk.END, "Remote-Admin> ", "prompt")
            terminal_output.mark_set("input_start", "end-1c")
        
        terminal_output.see(tk.END)
        return "break"
    
    elif event.keysym == "Up":
        # Navigate history up
        if command_history and history_index > 0:
            history_index -= 1
            terminal_output.delete("input_start", "end")
            terminal_output.insert("end", command_history[history_index])
        return "break"
    
    elif event.keysym == "Down":
        # Navigate history down
        if command_history:
            if history_index < len(command_history) - 1:
                history_index += 1
                terminal_output.delete("input_start", "end")
                terminal_output.insert("end", command_history[history_index])
            else:
                history_index = len(command_history)
                terminal_output.delete("input_start", "end")
        return "break"
    
    elif event.keysym == "BackSpace":
        # Prevent deleting prompt
        if terminal_output.index("insert") <= terminal_output.index("input_start"):
            return "break"

terminal_output.bind("<Key>", on_terminal_key)
terminal_output.bind("<Button-1>", lambda e: terminal_output.mark_set("insert", "end"))
terminal_output.focus()

# Activity Log
log_section = tk.Frame(right_panel, bg="#263238", relief="solid", bd=2)
log_section.grid(row=1, column=0, sticky="nsew")

log_header = tk.Frame(log_section, bg="#37474F", height=50)
log_header.pack(fill="x")
log_header.pack_propagate(False)

tk.Label(log_header, text="📋 ACTIVITY LOG", font=("Segoe UI", 13, "bold"), bg="#37474F", fg="#FFFFFF").pack(side="left", padx=25, pady=14)
tk.Label(log_header, text="Real-time event monitoring", font=("Segoe UI", 9), bg="#37474F", fg="#B0BEC5").pack(side="left", padx=10)

tk.Button(log_header, text="🗑️ Clear", command=lambda: log_text.delete("1.0", tk.END), font=("Segoe UI", 10), bg="#37474F", fg="#90CAF9", relief="flat", padx=15, cursor="hand2", borderwidth=0).pack(side="right", padx=15)

log_text = scrolledtext.ScrolledText(log_section, font=("Segoe UI", 11), bg="#FAFAFA", fg="#424242", relief="flat", wrap="word", padx=25, pady=18, height=6, borderwidth=0)
log_text.pack(fill="both", expand=True, padx=2, pady=2)

log_text.tag_config("timestamp", foreground="#78909C", font=("Segoe UI", 10, "bold"))
log_text.tag_config("info", foreground="#1976D2", font=("Segoe UI", 11, "bold"))
log_text.tag_config("success", foreground="#388E3C", font=("Segoe UI", 11, "bold"))
log_text.tag_config("error", foreground="#D32F2F", font=("Segoe UI", 11, "bold"))
log_text.tag_config("warning", foreground="#F57C00", font=("Segoe UI", 11, "bold"))

log_message("🚀 Application started", "SUCCESS")
log_message(f"🌐 Server ready on {HOST}:{PORT}", "INFO")
log_message("⏳ Waiting for connections...", "INFO")

root.mainloop()
