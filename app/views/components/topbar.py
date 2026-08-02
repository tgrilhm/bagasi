"""Topbar atas — breadcrumb + jam real-time + sync status + theme toggle."""
import tkinter as tk
from datetime import datetime
from typing import Callable
import customtkinter as ctk

_SYNC_ICONS = {
    "idle":         ("🟢 Tersinkron",   "#27ae60"),
    "syncing":      ("🔄 Syncing...",   "#f39c12"),
    "error":        ("🔴 Sync Error",   "#e74c3c"),
    "disconnected": ("⚪ Offline",      "gray"),
}


class Topbar(ctk.CTkFrame):
    def __init__(self, parent, on_theme_toggle: Callable, **kwargs):
        super().__init__(parent, height=52, corner_radius=0, **kwargs)
        self.pack_propagate(False)
        self._on_theme_toggle  = on_theme_toggle
        self._breadcrumb_var   = tk.StringVar(value="Dashboard")
        self._clock_var        = tk.StringVar()
        self._sync_var         = tk.StringVar(value="⚪ Offline")
        self._last_sync_status = "disconnected"
        self._build()
        self._tick()

    def _build(self) -> None:
        # Breadcrumb (kiri)
        ctk.CTkLabel(
            self,
            textvariable=self._breadcrumb_var,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="gray",
        ).pack(side="left", padx=20)

        # Kanan: sync status + jam + theme toggle
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=16)

        # Theme toggle
        self._theme_btn = ctk.CTkButton(
            right, text="🌙", width=36, height=36,
            fg_color="transparent",
            hover_color=("#e0e0e0", "#2d2d2d"),
            command=self._on_theme_toggle,
            font=ctk.CTkFont(size=16),
        )
        self._theme_btn.pack(side="right", padx=(8, 0))

        # Clock
        ctk.CTkLabel(
            right,
            textvariable=self._clock_var,
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(side="right", padx=(12, 0))

        # Sync status indicator
        self._sync_lbl = ctk.CTkLabel(
            right,
            textvariable=self._sync_var,
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self._sync_lbl.pack(side="right", padx=(0, 16))

    def _tick(self) -> None:
        # Update jam
        now   = datetime.now()
        hari  = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
        bulan = ["","Jan","Feb","Mar","Apr","Mei","Jun",
                 "Jul","Agu","Sep","Okt","Nov","Des"]
        self._clock_var.set(
            f"{hari[now.weekday()]}, {now.day} {bulan[now.month]} {now.year}"
            f"  —  {now.strftime('%H:%M:%S')}"
        )

        # Poll sync status di main thread (aman, tidak ada I/O)
        try:
            from ...services.sheets_sync import sync as gs_sync
            status = gs_sync.get_status()
            if status != self._last_sync_status:
                self._last_sync_status = status
                icon, color = _SYNC_ICONS.get(status, ("⚪ Offline", "gray"))
                self._sync_var.set(icon)
                self._sync_lbl.configure(text_color=color)
        except Exception:
            pass

        self.after(1000, self._tick)

    def set_breadcrumb(self, text: str) -> None:
        self._breadcrumb_var.set(text)

    def update_theme_icon(self, mode: str) -> None:
        self._theme_btn.configure(text="☀️" if mode == "dark" else "🌙")
