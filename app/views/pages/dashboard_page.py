"""Dashboard page — stat cards + tabel kloter aktif + activity feed."""
import customtkinter as ctk

from ...models import database
from ...utils.formatters import rupiah, tanggal_waktu
from ..components.stat_card import StatCard
from ..components.badge import StatusBadge


class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent, on_open_kloter=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_open_kloter = on_open_kloter
        self._build()
        self.refresh()

    def _build(self) -> None:
        # Scrollable container
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(self._scroll, text="Selamat Datang! 👋",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(self._scroll, text="Berikut ringkasan aktivitas hari ini.",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", pady=(2, 16))

        # Stat cards row
        self._cards_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._cards_frame.pack(fill="x", pady=(0, 20))

        # Bottom: kloter aktif + activity feed
        self._bottom = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._bottom.pack(fill="both", expand=True)
        self._bottom.grid_columnconfigure(0, weight=3)
        self._bottom.grid_columnconfigure(1, weight=2)

    def refresh(self) -> None:
        stats = database.get_dashboard_stats()

        # Clear and rebuild cards
        for w in self._cards_frame.winfo_children():
            w.destroy()

        card_data = [
            ("Paket Hari Ini",       str(stats["paket_hari_ini"]),
             "Total paket masuk hari ini", "📦", "#2563a8"),
            ("Kloter Aktif",         str(stats["kloter_aktif"]),
             "Kloter berstatus Terbuka", "🚚", "#27ae60"),
            ("Pendapatan Hari Ini",  rupiah(stats["pendapatan_hari_ini"]),
             "Estimasi omzet hari ini", "💰", "#e67e22"),
            ("Paket Bulan Ini",      str(stats["paket_bulan_ini"]),
             rupiah(stats["pendapatan_bulan_ini"]) + " pendapatan bulan ini", "📊", "#8e44ad"),
        ]

        self._cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        for i, (title, val, sub, icon, accent) in enumerate(card_data):
            card = StatCard(
                self._cards_frame,
                title=title, value=val, subtitle=sub,
                icon=icon, accent=accent,
            )
            card.grid(row=0, column=i, padx=6, sticky="nsew")

        # Clear bottom panels
        for w in self._bottom.winfo_children():
            w.destroy()

        # Kloter Aktif panel
        self._build_kloter_aktif(stats["kloter_aktif_list"])
        # Activity feed
        self._build_activity_feed(stats["recent_paket"])

    def _build_kloter_aktif(self, kloter_list: list) -> None:
        panel = ctk.CTkFrame(self._bottom, corner_radius=10)
        panel.grid(row=0, column=0, padx=(0, 10), pady=4, sticky="nsew")

        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(header, text="Kloter Aktif",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkLabel(header, text=f"{len(kloter_list)} kloter",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(side="right")

        if not kloter_list:
            ctk.CTkLabel(panel, text="Tidak ada kloter aktif.", text_color="gray").pack(pady=20)
            return

        for k in kloter_list:
            row = ctk.CTkFrame(panel, fg_color="transparent",
                               border_width=1, border_color="#2d3748",
                               cursor="hand2")
            row.pack(fill="x", padx=12, pady=3)

            ctk.CTkLabel(row, text=k["nama_kloter"],
                         font=ctk.CTkFont(size=12, weight="bold"),
                         anchor="w").pack(side="left", padx=10, pady=8)

            right = ctk.CTkFrame(row, fg_color="transparent")
            right.pack(side="right", padx=8)
            ctk.CTkLabel(right, text=f"{k['total_paket']} paket",
                         font=ctk.CTkFont(size=11), text_color="gray").pack(side="right")

            if self._on_open_kloter:
                row.bind("<Button-1>", lambda e, kk=k: self._on_open_kloter(dict(kk)))

    def _build_activity_feed(self, paket_list: list) -> None:
        panel = ctk.CTkFrame(self._bottom, corner_radius=10)
        panel.grid(row=0, column=1, pady=4, sticky="nsew")

        ctk.CTkLabel(panel, text="Aktivitas Terbaru",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(
                         anchor="w", padx=16, pady=(14, 8))

        if not paket_list:
            ctk.CTkLabel(panel, text="Belum ada aktivitas.", text_color="gray").pack(pady=20)
            return

        scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent", height=280)
        scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        for p in paket_list:
            item = ctk.CTkFrame(scroll, fg_color="transparent",
                                border_width=1, border_color="#2d3748")
            item.pack(fill="x", pady=2)

            ctk.CTkLabel(item, text="📦", font=ctk.CTkFont(size=14)).pack(
                side="left", padx=(8, 4), pady=6)

            info = ctk.CTkFrame(item, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=4)
            ctk.CTkLabel(info, text=p["nama_penerima"],
                         font=ctk.CTkFont(size=11, weight="bold"),
                         anchor="w").pack(anchor="w")
            ctk.CTkLabel(info,
                         text=f"{p['no_resi']}  •  {p.get('nama_kloter', '')}", 
                         font=ctk.CTkFont(size=10), text_color="gray",
                         anchor="w").pack(anchor="w")

            ctk.CTkLabel(item, text=rupiah(p["total_harga"]),
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#27ae60").pack(side="right", padx=10)
