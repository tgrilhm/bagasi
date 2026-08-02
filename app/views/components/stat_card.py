"""Stat card untuk dashboard."""
import customtkinter as ctk


class StatCard(ctk.CTkFrame):
    def __init__(self, parent, title: str, value: str, subtitle: str = "",
                 icon: str = "", accent: str = "#2563a8", **kwargs):
        super().__init__(parent, corner_radius=10, **kwargs)

        # Icon
        if icon:
            ctk.CTkLabel(self, text=icon, font=ctk.CTkFont(size=24)).pack(
                anchor="w", padx=16, pady=(14, 0))

        # Value
        self._val_label = ctk.CTkLabel(
            self, text=value,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=accent,
        )
        self._val_label.pack(anchor="w", padx=16, pady=(4, 0))

        # Title
        ctk.CTkLabel(
            self, text=title,
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(anchor="w", padx=16, pady=(0, 2))

        # Subtitle
        if subtitle:
            ctk.CTkLabel(
                self, text=subtitle,
                font=ctk.CTkFont(size=10),
                text_color="#888",
            ).pack(anchor="w", padx=16, pady=(0, 12))
        else:
            ctk.CTkFrame(self, height=12, fg_color="transparent").pack()

        # Accent bar di bawah
        ctk.CTkFrame(self, height=3, fg_color=accent, corner_radius=0).pack(
            fill="x", side="bottom"
        )

    def update_value(self, value: str) -> None:
        self._val_label.configure(text=value)
