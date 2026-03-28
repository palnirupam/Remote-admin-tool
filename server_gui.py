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
clients_lock = threading.Lock()  # Thread-safe access to clients dict
stop_monitoring = False  # Flag to stop monitoring thread

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
    """Update client listbox - thread-safe with error handling"""
    try:
        # Must be called from main thread
        if threading.current_thread() != threading.main_thread():
            root.after(0, update_client_list)
            return
        
        client_listbox.delete(0, tk.END)
        
        with clients_lock:
            if not clients:
                return
            clients_copy = list(clients.items())  # Create list copy inside lock
        
        # Update UI outside lock
        for client_id, client_data in clients_copy:
            try:
                info = client_data.get("info", {})
                hostname = info.get("hostname", "Unknown")
                ip = client_data["addr"][0]
                status = "🟢" if client_id == active_client_id else "⚪"
                client_listbox.insert(tk.END, f"{status} {hostname} ({ip})")
            except Exception as e:
                log_message(f"Error updating client list item: {e}", "ERROR")
                continue
    except Exception as e:
        log_message(f"Error in update_client_list: {e}", "ERROR")

def start_server():
    """Start server and accept multiple clients - advanced error handling"""
    global server_running, server_socket, stop_monitoring
    
    if server_running:
        messagebox.showwarning("Server Running", "Server is already running!")
        return
    
    def server_thread():
        global server_running, server_socket, stop_monitoring
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            try:
                server_socket.bind((HOST, PORT))
            except OSError as e:
                root.after(0, lambda: log_message(f"Bind error: {e}. Port {PORT} may be in use", "ERROR"))
                root.after(0, lambda: messagebox.showerror("Server Error", f"Cannot bind to port {PORT}.\nPort may be in use."))
                return
            
            server_socket.listen(5)
            server_socket.settimeout(1.0)  # Non-blocking with timeout
            
            server_running = True
            stop_monitoring = False
            
            root.after(0, lambda: log_message(f"Server started on {HOST}:{PORT}", "SUCCESS"))
            root.after(0, lambda: update_status("Server listening...", "#66BB6A", "✓"))
            
            root.after(0, lambda: connect_btn.config(state="disabled", text="✓ Server Running", bg="#43A047"))
            root.after(0, lambda: stop_server_btn.config(state="normal"))
            root.after(0, lambda: disconnect_btn.config(state="disabled"))
            
            while server_running:
                try:
                    conn, addr = server_socket.accept()
                    
                    # Receive client info with timeout
                    conn.settimeout(5.0)
                    try:
                        data = conn.recv(4096).decode('utf-8', errors='ignore')
                        if data:
                            client_info = json.loads(data)
                        else:
                            client_info = {"hostname": "Unknown", "os": "Unknown", "user": "Unknown"}
                    except socket.timeout:
                        root.after(0, lambda: log_message("Client info timeout", "WARNING"))
                        client_info = {"hostname": "Unknown", "os": "Unknown", "user": "Unknown"}
                    except json.JSONDecodeError:
                        root.after(0, lambda: log_message("Invalid client info JSON", "WARNING"))
                        client_info = {"hostname": "Unknown", "os": "Unknown", "user": "Unknown"}
                    except Exception as e:
                        root.after(0, lambda e=e: log_message(f"Client info error: {e}", "WARNING"))
                        client_info = {"hostname": "Unknown", "os": "Unknown", "user": "Unknown"}
                    
                    # Reset socket timeout
                    conn.settimeout(None)
                    
                    client_id = f"{addr[0]}:{addr[1]}"
                    
                    with clients_lock:
                        clients[client_id] = {
                            "conn": conn,
                            "addr": addr,
                            "info": client_info
                        }
                        total = len(clients)
                    
                    hostname = client_info.get('hostname', 'Unknown')
                    root.after(0, lambda h=hostname, ip=addr[0]: log_message(f"Client connected: {h} from {ip}", "SUCCESS"))
                    
                    # Update UI in main thread with delay
                    root.after(100, update_client_list)
                    
                    # Auto-select first client in main thread
                    if total == 1:
                        root.after(200, lambda: select_client(0))
                
                except socket.timeout:
                    continue  # Keep checking if server should stop
                except Exception as e:
                    if server_running:
                        root.after(0, lambda e=e: log_message(f"Accept error: {str(e)}", "ERROR"))
        
        except Exception as e:
            root.after(0, lambda e=e: log_message(f"Server error: {str(e)}", "ERROR"))
            root.after(0, lambda e=e: messagebox.showerror("Server Error", f"Server failed:\n{str(e)}"))
            server_running = False
        
        finally:
            if server_socket:
                try:
                    server_socket.close()
                except:
                    pass
            server_running = False
            root.after(0, lambda: connect_btn.config(state="normal", text="🚀 Start Server", bg="#1976D2"))
            root.after(0, lambda: stop_server_btn.config(state="disabled"))
            root.after(0, lambda: disconnect_btn.config(state="disabled"))
    
    # Start server thread
    server_t = threading.Thread(target=server_thread, daemon=True, name="ServerThread")
    server_t.start()
    
    # Start connection monitoring with delay
    time.sleep(0.5)
    monitor_t = threading.Thread(target=check_client_connections, daemon=True, name="MonitorThread")
    monitor_t.start()

def stop_server():
    """Stop server and disconnect all clients - thread-safe"""
    global server_running, active_client_id, stop_monitoring
    
    try:
        if not server_running:
            log_message("Server is not running", "WARNING")
            return
        
        if not messagebox.askyesno("Stop Server", "Stop server and disconnect all clients?"):
            return
        
        server_running = False
        stop_monitoring = True
        
        # Disconnect all clients safely
        with clients_lock:
            client_count = len(clients)
            for client_id in list(clients.keys()):
                try:
                    clients[client_id]["conn"].close()
                except Exception as e:
                    log_message(f"Error closing client {client_id}: {e}", "WARNING")
            
            clients.clear()
            active_client_id = None
        
        # Update UI
        update_client_list()
        update_status("Server stopped", "#FF7043", "⚠")
        
        log_message("Server stopped", "WARNING")
        log_message(f"All {client_count} clients disconnected", "WARNING")
        
        for btn in command_buttons:
            btn.config(state="disabled")
        for btn in advanced_buttons:
            btn.config(state="disabled")
        connect_btn.config(state="normal", text="🚀 Start Server", bg="#1976D2")
        stop_server_btn.config(state="disabled")
        disconnect_btn.config(state="disabled")
        terminal_output.config(state="disabled")
        
        terminal_output.insert(tk.END, "\n⚠ Server stopped\n\n", "warning")
        terminal_output.see(tk.END)
        
    except Exception as e:
        log_message(f"Error in stop_server: {e}", "ERROR")
        messagebox.showerror("Stop Server Error", f"Failed to stop server:\n{str(e)}")

