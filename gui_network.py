"""
gui_network.py - Server & Client Network Logic
"""
import socket
import threading
import time
import json
import tkinter as tk
from tkinter import messagebox
import gui_globals as g


def log_message(message, level="INFO"):
    g.log_message(message, level)


def update_status(text, color, icon):
    g.root.after(0, lambda: g.status_icon.config(text=icon))
    g.root.after(0, lambda: g.status_text.config(text=text, foreground=color))


def update_client_list():
    """Update client listbox — thread-safe."""
    try:
        if threading.current_thread() != threading.main_thread():
            g.root.after(0, update_client_list)
            return
        g.client_listbox.delete(0, tk.END)
        with g.clients_lock:
            if not g.clients:
                return
            clients_copy = list(g.clients.items())
        for client_id, client_data in clients_copy:
            try:
                info = client_data.get("info", {})
                hostname = info.get("hostname", "Unknown")
                ip = client_data["addr"][0]
                status = "🟢" if client_id == g.active_client_id else "⚪"
                g.client_listbox.insert(tk.END, f"{status} {hostname} ({ip})")
            except Exception:
                continue
    except Exception as e:
        print(f"[ERROR] update_client_list: {e}")


def start_server():
    """Start TCP server in background thread."""
    if g.server_running:
        messagebox.showwarning("Server Running", "Server is already running!")
        return

    def server_thread():
        try:
            g.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            g.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                g.server_socket.bind((g.HOST, g.PORT))
            except OSError as e:
                g.root.after(0, lambda: messagebox.showerror("Server Error", f"Cannot bind to port {g.PORT}.\nPort may be in use."))
                return
            g.server_socket.listen(5)
            g.server_socket.settimeout(1.0)
            g.server_running = True
            g.stop_monitoring = False

            g.root.after(0, lambda: log_message(f"Server started on {g.HOST}:{g.PORT}", "SUCCESS"))
            g.root.after(0, lambda: update_status("Server listening...", "#66BB6A", "✓"))
            g.root.after(0, lambda: g.connect_btn.config(state="disabled", text="✓ Server Running", bg="#43A047"))
            g.root.after(0, lambda: g.stop_server_btn.config(state="normal"))
            g.root.after(0, lambda: g.disconnect_btn.config(state="disabled"))

            while g.server_running:
                try:
                    conn, addr = g.server_socket.accept()
                    conn.settimeout(5.0)
                    try:
                        data = conn.recv(4096).decode('utf-8', errors='ignore')
                        if not data:
                            conn.close()
                            continue
                        client_info = json.loads(data)
                    except Exception:
                        # If they don't send valid JSON, they aren't our real client (might be a scanner or old version)
                        conn.close()
                        continue

                    conn.settimeout(None)
                    client_id = f"{addr[0]}:{addr[1]}"
                    with g.clients_lock:
                        g.clients[client_id] = {"conn": conn, "addr": addr, "info": client_info}
                        total = len(g.clients)
                    hostname = client_info.get('hostname', 'Unknown')
                    g.root.after(0, lambda h=hostname, ip=addr[0]: log_message(f"Client connected: {h} from {ip}", "SUCCESS"))
                    g.root.after(100, update_client_list)
                    if total == 1:
                        g.root.after(200, lambda: select_client(0))
                except socket.timeout:
                    continue
                except Exception as e:
                    if g.server_running:
                        g.root.after(0, lambda e=e: log_message(f"Accept error: {str(e)}", "ERROR"))
        except Exception as e:
            g.root.after(0, lambda e=e: messagebox.showerror("Server Error", f"Server failed:\n{str(e)}"))
            g.server_running = False
        finally:
            if g.server_socket:
                try:
                    g.server_socket.close()
                except Exception:
                    pass
            g.server_running = False
            g.root.after(0, lambda: g.connect_btn.config(state="normal", text="🚀 Start Server", bg="#1976D2"))
            g.root.after(0, lambda: g.stop_server_btn.config(state="disabled"))
            g.root.after(0, lambda: g.disconnect_btn.config(state="disabled"))

    threading.Thread(target=server_thread, daemon=True, name="ServerThread").start()
    time.sleep(0.5)
    threading.Thread(target=check_client_connections, daemon=True, name="MonitorThread").start()


