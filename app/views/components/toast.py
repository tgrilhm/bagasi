"""Toast notification — muncul sudut kanan bawah, auto-dismiss."""
import tkinter as tk
import customtkinter as ctk

_COLORS = {
    "success": ("#1e8449", "#d5f5e3"),
    "error":   ("#c0392b", "#fadbd8"),
    "warning": ("#d68910", "#fef9e7"),
    "info":    ("#1a5276", "#d6eaf8"),
}
_ICONS = {"success": "✓", "error": "✕", "warning": "⚠", "info": "ℹ"}


def show_toast(root: tk.Tk, message: str, kind: str = "success", duration: int = 3000) -> None:
    """Tampilkan toast notification di sudut kanan bawah root window."""
    fg, bg = _COLORS.get(kind, _COLORS["info"])
    icon   = _ICONS.get(kind, "•")

    toast = tk.Toplevel(root)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    toast.configure(bg=bg)

    frame = tk.Frame(toast, bg=bg, bd=0)
    frame.pack(fill="both", expand=True, padx=1, pady=1)

    tk.Label(frame, text=icon, bg=bg, fg=fg,
             font=("Arial", 14, "bold")).pack(side="left", padx=(12, 6), pady=10)
    tk.Label(frame, text=message, bg=bg, fg="#111",
             font=("Arial", 10), wraplength=260, justify="left").pack(
                 side="left", padx=(0, 14), pady=10)

    # Posisi: kanan bawah window utama
    root.update_idletasks()
    rw = root.winfo_width()
    rh = root.winfo_height()
    rx = root.winfo_x()
    ry = root.winfo_y()
    tw = 320
    th = 52
    x = rx + rw - tw - 20
    y = ry + rh - th - 20
    toast.geometry(f"{tw}x{th}+{x}+{y}")

    # Border simulasi dengan outline frame
    toast.configure(highlightbackground=fg, highlightcolor=fg, highlightthickness=1)

    toast.after(duration, toast.destroy)
