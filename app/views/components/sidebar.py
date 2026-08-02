"""
Enterprise sidebar navigation dengan collapsible support.
"""
import tkinter as tk
from typing import Callable
import customtkinter as ctk

from ...core.session import Session

MENU_ITEMS = [
    ("dashboard", "🏠", "Dashboard"),
    ("kloter",    "📦", "Kloter"),
    ("pengaturan","⚙️",  "Pengaturan"),
]
MENU_ADMIN = [
    ("karyawan",  "👥", "Karyawan"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_navigate: Callable[[str], None], **kwargs):
        super().__init__(parent, width=220, corner_radius=0,
                         fg_color="#0f1729", **kwargs)
        self.pack_propagate(False)
        self._on_navigate = on_navigate
        self._active_page = "dashboard"
        self._collapsed   = False
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._build()

    def _build(self) -> None:
        # Logo area
        logo_frame = ctk.CTkFrame(self, fg_color="#0a1020", corner_radius=0)
        logo_frame.pack(fill="x")

        ctk.CTkLabel(
            logo_frame,
            text="🧳 Amanah",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white",
        ).pack(pady=(18, 2))
        ctk.CTkLabel(
            logo_frame,
            text="Baggage",
            font=ctk.CTkFont(size=13),
            text_color="#7eb3e8",
        ).pack(pady=(0, 14))

        ctk.CTkFrame(self, height=1, fg_color="#1e2d4a", corner_radius=0).pack(fill="x")

        # Nav section label
        self._nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._nav_frame.pack(fill="x", pady=(12, 0))

        ctk.CTkLabel(
            self._nav_frame, text="MENU",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#4a6a9a",
        ).pack(anchor="w", padx=20, pady=(0, 6))

        # Menu items
        for page_id, icon, label in MENU_ITEMS:
            self._add_nav_btn(page_id, icon, label)

        if Session.is_admin():
            ctk.CTkFrame(self, height=1, fg_color="#1e2d4a").pack(fill="x", padx=16, pady=8)
            ctk.CTkLabel(
                self, text="ADMIN",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color="#4a6a9a",
            ).pack(anchor="w", padx=20)
            for page_id, icon, label in MENU_ADMIN:
                self._add_nav_btn(page_id, icon, label)

        # Spacer
        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)

        # Bottom: profil + logout
        ctk.CTkFrame(self, height=1, fg_color="#1e2d4a").pack(fill="x")
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", pady=6)

        # Avatar + nama
        avatar_frame = ctk.CTkFrame(bottom, fg_color="#1e2d4a", corner_radius=20,
                                     width=36, height=36)
        avatar_frame.pack_propagate(False)
        avatar_frame.pack(side="left", padx=(16, 8), pady=8)
        initials = Session.nama()[:1].upper() if Session.nama() else "U"
        ctk.CTkLabel(avatar_frame, text=initials,
                     font=ctk.CTkFont(weight="bold"), text_color="white").place(relx=.5, rely=.5, anchor="center")

        info_col = ctk.CTkFrame(bottom, fg_color="transparent")
        info_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(info_col, text=Session.nama(),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="white", anchor="w").pack(anchor="w")
        role_text = "Administrator" if Session.is_admin() else "Karyawan"
        ctk.CTkLabel(info_col, text=role_text,
                     font=ctk.CTkFont(size=10), text_color="#7eb3e8", anchor="w").pack(anchor="w")

        ctk.CTkButton(
            self, text="  👤  Profil", anchor="w",
            fg_color="transparent", hover_color="#1e2d4a",
            text_color="#c0d0e8", height=34,
            command=lambda: self._navigate("profil"),
        ).pack(fill="x", padx=8, pady=(0, 2))

        ctk.CTkButton(
            self, text="  🚪  Keluar", anchor="w",
            fg_color="transparent", hover_color="#1e2d4a",
            text_color="#e74c3c", height=34,
            command=lambda: self._on_navigate("logout"),
        ).pack(fill="x", padx=8, pady=(0, 10))

    def _add_nav_btn(self, page_id: str, icon: str, label: str) -> None:
        btn = ctk.CTkButton(
            self,
            text=f"  {icon}  {label}",
            anchor="w",
            height=40,
            fg_color="transparent",
            hover_color="#1e2d4a",
            text_color="#c0d0e8",
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            command=lambda p=page_id: self._navigate(p),
        )
        btn.pack(fill="x", padx=8, pady=1)
        self._buttons[page_id] = btn

    def _navigate(self, page_id: str) -> None:
        self.set_active(page_id)
        self._on_navigate(page_id)

    def set_active(self, page_id: str) -> None:
        for pid, btn in self._buttons.items():
            if pid == page_id:
                btn.configure(fg_color="#1e3a6e", text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="#c0d0e8")
        self._active_page = page_id
