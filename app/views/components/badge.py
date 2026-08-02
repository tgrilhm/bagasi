"""Status badge label."""
import customtkinter as ctk

STATUS_COLORS = {
    "Terbuka": ("#27ae60", "#d5f5e3"),
    "Dikirim": ("#e67e22", "#fef5e7"),
    "Selesai": ("#7f8c8d", "#f2f3f4"),
    "Admin":   ("#8e44ad", "#f4ecf7"),
    "Karyawan":("#2980b9", "#ebf5fb"),
    "Aktif":   ("#27ae60", "#d5f5e3"),
    "Nonaktif":("#e74c3c", "#fadbd8"),
}


class StatusBadge(ctk.CTkLabel):
    def __init__(self, parent, status: str, **kwargs):
        fg, bg = STATUS_COLORS.get(status, ("#555", "#eee"))
        super().__init__(
            parent,
            text=f"  {status}  ",
            text_color=fg,
            fg_color=bg,
            corner_radius=10,
            font=ctk.CTkFont(size=11, weight="bold"),
            **kwargs,
        )