def stop_server():
    """Stop server and disconnect all clients."""
    if not g.server_running:
        log_message("Server is not running", "WARNING")
        return
    if not messagebox.askyesno("Stop Server", "Stop server and disconnect all clients?"):
        return
    g.server_running = False
    g.stop_monitoring = True
    with g.clients_lock:
        client_count = len(g.clients)
        for client_id in list(g.clients.keys()):
            try:
                g.clients[client_id]["conn"].close()
            except Exception:
                pass
        g.clients.clear()
        g.active_client_id = None
    update_client_list()
    update_status("Server stopped", "#FF7043", "⚠")
    log_message("Server stopped", "WARNING")
    for btn in g.command_buttons:
        btn.config(state="disabled")
    for btn in g.advanced_buttons:
        btn.config(state="disabled")
    g.connect_btn.config(state="normal", text="🚀 Start Server", bg="#1976D2")
    g.stop_server_btn.config(state="disabled")
    g.disconnect_btn.config(state="disabled")
    g.terminal_output.config(state="disabled")
    g.terminal_output.insert(tk.END, "\n⚠ Server stopped\n\n", "warning")
    g.terminal_output.see(tk.END)


def select_client(index):
    """Select active client."""
    try:
        if threading.current_thread() != threading.main_thread():
            g.root.after(0, lambda: select_client(index))
            return
        with g.clients_lock:
            if index < 0 or index >= len(g.clients):
                return
            client_id = list(g.clients.keys())[index]
            if client_id not in g.clients:
                return
            g.active_client_id = client_id
            client_data = g.clients[g.active_client_id]
            info = client_data.get("info", {})
            addr = client_data['addr']
            client_os = info.get("os", "Unknown")
        
        # ── Detect OS and set badge ──────────────────────────────────────────
        os_lower = client_os.lower()
        if "windows" in os_lower:
            os_badge = "🪟 Windows"
            os_color  = "success"
        elif "linux" in os_lower:
            os_badge = "🐧 Linux"
            os_color  = "success"
        elif "darwin" in os_lower or "mac" in os_lower:
            os_badge = "🍎 macOS"
            os_color  = "success"
        else:
            os_badge = f"❓ {client_os}"
            os_color  = "warning"

        update_client_list()
        update_status(f"Active: {info.get('hostname', 'Unknown')} ({addr[0]})", "#66BB6A", "✓")

        # ── Build OS-specific command buttons FIRST, then enable them ─────────
        import gui_commands as cmds
        cmds.update_commands_for_client_os(client_os)   # populates g.command_buttons

        g.disconnect_btn.config(state="normal")
        g.terminal_output.config(state="normal")
        g.terminal_output.focus()

        # ── Show connection banner in terminal ────────────────────────────────
        sep = "═" * 68
        g.terminal_output.insert(tk.END, f"\n{sep}\n", "separator")
        g.terminal_output.insert(tk.END, f"  ✓  CLIENT CONNECTED\n", "success")
        g.terminal_output.insert(tk.END, f"     Hostname : {info.get('hostname','Unknown')}\n", "output")
        g.terminal_output.insert(tk.END, f"     OS       : {os_badge} ({client_os})\n", os_color)
        g.terminal_output.insert(tk.END, f"     IP       : {addr[0]}:{addr[1]}\n", "output")
        g.terminal_output.insert(tk.END, f"     User     : {info.get('user','Unknown')}\n", "output")
        g.terminal_output.insert(tk.END, f"{sep}\n\n", "separator")
        g.terminal_output.insert(tk.END, "Remote-Admin> ", "prompt")
        g.terminal_output.mark_set("input_start", "end-1c")
        g.terminal_output.mark_gravity("input_start", "left")
        g.terminal_output.see(tk.END)
        log_message(f"Client selected: {info.get('hostname','Unknown')} | {os_badge}", "SUCCESS")
    except Exception as e:
        log_message(f"Error selecting client: {e}", "ERROR")