def select_client(index):
    """Select active client - thread-safe with validation"""
    global active_client_id
    
    try:
        # Must be called from main thread
        if threading.current_thread() != threading.main_thread():
            root.after(0, lambda: select_client(index))
            return
        
        with clients_lock:
            if index < 0 or index >= len(clients):
                log_message(f"Invalid client index: {index}", "WARNING")
                return
            
            client_id = list(clients.keys())[index]
            if client_id not in clients:
                log_message(f"Client {client_id} not found", "WARNING")
                return
            
            active_client_id = client_id
            client_data = clients[active_client_id]
            info = client_data.get("info", {})
            addr = client_data['addr']
            client_os = info.get("os", "Unknown")
        
        # Update UI outside lock
        update_client_list()
        update_status(f"Active: {info.get('hostname', 'Unknown')} ({addr[0]})", "#66BB6A", "✓")
        
        # Update commands based on client OS
        update_commands_for_client_os(client_os)
        
        # Enable controls
        for btn in command_buttons:
            btn.config(state="normal")
        for btn in advanced_buttons:
            btn.config(state="normal")
        disconnect_btn.config(state="normal")
        terminal_output.config(state="normal")
        terminal_output.focus()
        
        # Show client info in terminal
        terminal_output.insert(tk.END, f"\n{'='*80}\n", "separator")
        terminal_output.insert(tk.END, f"✓ Selected Client: {info.get('hostname', 'Unknown')}\n", "success")
        terminal_output.insert(tk.END, f"  OS: {client_os}\n", "output")
        terminal_output.insert(tk.END, f"  IP: {addr[0]}\n", "output")
        terminal_output.insert(tk.END, f"  User: {info.get('user', 'Unknown')}\n", "output")
        terminal_output.insert(tk.END, f"{'='*80}\n\n", "separator")
        terminal_output.insert(tk.END, "Remote-Admin> ", "prompt")
        terminal_output.mark_set("input_start", "end-1c")
        terminal_output.see(tk.END)
        
        log_message(f"Selected client: {info.get('hostname', 'Unknown')} ({client_os})", "INFO")
        
    except Exception as e:
        log_message(f"Error selecting client: {e}", "ERROR")
        messagebox.showerror("Error", f"Failed to select client:\n{str(e)}")

def on_client_select(event):
    """Handle client selection from listbox"""
    selection = client_listbox.curselection()
    if selection:
        select_client(selection[0])

def send_command_from_button(cmd, cmd_name):
    """Send command from button - thread-safe with validation"""
    try:
        # Validate active client with lock
        with clients_lock:
            if not active_client_id or active_client_id not in clients:
                messagebox.showerror("No Client", "Please select a client first!")
                return
        
        # Validate terminal state
        if terminal_output.cget("state") == "disabled":
            log_message("Terminal is disabled", "WARNING")
            return
        
        # Clear any existing input after prompt
        try:
            terminal_output.delete("input_start", "end")
            terminal_output.insert(tk.END, f"{cmd}\n", "command")
            terminal_output.mark_set("input_start", "end-1c")
            terminal_output.see(tk.END)
        except tk.TclError as e:
            log_message(f"Terminal update error: {e}", "ERROR")
            return
        
        execute_command(cmd, cmd_name)
        
    except Exception as e:
        log_message(f"Error in send_command_from_button: {e}", "ERROR")
        messagebox.showerror("Command Error", f"Failed to send command:\n{str(e)}")

def execute_command(cmd, cmd_name):
    """Execute command on active client - real terminal experience with streaming"""
    conn = None
    client_hostname = "Unknown"
    
    try:
        # Thread-safe client validation
        with clients_lock:
            if not active_client_id or active_client_id not in clients:
                root.after(0, lambda: terminal_output.insert(tk.END, "\n❌ ERROR: No active client\n\n", "error"))
                root.after(0, lambda: terminal_output.insert(tk.END, "Remote-Admin> ", "prompt"))
                root.after(0, lambda: terminal_output.mark_set("input_start", "end-1c"))
                return
            
            try:
                conn = clients[active_client_id]["conn"]
                client_hostname = clients[active_client_id].get("info", {}).get("hostname", "Unknown")
            except (KeyError, TypeError) as e:
                root.after(0, lambda: terminal_output.insert(tk.END, f"\n❌ ERROR: {e}\n\n", "error"))
                root.after(0, lambda: terminal_output.insert(tk.END, "Remote-Admin> ", "prompt"))
                root.after(0, lambda: terminal_output.mark_set("input_start", "end-1c"))
                return
        
        # Set socket for non-blocking streaming
        conn.settimeout(0.1)  # Very short timeout for streaming
        
        log_message(f"Executing: {cmd}", "INFO")
        
        # Send command
        conn.send(cmd.encode())
        
        if cmd.lower() == "exit":
            root.after(0, lambda: terminal_output.insert(tk.END, "\n✓ Disconnecting...\n\n", "success"))
            root.after(0, disconnect_active_client)
            return
        
        # Real-time streaming output
        all_data = b""
        chunk_count = 0
        max_chunks = 200  # Increased for large screenshots
        start_time = time.time()
        last_update = time.time()
        
        # Check if special command (JSON response expected)
        is_special_cmd = cmd.upper().startswith(("SCREENSHOT", "DOWNLOAD:", "UPLOAD:", "SYSINFO"))
        
        # For screenshots, expect larger data
        if cmd.upper() == "SCREENSHOT":
            max_timeout = 15.0  # 15 seconds for screenshot
            max_chunks = 500  # More chunks for large images
        else:
            max_timeout = 5.0
        
        while chunk_count < max_chunks:
            try:
                # Timeout check
                if time.time() - start_time > max_timeout:
                    break
                
                chunk = conn.recv(8192)  # Larger chunks for faster transfer
                if not chunk:
                    break
                
                all_data += chunk
                chunk_count += 1
                
                # Real-time streaming display (not for special commands)
                if not is_special_cmd and chunk:
                    try:
                        decoded_chunk = chunk.decode(errors="ignore")
                        # Update terminal in real-time
                        root.after(0, lambda text=decoded_chunk: terminal_output.insert(tk.END, text, "output"))
                        root.after(0, lambda: terminal_output.see(tk.END))
                    except:
                        pass
                
                # Update UI every 100ms for smooth display
                if time.time() - last_update > 0.1:
                    root.after(0, lambda: root.update_idletasks())
                    last_update = time.time()
                
                # Check for complete response
                if b'}' in chunk:
                    # For JSON, wait a bit more to ensure all data received
                    time.sleep(0.1)
                    try:
                        final_chunk = conn.recv(8192)
                        if final_chunk:
                            all_data += final_chunk
                    except:
                        pass
                    break
                elif not is_special_cmd and len(all_data) > 100 and b'\n' in chunk:
                    # For regular commands, check if complete
                    time.sleep(0.05)
                    try:
                        final_chunk = conn.recv(4096)
                        if final_chunk:
                            all_data += final_chunk
                        else:
                            break
                    except:
                        break
                    
            except socket.timeout:
                # No more data available
                if chunk_count > 0:
                    break
                continue
            except Exception as e:
                log_message(f"Receive error: {e}", "ERROR")
                break
        
        output = all_data.decode(errors="ignore")
        
        # Handle special JSON commands
        if is_special_cmd:
            is_json_handled = False
            try:
                json_start = output.find('{')
                json_end = output.rfind('}')
                
                if json_start != -1 and json_end != -1:
                    json_str = output[json_start:json_end+1]
                    
                    try:
                        response = json.loads(json_str)
                        resp_type = response.get("type", "")
                        
                        if resp_type == "SCREENSHOT":
                            if response.get("status") == "success":
                                root.after(0, lambda: show_screenshot(response.get("data")))
                                root.after(0, lambda: terminal_output.insert(tk.END, "✓ Screenshot captured\n", "success"))
                            else:
                                root.after(0, lambda msg=response.get('message'): terminal_output.insert(tk.END, f"❌ {msg}\n", "error"))
                            is_json_handled = True
                            
                        elif resp_type == "DOWNLOAD":
                            if response.get("status") == "success":
                                root.after(0, lambda: save_downloaded_file(response.get("filename"), response.get("data")))
                            else:
                                root.after(0, lambda msg=response.get('message'): terminal_output.insert(tk.END, f"❌ {msg}\n", "error"))
                            is_json_handled = True
                            
                        elif resp_type == "SYSINFO":
                            formatted = json.dumps(response, indent=2)
                            root.after(0, lambda text=formatted: terminal_output.insert(tk.END, text + "\n", "output"))
                            is_json_handled = True
                            
                        elif resp_type == "UPLOAD":
                            if response.get("status") == "success":
                                root.after(0, lambda msg=response.get('message'): terminal_output.insert(tk.END, f"✓ {msg}\n", "success"))
                            else:
                                root.after(0, lambda msg=response.get('message'): terminal_output.insert(tk.END, f"❌ {msg}\n", "error"))
                            is_json_handled = True
                            
                    except json.JSONDecodeError:
                        pass
                        
            except Exception as e:
                log_message(f"JSON error: {e}", "ERROR")
            
            # If not handled as JSON, display as text
            if not is_json_handled and output.strip():
                root.after(0, lambda text=output: terminal_output.insert(tk.END, text + "\n", "output"))
        
        # Add newline and prompt
        root.after(0, lambda: terminal_output.insert(tk.END, "\n", "output"))
        root.after(0, lambda: terminal_output.insert(tk.END, "Remote-Admin> ", "prompt"))
        root.after(0, lambda: terminal_output.mark_set("input_start", "end-1c"))
        root.after(0, lambda: terminal_output.see(tk.END))
        
        log_message(f"Completed: {cmd}", "SUCCESS")
        
    except socket.error as e:
        terminal_output.insert(tk.END, f"\n❌ SOCKET ERROR: {str(e)}\n", "error")
        terminal_output.insert(tk.END, "⚠️  Client may have disconnected\n\n", "warning")
        log_message(f"Socket error on {client_hostname}: {str(e)}", "ERROR")
        
        # Auto-disconnect on socket error
        root.after(100, disconnect_active_client)
        
    except KeyError as e:
        terminal_output.insert(tk.END, f"\n❌ CLIENT ERROR: Client disconnected during execution\n\n", "error")
        log_message(f"Client key error: {e}", "ERROR")
        
    except Exception as e:
        terminal_output.insert(tk.END, f"\n❌ ERROR: {str(e)}\n\n", "error")
        log_message(f"Command execution failed on {client_hostname}: {str(e)}", "ERROR")
    
    finally:
        # Always restore prompt
        try:
            terminal_output.insert(tk.END, "Remote-Admin> ", "prompt")
            terminal_output.mark_set("input_start", "end-1c")
            terminal_output.see(tk.END)
        except tk.TclError:
            pass  # Terminal may be destroyed

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