def on_client_select(event):
    selection = g.client_listbox.curselection()
    if selection:
        select_client(selection[0])


def disconnect_active_client():
    """Force disconnect and kill active client."""
    try:
        if threading.current_thread() != threading.main_thread():
            g.root.after(0, disconnect_active_client)
            return
        if not g.active_client_id:
            log_message("No active client to disconnect", "WARNING")
            return
        hostname = "Unknown"
        has_more = False
        with g.clients_lock:
            if g.active_client_id not in g.clients:
                g.active_client_id = None
                return
            try:
                conn = g.clients[g.active_client_id]["conn"]
                conn.send("shutdown_client".encode())
                time.sleep(0.3)
                conn.close()
            except Exception as e:
                log_message(f"Error sending shutdown: {e}", "WARNING")
            hostname = g.clients[g.active_client_id].get("info", {}).get("hostname", "Unknown")
            del g.clients[g.active_client_id]
            g.active_client_id = None
            has_more = len(g.clients) > 0
        log_message(f"Client disconnected: {hostname}", "WARNING")
        update_client_list()
        if has_more:
            g.root.after(100, lambda: select_client(0))
        else:
            update_status("No clients connected", "#FF7043", "⚠")
            for btn in g.command_buttons:
                btn.config(state="disabled")
            for btn in g.advanced_buttons:
                btn.config(state="disabled")
            g.disconnect_btn.config(state="disabled")
            g.terminal_output.config(state="disabled")
        g.terminal_output.insert(tk.END, "\n⚠ Client disconnected\n\n", "warning")
        g.terminal_output.see(tk.END)
    except Exception as e:
        log_message(f"Error disconnecting client: {e}", "ERROR")


def _is_socket_alive(sock):
    """Actually probe the socket to see if it's still connected."""
    try:
        old_timeout = sock.gettimeout()
        sock.setblocking(False)
        try:
            data = sock.recv(1, socket.MSG_PEEK)
            return data != b""   # empty bytes = graceful close
        except BlockingIOError:
            return True           # would block = still alive
        finally:
            sock.settimeout(old_timeout)
    except Exception:
        return False


def check_client_connections():
    """Background monitor for dropped connections."""
    while g.server_running and not g.stop_monitoring:
        try:
            disconnected = []
            with g.clients_lock:
                clients_snapshot = list(g.clients.items())
            for client_id, client_data in clients_snapshot:
                if not _is_socket_alive(client_data["conn"]):
                    disconnected.append(client_id)
            for client_id in disconnected:
                with g.clients_lock:
                    if client_id not in g.clients:
                        continue
                    hostname = g.clients[client_id].get("info", {}).get("hostname", "Unknown")
                    try:
                        g.clients[client_id]["conn"].close()
                    except Exception:
                        pass
                    del g.clients[client_id]
                was_active = (client_id == g.active_client_id)
                if was_active:
                    g.active_client_id = None
                log_message(f"Client lost: {hostname}", "WARNING")
                g.root.after(0, update_client_list)
                if was_active:
                    g.root.after(0, lambda: update_status("Client disconnected", "#FF7043", "⚠"))
                    g.root.after(0, lambda: g.disconnect_btn.config(state="disabled"))
                    g.root.after(0, lambda: [btn.config(state="disabled") for btn in g.command_buttons])
                    g.root.after(0, lambda: [btn.config(state="disabled") for btn in g.advanced_buttons])
                    g.root.after(0, lambda: g.terminal_output.config(state="disabled"))
                    with g.clients_lock:
                        if g.clients:
                            g.root.after(100, lambda: select_client(0))
            time.sleep(3)
        except Exception:
            time.sleep(3)