def show_original_size(image):
    """Display screenshot at 100% original size for perfect text clarity"""
    try:
        # Create new window for original size view
        original_window = tk.Toplevel(root)
        original_window.title("📸 Original Size (100% - Perfect Text)")
        original_window.configure(bg="#1E1E1E")
        
        # Get original image dimensions
        img_width, img_height = image.size
        
        # Set window size to match image (with small padding)
        window_width = img_width + 40
        window_height = img_height + 100  # Extra space for header
        
        # Ensure window fits on screen
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        if window_width > screen_width:
            window_width = screen_width - 50
        if window_height > screen_height:
            window_height = screen_height - 50
        
        original_window.geometry(f"{window_width}x{window_height}")
        
        # Header
        header = tk.Frame(original_window, bg="#263238", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="📸 Original Size - Perfect Text Clarity", font=("Segoe UI", 12, "bold"), bg="#263238", fg="#FFFFFF").pack(side="left", padx=20, pady=15)
        tk.Label(header, text=f"Resolution: {img_width}x{img_height}", font=("Segoe UI", 10), bg="#263238", fg="#90CAF9").pack(side="left", padx=10, pady=15)
        
        tk.Button(header, text="✗ Close", command=original_window.destroy, font=("Segoe UI", 11), bg="#757575", fg="white", relief="flat", padx=25, pady=8, cursor="hand2").pack(side="right", padx=20, pady=10)
        
        # Scrollable frame for large images
        canvas = tk.Canvas(original_window, bg="#1E1E1E")
        scrollbar_v = tk.Scrollbar(original_window, orient="vertical", command=canvas.yview)
        scrollbar_h = tk.Scrollbar(original_window, orient="horizontal", command=canvas.xview)
        scrollable_frame = tk.Frame(canvas, bg="#1E1E1E")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        # Display image at original size
        photo = ImageTk.PhotoImage(image)
        label = tk.Label(scrollable_frame, image=photo, bg="#1E1E1E")
        label.image = photo  # Keep a reference
        label.pack(padx=20, pady=20)
        
        # Pack scrollable widgets
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(0, 20))
        scrollbar_v.pack(side="right", fill="y", pady=(0, 20))
        scrollbar_h.pack(side="bottom", fill="x", padx=(20, 0))
        
        log_message(f"Opened original size view: {img_width}x{img_height}", "INFO")
        
    except Exception as e:
        log_message(f"Error showing original size: {e}", "ERROR")
        messagebox.showerror("Error", f"Failed to show original size:\n{str(e)}")

def show_screenshot(img_data_b64):
    """Display screenshot in new window - 4K quality support for Linux & Windows"""
    try:
        img_data = base64.b64decode(img_data_b64)
        original_image = Image.open(io.BytesIO(img_data))
        
        # Get screen resolution for adaptive display
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Detect if 4K/high-res display
        is_4k = screen_width >= 3840 or screen_height >= 2160
        is_2k = screen_width >= 2560 or screen_height >= 1440
        
        # Create a copy for display (keep original for saving)
        display_image = original_image.copy()
        
        # Adaptive max size based on screen resolution
        if is_4k:
            max_size = (3200, 2400)  # 4K display - show near-original quality
            window_size = "3200x2000"
        elif is_2k:
            max_size = (2400, 1800)  # 2K display - high quality
            window_size = "2400x1600"
        else:
            max_size = (1920, 1440)  # Full HD - good quality
            window_size = "1920x1200"
        
        # Get original dimensions
        orig_width, orig_height = original_image.size
        
        # Only resize if image is larger than max_size
        if orig_width > max_size[0] or orig_height > max_size[1]:
            # Use LANCZOS (highest quality) resampling
            display_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Apply subtle sharpening for text clarity (less aggressive for 4K)
            from PIL import ImageFilter, ImageEnhance
            if is_4k:
                # Minimal sharpening for 4K - already sharp
                display_image = display_image.filter(ImageFilter.UnsharpMask(radius=0.5, percent=120, threshold=3))
            else:
                # More sharpening for lower res displays
                display_image = display_image.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=2))
            
            # Enhance contrast slightly for better visibility
            enhancer = ImageEnhance.Contrast(display_image)
            display_image = enhancer.enhance(1.05)
        
        # Create window
        screenshot_window = tk.Toplevel(root)
        screenshot_window.title(f"📸 Client Screenshot - {orig_width}x{orig_height}")
        screenshot_window.configure(bg="#1E1E1E")
        screenshot_window.geometry(window_size)
        
        # Maximize on 4K displays
        if is_4k:
            try:
                screenshot_window.state('zoomed')  # Windows
            except:
                try:
                    screenshot_window.attributes('-zoomed', True)  # Linux
                except:
                    pass
        
        # Store ORIGINAL PIL image for saving (not the resized one)
        screenshot_window.pil_image = original_image
        
        # Save function with 4K quality preservation
        def save_img():
            # Detect format from image data
            img_format = "PNG"
            filename_ext = ".png"
            
            # Check if it's JPEG (starts with /9j/ in base64)
            if img_data_b64.startswith('/9j/'):
                img_format = "JPEG"
                filename_ext = ".jpg"
            
            # Add option for original format
            filetypes = [
                ("PNG - Lossless Quality", "*.png"),
                ("JPEG - High Quality", "*.jpg"), 
                ("All files", "*.*")
            ]
            
            filename = filedialog.asksaveasfilename(
                defaultextension=filename_ext, 
                filetypes=filetypes,
                initialfile=f"screenshot_4K_{datetime.now().strftime('%Y%m%d_%H%M%S')}{filename_ext}"
            )
            if filename:
                try:
                    # Save with maximum quality - 4K preserved
                    if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                        # JPEG with 99% quality (near lossless)
                        screenshot_window.pil_image.save(filename, "JPEG", quality=99, optimize=True, progressive=True, subsampling=0)
                    else:
                        # PNG with minimal compression (maximum quality)
                        screenshot_window.pil_image.save(filename, "PNG", optimize=False, compress_level=1)
                    
                    file_size = os.path.getsize(filename) / (1024 * 1024)  # MB
                    log_message(f"Screenshot saved: {filename} ({orig_width}x{orig_height}, {file_size:.2f}MB)", "SUCCESS")
                    messagebox.showinfo("Success", f"Screenshot saved successfully!\n\nResolution: {orig_width}x{orig_height}\nSize: {file_size:.2f}MB\nFile: {os.path.basename(filename)}")
                except Exception as e:
                    log_message(f"Error saving screenshot: {e}", "ERROR")
                    messagebox.showerror("Error", f"Failed to save screenshot:\n{str(e)}")
        
        # Header with save button
        header = tk.Frame(screenshot_window, bg="#263238", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Left side - title with resolution info
        title_frame = tk.Frame(header, bg="#263238")
        title_frame.pack(side="left", padx=20, pady=15)
        
        tk.Label(title_frame, text="📸 Client Screenshot", font=("Segoe UI", 14, "bold"), bg="#263238", fg="#FFFFFF").pack(anchor="w")
        
        quality_label = "4K Quality" if is_4k else "2K Quality" if is_2k else "HD Quality"
        tk.Label(title_frame, text=f"{orig_width}x{orig_height} • {quality_label}", font=("Segoe UI", 10), bg="#263238", fg="#90CAF9").pack(anchor="w")
        
        # Right side - save, original size, and close buttons
        btn_frame = tk.Frame(header, bg="#263238")
        btn_frame.pack(side="right", padx=20, pady=10)
        
        tk.Button(btn_frame, text="💾 Save 4K", command=save_img, font=("Segoe UI", 11, "bold"), bg="#4CAF50", fg="white", relief="flat", padx=25, pady=10, cursor="hand2").pack(side="left", padx=5)
        tk.Button(btn_frame, text="🔍 100% Size", command=lambda: show_original_size(original_image), font=("Segoe UI", 11, "bold"), bg="#2196F3", fg="white", relief="flat", padx=25, pady=10, cursor="hand2").pack(side="left", padx=5)
        tk.Button(btn_frame, text="✗ Close", command=screenshot_window.destroy, font=("Segoe UI", 11), bg="#757575", fg="white", relief="flat", padx=25, pady=10, cursor="hand2").pack(side="left", padx=5)
        
        # Scrollable image container for large screenshots
        canvas = tk.Canvas(screenshot_window, bg="#1E1E1E", highlightthickness=0)
        scrollbar_v = tk.Scrollbar(screenshot_window, orient="vertical", command=canvas.yview)
        scrollbar_h = tk.Scrollbar(screenshot_window, orient="horizontal", command=canvas.xview)
        
        img_frame = tk.Frame(canvas, bg="#1E1E1E")
        
        canvas.create_window((0, 0), window=img_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        # Display image
        photo = ImageTk.PhotoImage(display_image)
        label = tk.Label(img_frame, image=photo, bg="#1E1E1E")
        label.image = photo  # Keep reference
        label.pack(padx=20, pady=20)
        
        # Update scroll region
        img_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Pack scrollable widgets
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_v.pack(side="right", fill="y")
        scrollbar_h.pack(side="bottom", fill="x")
        
        # Mouse wheel scrolling support (Linux & Windows)
        def on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)  # Windows
        canvas.bind_all("<Button-4>", on_mousewheel)    # Linux scroll up
        canvas.bind_all("<Button-5>", on_mousewheel)    # Linux scroll down
        
        terminal_output.insert(tk.END, f"✓ Screenshot captured ({orig_width}x{orig_height})\n", "success")
        log_message(f"Screenshot displayed: {orig_width}x{orig_height} ({quality_label})", "SUCCESS")
        
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
    """Disconnect active client - thread-safe with proper UI updates"""
    global active_client_id
    
    try:
        # Must be called from main thread
        if threading.current_thread() != threading.main_thread():
            root.after(0, disconnect_active_client)
            return
        
        if not active_client_id:
            log_message("No active client to disconnect", "WARNING")
            return
        
        hostname = "Unknown"
        has_more_clients = False
        
        with clients_lock:
            if active_client_id not in clients:
                log_message("Active client already disconnected", "WARNING")
                active_client_id = None
                return
            
            try:
                # Send shutdown command to completely terminate client
                conn = clients[active_client_id]["conn"]
                conn.send("shutdown_client".encode())
                time.sleep(0.3)  # Reduced wait time
                conn.close()
            except Exception as e:
                log_message(f"Error sending shutdown: {e}", "WARNING")
            
            hostname = clients[active_client_id].get("info", {}).get("hostname", "Unknown")
            del clients[active_client_id]
            active_client_id = None
            
            has_more_clients = len(clients) > 0
        
        # All UI updates outside lock
        log_message(f"Client disconnected and terminated: {hostname}", "WARNING")
        update_client_list()
        
        if has_more_clients:
            # Auto-select next client
            root.after(100, lambda: select_client(0))
        else:
            # No more clients - disable UI
            update_status("No clients connected", "#FF7043", "⚠")
            for btn in command_buttons:
                btn.config(state="disabled")
            for btn in advanced_buttons:
                btn.config(state="disabled")
            disconnect_btn.config(state="disabled")
            terminal_output.config(state="disabled")
        
        terminal_output.insert(tk.END, "\n⚠ Client disconnected\n\n", "warning")
        terminal_output.see(tk.END)
        
    except Exception as e:
        log_message(f"Error in disconnect_active_client: {e}", "ERROR")
        messagebox.showerror("Disconnect Error", f"Failed to disconnect client:\n{str(e)}")

def check_client_connections():
    """Background thread to monitor client connections"""
    global active_client_id, stop_monitoring
    
    while server_running and not stop_monitoring:
        try:
            # Check each client connection
            disconnected_clients = []
            
            with clients_lock:
                for client_id, client_data in list(clients.items()):
                    try:
                        # Try to check if socket is still connected using getpeername
                        conn = client_data["conn"]
                        conn.getpeername()  # Will raise exception if disconnected
                    except:
                        disconnected_clients.append(client_id)
            
            # Remove disconnected clients and update UI
            for client_id in disconnected_clients:
                with clients_lock:
                    if client_id in clients:
                        hostname = clients[client_id].get("info", {}).get("hostname", "Unknown")
                        try:
                            clients[client_id]["conn"].close()
                        except:
                            pass
                        del clients[client_id]
                        
                        log_message(f"⚠️ Client disconnected: {hostname}", "WARNING")
                        
                        # Update UI in main thread
                        root.after(0, update_client_list)
                        
                        # If active client disconnected
                        if client_id == active_client_id:
                            active_client_id = None
                            root.after(0, lambda: update_status("Client disconnected", "#FF7043", "⚠"))
                            root.after(0, lambda: disconnect_btn.config(state="disabled"))
                            root.after(0, lambda: [btn.config(state="disabled") for btn in command_buttons])
                            root.after(0, lambda: [btn.config(state="disabled") for btn in advanced_buttons])
                            root.after(0, lambda: terminal_output.config(state="disabled"))
                            root.after(0, lambda: terminal_output.insert(tk.END, "\n⚠ Client connection lost\n\n", "warning"))
                            root.after(0, lambda: terminal_output.see(tk.END))
                            
                            # Auto-select next client if available
                            with clients_lock:
                                if clients:
                                    root.after(100, lambda: select_client(0))
            
            # Check every 3 seconds
            time.sleep(3)
            
        except Exception as e:
            time.sleep(3)
            continue

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

# Pack scrollbar first for proper layering
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

# Mouse wheel scrolling - ultra smooth 120Hz
def on_left_mousewheel(event):
    """Ultra smooth 120Hz mouse wheel scrolling with easing"""
    # Get scroll direction and amount
    if event.delta:
        # Windows - use smaller units for smoother scroll
        scroll_amount = int(-1 * (event.delta / 120))  # 1 unit per notch
    else:
        # Linux
        scroll_amount = -1 if event.num == 4 else 1
    
    # Smooth scroll with easing animation
    def smooth_scroll(remaining, step=0):
        if remaining == 0:
            return
        
        # Ease-out animation for buttery smooth feel
        current_step = min(remaining, 1)
        left_canvas.yview_scroll(current_step, "units")
        
        # Continue animation at 120Hz (8.3ms per frame)
        if remaining > 0:
            root.after(8, lambda: smooth_scroll(remaining - current_step, step + 1))
    
    # Start smooth scroll animation
    smooth_scroll(abs(scroll_amount) * 3 if scroll_amount < 0 else -abs(scroll_amount) * 3)
    
    return "break"  # Prevent scrolling other widgets

# Scrollbar drag support - bind to all child widgets
def enable_scrollbar_drag(widget):
    """Enable scrollbar drag for widget and all children"""
    try:
        # Bind mouse wheel
        widget.bind("<MouseWheel>", on_left_mousewheel, add="+")
        widget.bind("<Button-4>", on_left_mousewheel, add="+")
        widget.bind("<Button-5>", on_left_mousewheel, add="+")
        
        # Recursively bind to all children
        for child in widget.winfo_children():
            enable_scrollbar_drag(child)
    except:
        pass

# Bind mouse wheel to canvas and all widgets
def bind_left_mousewheel():
    """Bind mouse wheel events to left canvas"""
    left_canvas.bind("<MouseWheel>", on_left_mousewheel)
    left_canvas.bind("<Button-4>", on_left_mousewheel)
    left_canvas.bind("<Button-5>", on_left_mousewheel)
    # Also bind to all child widgets
    enable_scrollbar_drag(left_panel)

def unbind_left_mousewheel():
    """Unbind mouse wheel events from left canvas"""
    left_canvas.unbind("<MouseWheel>")
    left_canvas.unbind("<Button-4>")
    left_canvas.unbind("<Button-5>")

# Bind enter/leave to enable/disable scrolling
left_panel_container.bind("<Enter>", lambda e: bind_left_mousewheel())
left_panel_container.bind("<Leave>", lambda e: unbind_left_mousewheel())

# Initial binding
bind_left_mousewheel()

# Client List Section
tk.Label(left_panel, text="👥 CONNECTED CLIENTS", font=("Segoe UI", 11, "bold"), bg="#FFFFFF", fg="#424242").pack(anchor="w", padx=20, pady=(20, 10))

client_list_frame = tk.Frame(left_panel, bg="#F5F5F5", relief="flat")
client_list_frame.pack(fill="x", padx=15, pady=(0, 20))

client_listbox = tk.Listbox(client_list_frame, font=("Segoe UI", 10), bg="#FAFAFA", fg="#212121", height=6, relief="flat", selectbackground="#1976D2", selectforeground="white", borderwidth=0, highlightthickness=1, highlightbackground="#E0E0E0")
client_listbox.pack(fill="x", padx=5, pady=5)
client_listbox.bind("<<ListboxSelect>>", on_client_select)

tk.Label(client_list_frame, text="Click to select active client", font=("Segoe UI", 9), bg="#F5F5F5", fg="#757575").pack(pady=(5, 10))

# Quick Commands - OS-aware
tk.Label(left_panel, text="⚡ QUICK COMMANDS", font=("Segoe UI", 11, "bold"), bg="#FFFFFF", fg="#424242").pack(anchor="w", padx=20, pady=(15, 10))

commands_container = tk.Frame(left_panel, bg="#FFFFFF")
commands_container.pack(fill="x", padx=15)

command_buttons = []  # Only for quick command buttons
advanced_buttons = []  # For advanced, system, and process control buttons

# OS-specific commands - will be populated when client connects
def update_commands_for_client_os(client_os):
    """Update command buttons based on client OS"""
    # Clear existing command buttons only
    for widget in commands_container.winfo_children():
        widget.destroy()
    
    command_buttons.clear()
    
    # Detect OS type
    is_windows = "windows" in client_os.lower()
    is_linux = "linux" in client_os.lower()
    
    # Define OS-specific commands
    if is_windows:
        commands = [
            ("Network Info", "ipconfig /all", "🌐", "#2196F3"),
            ("Current User", "whoami", "👤", "#9C27B0"),
            ("List Files", "dir", "📁", "#FF9800"),
            ("System Info", "systeminfo", "💻", "#4CAF50"),
            ("Processes", "tasklist", "📊", "#00BCD4"),
            ("Current Path", "cd", "📍", "#E91E63"),
            ("Disk Info", "wmic logicaldisk get name,size,freespace", "💾", "#795548"),
            ("Network Status", "netstat -an", "📡", "#009688")
        ]
    elif is_linux:
        commands = [
            ("Network Info", "ifconfig -a", "🌐", "#2196F3"),
            ("Current User", "whoami", "👤", "#9C27B0"),
            ("List Files", "ls -la", "📁", "#FF9800"),
            ("System Info", "uname -a", "💻", "#4CAF50"),
            ("Processes", "ps aux", "📊", "#00BCD4"),
            ("Current Path", "pwd", "📍", "#E91E63"),
            ("Disk Info", "df -h", "💾", "#795548"),
            ("Network Status", "netstat -tuln", "📡", "#009688")
        ]
    else:
        # Generic/Unknown OS - use cross-platform commands
        commands = [
            ("Network Info", "NETWORK_INFO", "🌐", "#2196F3"),
            ("Current User", "whoami", "👤", "#9C27B0"),
            ("List Files", "LIST_FILES", "📁", "#FF9800"),
            ("System Info", "SYSTEM_INFO", "💻", "#4CAF50"),
            ("Processes", "PROCESSES", "📊", "#00BCD4"),
            ("Current Path", "cd", "📍", "#E91E63")
        ]
    
    # Create buttons
    for text, cmd, icon, color in commands:
        btn = tk.Button(
            commands_container, 
            text=f"{icon}  {text}", 
            command=lambda c=cmd, t=text: send_command_from_button(c, t), 
            font=("Segoe UI", 11, "bold"), 
            bg=color, 
            fg="white", 
            relief="flat", 
            padx=18, 
            pady=12, 
            cursor="hand2", 
            state="normal" if active_client_id else "disabled", 
            anchor="w", 
            activebackground=color, 
            activeforeground="white"
        )
        btn.pack(fill="x", pady=4)
        command_buttons.append(btn)
    
    # Enable advanced buttons too
    for btn in advanced_buttons:
        btn.config(state="normal")
    
    log_message(f"Commands updated for {client_os}", "INFO")

# Initial empty state - will populate when client connects
initial_label = tk.Label(
    commands_container, 
    text="Connect a client to see\nOS-specific commands", 
    font=("Segoe UI", 10), 
    bg="#FFFFFF", 
    fg="#9E9E9E",
    justify="center"
)
initial_label.pack(pady=30)

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
    advanced_buttons.append(btn)  # Add to advanced_buttons list

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
    advanced_buttons.append(btn)  # Add to advanced_buttons list

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
    advanced_buttons.append(btn)  # Add to advanced_buttons list

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
# Detect OS and set appropriate font
import platform
current_os = platform.system()

if current_os == "Windows":
    terminal_font = ("Consolas", 11)  # Windows Command Prompt style
    terminal_bg = "#000000"  # Black background like Windows terminal
    terminal_fg = "#00FF00"  # Green text like classic Windows
elif current_os == "Linux":
    terminal_font = ("Ubuntu Mono", 11)  # Linux terminal style
    terminal_bg = "#300A24"  # Dark background like Linux terminal
    terminal_fg = "#FFFFFF"  # White text like Linux terminal
else:
    terminal_font = ("Courier New", 11)  # Fallback monospace
    terminal_bg = "#1E1E1E"  # Dark theme
    terminal_fg = "#C9D1D9"  # GitHub terminal style

terminal_output = scrolledtext.ScrolledText(
        terminal_section, 
        font=terminal_font, 
        bg=terminal_bg, 
        fg=terminal_fg, 
        insertbackground="#58A6FF", 
        relief="flat", 
        wrap="word", 
        padx=25, 
        pady=20, 
        state="normal"
    )
terminal_output.pack(fill="both", expand=True)

# Terminal tags - OS-specific colors
if current_os == "Windows":
    # Windows Command Prompt colors
    terminal_output.tag_config("prompt", foreground="#00FF00", font=("Consolas", 12, "bold"))
    terminal_output.tag_config("command", foreground="#FFFFFF", font=("Consolas", 12, "bold"))
    terminal_output.tag_config("output", foreground="#00FF00", font=("Consolas", 11))
    terminal_output.tag_config("success", foreground="#00FFFF", font=("Consolas", 12, "bold"))
    terminal_output.tag_config("error", foreground="#FF0000", font=("Consolas", 12, "bold"))
    terminal_output.tag_config("warning", foreground="#FFFF00", font=("Consolas", 12))
    terminal_output.tag_config("separator", foreground="#808080", font=("Consolas", 11))
    terminal_output.tag_config("loading", foreground="#00FFFF", font=("Consolas", 11))
elif current_os == "Linux":
    # Linux terminal colors
    terminal_output.tag_config("prompt", foreground="#00FF00", font=("Ubuntu Mono", 12, "bold"))
    terminal_output.tag_config("command", foreground="#FFFFFF", font=("Ubuntu Mono", 12, "bold"))
    terminal_output.tag_config("output", foreground="#FFFFFF", font=("Ubuntu Mono", 11))
    terminal_output.tag_config("success", foreground="#00FF00", font=("Ubuntu Mono", 12, "bold"))
    terminal_output.tag_config("error", foreground="#FF0000", font=("Ubuntu Mono", 12, "bold"))
    terminal_output.tag_config("warning", foreground="#FFFF00", font=("Ubuntu Mono", 12))
    terminal_output.tag_config("separator", foreground="#808080", font=("Ubuntu Mono", 11))
    terminal_output.tag_config("loading", foreground="#00FFFF", font=("Ubuntu Mono", 11))
else:
    # Default colors
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

# Welcome - OS-specific terminal welcome
if current_os == "Windows":
    # Windows Command Prompt style
    terminal_output.insert(tk.END, "Microsoft Windows [Version 10.0.19045.2364]\n", "output")
    terminal_output.insert(tk.END, "(c) 2024 Microsoft Corporation. All rights reserved.\n", "output")
    terminal_output.insert(tk.END, "\nC:\\Users\\RemoteAdmin> ", "prompt")
elif current_os == "Linux":
    # Linux terminal style
    import os
    username = os.getenv('USER', 'user')
    hostname = os.getenv('HOSTNAME', 'localhost')
    terminal_output.insert(tk.END, f"┌─({username}@{hostname})─[~]\n", "prompt")
    terminal_output.insert(tk.END, "└─$ ", "prompt")
else:
    # Default welcome
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
    """Handle key press in terminal - real terminal features"""
    try:
        # Check if client is active
        with clients_lock:
            has_active_client = active_client_id and active_client_id in clients
        
        if not has_active_client:
            return "break"
        
        # Get current cursor position safely
        try:
            insert_pos = terminal_output.index("insert")
            input_start_pos = terminal_output.index("input_start")
        except tk.TclError:
            return "break"
        
        # Handle Return key - Execute command in thread for smooth UI
        if event.keysym == "Return":
            try:
                cmd = terminal_output.get("input_start", "end-1c").strip()
                
                if cmd:
                    # Add to history
                    command_history.append(cmd)
                    global history_index
                    history_index = len(command_history)
                    
                    # Add newline
                    terminal_output.insert(tk.END, "\n")
                    terminal_output.see(tk.END)
                    
                    # Execute command in separate thread for smooth 120Hz UI
                    threading.Thread(
                        target=execute_command, 
                        args=(cmd, cmd), 
                        daemon=True,
                        name=f"FastCmd-{cmd[:15]}"
                    ).start()
                else:
                    # Empty command - just show new prompt
                    terminal_output.insert(tk.END, "\n")
                    terminal_output.insert(tk.END, "Remote-Admin> ", "prompt")
                    terminal_output.mark_set("input_start", "end-1c")
                    terminal_output.see(tk.END)
            except Exception as e:
                log_message(f"Command execution error: {e}", "ERROR")
            
            return "break"
        
        # Handle Tab key - Command completion (OS-aware)
        elif event.keysym == "Tab":
            try:
                current_input = terminal_output.get("input_start", "end-1c")
                
                # Get client OS
                client_os = "Unknown"
                with clients_lock:
                    if active_client_id and active_client_id in clients:
                        client_os = clients[active_client_id].get("info", {}).get("os", "Unknown")
                
                is_windows = "windows" in client_os.lower()
                is_linux = "linux" in client_os.lower()
                
                # OS-specific commands for completion
                if is_windows:
                    commands = [
                        "SCREENSHOT", "DOWNLOAD:", "UPLOAD:", "SYSINFO",
                        "ipconfig", "dir", "cd", "whoami", "systeminfo", "tasklist",
                        "netstat", "ping", "tracert", "cls", "copy", "move", "del",
                        "mkdir", "rmdir", "type", "echo", "set", "wmic", "shutdown",
                        "restart", "taskkill", "reg", "sc", "net", "hostname"
                    ]
                elif is_linux:
                    commands = [
                        "SCREENSHOT", "DOWNLOAD:", "UPLOAD:", "SYSINFO",
                        "ifconfig", "ls", "cd", "pwd", "whoami", "uname", "ps",
                        "netstat", "ping", "traceroute", "clear", "cp", "mv", "rm",
                        "mkdir", "rmdir", "cat", "echo", "export", "df", "du",
                        "shutdown", "reboot", "kill", "grep", "find", "chmod",
                        "chown", "sudo", "apt", "yum", "systemctl", "hostname"
                    ]
                else:
                    # Generic commands
                    commands = [
                        "SCREENSHOT", "DOWNLOAD:", "UPLOAD:", "SYSINFO", "NETWORK_INFO",
                        "SYSTEM_INFO", "PROCESSES", "LIST_FILES",
                        "whoami", "cd", "exit"
                    ]
                
                # Find matching commands
                matches = [cmd for cmd in commands if cmd.lower().startswith(current_input.lower())]
                
                if len(matches) == 1:
                    # Single match - auto complete
                    terminal_output.delete("input_start", "end-1c")
                    terminal_output.insert("input_start", matches[0])
                elif len(matches) > 1:
                    # Multiple matches - show options
                    terminal_output.insert(tk.END, "\n")
                    terminal_output.insert(tk.END, "  ".join(matches[:10]) + "\n", "output")  # Show max 10
                    if len(matches) > 10:
                        terminal_output.insert(tk.END, f"... and {len(matches)-10} more\n", "output")
                    terminal_output.insert(tk.END, "Remote-Admin> ", "prompt")
                    terminal_output.insert(tk.END, current_input)
                    terminal_output.mark_set("input_start", f"end-{len(current_input)+1}c")
                
                terminal_output.mark_set("insert", "end")
            except Exception as e:
                log_message(f"Tab completion error: {e}", "ERROR")
            
            return "break"
        
        # Handle Up arrow - Previous command in history
        elif event.keysym == "Up":
            try:
                if command_history and history_index > 0:
                    history_index -= 1
                    terminal_output.delete("input_start", "end-1c")
                    terminal_output.insert("input_start", command_history[history_index])
                    terminal_output.mark_set("insert", "end")
            except Exception as e:
                log_message(f"History up error: {e}", "ERROR")
            
            return "break"
        
        # Handle Down arrow - Next command in history
        elif event.keysym == "Down":
            try:
                if command_history:
                    if history_index < len(command_history) - 1:
                        history_index += 1
                        terminal_output.delete("input_start", "end-1c")
                        terminal_output.insert("input_start", command_history[history_index])
                    else:
                        history_index = len(command_history)
                        terminal_output.delete("input_start", "end-1c")
                    terminal_output.mark_set("insert", "end")
            except Exception as e:
                log_message(f"History down error: {e}", "ERROR")
            
            return "break"
        
        # Handle BackSpace - Prevent deleting prompt
        elif event.keysym == "BackSpace":
            try:
                if terminal_output.compare("insert", "<=", "input_start"):
                    return "break"
            except tk.TclError:
                return "break"
        
        # Handle Delete key - Prevent deleting beyond input area
        elif event.keysym == "Delete":
            try:
                if terminal_output.compare("insert", ">=", "end-1c"):
                    return "break"
            except tk.TclError:
                return "break"
        
        # Handle Left arrow - Prevent moving before prompt
        elif event.keysym == "Left":
            try:
                if terminal_output.compare("insert", "<=", "input_start"):
                    return "break"
            except tk.TclError:
                return "break"
        
        # Handle Home key - Move to start of input (after prompt)
        elif event.keysym == "Home":
            try:
                terminal_output.mark_set("insert", "input_start")
                return "break"
            except tk.TclError:
                return "break"
        
        # Handle End key - Move to end of input
        elif event.keysym == "End":
            try:
                terminal_output.mark_set("insert", "end-1c")
                return "break"
            except tk.TclError:
                return "break"
        
        # Handle Ctrl+A - Select all input text
        elif event.char == '\x01':  # Ctrl+A
            try:
                terminal_output.tag_add("sel", "input_start", "end-1c")
                terminal_output.mark_set("insert", "end-1c")
                return "break"
            except tk.TclError:
                return "break"
        
        # Handle Ctrl+C - Clear current input OR copy selection
        elif event.char == '\x03':  # Ctrl+C
            try:
                # Check if there's a selection
                if terminal_output.tag_ranges("sel"):
                    # Copy selected text to clipboard
                    selected_text = terminal_output.get("sel.first", "sel.last")
                    root.clipboard_clear()
                    root.clipboard_append(selected_text)
                    log_message("Text copied to clipboard", "INFO")
                else:
                    # No selection - clear current input
                    terminal_output.delete("input_start", "end-1c")
                return "break"
            except tk.TclError:
                return "break"
        
        # Handle Ctrl+V - Paste from clipboard
        elif event.char == '\x16':  # Ctrl+V
            try:
                clipboard_text = root.clipboard_get()
                # Insert at cursor position
                terminal_output.insert("insert", clipboard_text)
                return "break"
            except tk.TclError:
                pass  # Clipboard empty or error
            return "break"
        
        # Handle Ctrl+X - Cut selected text
        elif event.char == '\x18':  # Ctrl+X
            try:
                if terminal_output.tag_ranges("sel"):
                    # Check if selection is within input area
                    sel_start = terminal_output.index("sel.first")
                    if terminal_output.compare(sel_start, ">=", "input_start"):
                        selected_text = terminal_output.get("sel.first", "sel.last")
                        root.clipboard_clear()
                        root.clipboard_append(selected_text)
                        terminal_output.delete("sel.first", "sel.last")
                        log_message("Text cut to clipboard", "INFO")
                return "break"
            except tk.TclError:
                return "break"
        
        # Handle Ctrl+L - Clear terminal
        elif event.char == '\x0c':  # Ctrl+L
            clear_terminal()
            return "break"
        
        # Handle Ctrl+U - Clear line (delete from cursor to start of input)
        elif event.char == '\x15':  # Ctrl+U
            try:
                terminal_output.delete("input_start", "insert")
                return "break"
            except tk.TclError:
                return "break"
        
        # Handle Ctrl+K - Kill line (delete from cursor to end of input)
        elif event.char == '\x0b':  # Ctrl+K
            try:
                terminal_output.delete("insert", "end-1c")
                return "break"
            except tk.TclError:
                return "break"
        
        # Handle Ctrl+W - Delete word before cursor
        elif event.char == '\x17':  # Ctrl+W
            try:
                current_pos = terminal_output.index("insert")
                line_start = terminal_output.index("input_start")
                
                # Get text from line start to cursor
                text = terminal_output.get(line_start, current_pos)
                
                # Find last word boundary
                words = text.rstrip().rsplit(None, 1)
                if len(words) > 1:
                    delete_from = f"{line_start}+{len(words[0])}c"
                    terminal_output.delete(delete_from, current_pos)
                else:
                    terminal_output.delete(line_start, current_pos)
                
                return "break"
            except tk.TclError:
                return "break"
        
        # Handle Ctrl+D - Delete character under cursor (or exit if empty)
        elif event.char == '\x04':  # Ctrl+D
            try:
                current_input = terminal_output.get("input_start", "end-1c").strip()
                if not current_input:
                    # Empty line - send exit command
                    terminal_output.insert(tk.END, "exit\n")
                    execute_command("exit", "exit")
                else:
                    # Delete character under cursor
                    if terminal_output.compare("insert", "<", "end-1c"):
                        terminal_output.delete("insert")
                return "break"
            except tk.TclError:
                return "break"
        
        # Handle Ctrl+R - Reverse search in history (simplified)
        elif event.char == '\x12':  # Ctrl+R
            try:
                search_term = terminal_output.get("input_start", "end-1c")
                if search_term and command_history:
                    # Find last matching command
                    for i in range(len(command_history) - 1, -1, -1):
                        if search_term.lower() in command_history[i].lower():
                            terminal_output.delete("input_start", "end-1c")
                            terminal_output.insert("input_start", command_history[i])
                            history_index = i
                            break
                return "break"
            except Exception as e:
                log_message(f"History search error: {e}", "ERROR")
            return "break"
        
        # For all other keys, ensure cursor is after prompt
        else:
            try:
                if terminal_output.compare("insert", "<", "input_start"):
                    terminal_output.mark_set("insert", "end")
            except tk.TclError:
                pass
    
    except Exception as e:
        log_message(f"Terminal key error: {e}", "ERROR")
        return "break"

# Mouse click handler - ensure cursor stays after prompt
def on_terminal_click(event):
    """Handle mouse click in terminal"""
    try:
        # Let the click happen first
        terminal_output.after(1, lambda: ensure_cursor_after_prompt())
    except Exception as e:
        log_message(f"Terminal click error: {e}", "ERROR")

def ensure_cursor_after_prompt():
    """Ensure cursor is positioned after the prompt"""
    try:
        if terminal_output.compare("insert", "<", "input_start"):
            terminal_output.mark_set("insert", "end")
    except tk.TclError:
        pass

# Right-click context menu for terminal
def show_terminal_context_menu(event):
    """Show right-click context menu"""
    try:
        context_menu = tk.Menu(terminal_output, tearoff=0)
        
        # Copy
        context_menu.add_command(
            label="📋 Copy (Ctrl+C)",
            command=lambda: copy_terminal_selection()
        )
        
        # Paste
        context_menu.add_command(
            label="📄 Paste (Ctrl+V)",
            command=lambda: paste_to_terminal()
        )
        
        context_menu.add_separator()
        
        # Select All
        context_menu.add_command(
            label="🔘 Select All (Ctrl+A)",
            command=lambda: terminal_output.tag_add("sel", "input_start", "end-1c")
        )
        
        context_menu.add_separator()
        
        # Clear
        context_menu.add_command(
            label="🗑️ Clear Terminal (Ctrl+L)",
            command=clear_terminal
        )
        
        context_menu.post(event.x_root, event.y_root)
    except Exception as e:
        log_message(f"Context menu error: {e}", "ERROR")

def copy_terminal_selection():
    """Copy selected text to clipboard"""
    try:
        if terminal_output.tag_ranges("sel"):
            selected_text = terminal_output.get("sel.first", "sel.last")
            root.clipboard_clear()
            root.clipboard_append(selected_text)
            log_message("Text copied", "INFO")
    except tk.TclError:
        pass

def paste_to_terminal():
    """Paste from clipboard to terminal"""
    try:
        clipboard_text = root.clipboard_get()
        terminal_output.insert("insert", clipboard_text)
    except tk.TclError:
        pass

terminal_output.bind("<Key>", on_terminal_key)
terminal_output.bind("<Button-1>", on_terminal_click)
terminal_output.bind("<Button-3>", show_terminal_context_menu)  # Right-click menu
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

# Start the application - now safe to log messages
log_message("🚀 Application started", "SUCCESS")
log_message(f"🌐 Server ready on {HOST}:{PORT}", "INFO")
log_message("⏳ Waiting for connections...", "INFO")

root.mainloop()
