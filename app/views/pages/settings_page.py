"""Halaman Pengaturan — setup Google Sheets via Apps Script Web App."""
import tkinter as tk
import threading
import webbrowser
import customtkinter as ctk

from ...services.sheets_sync import sync


class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, root_window=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._app_window = root_window
        self._build()
        self._refresh_status()

    def _build(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=16)

        # Judul
        ctk.CTkLabel(scroll, text="⚙️  Pengaturan Integrasi Google Sheets",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll,
                     text="Hubungkan aplikasi ke Google Spreadsheet menggunakan Apps Script (tanpa OAuth).",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", pady=(0, 20))

        # ── Status card ──────────────────────────────────────────
        status_frame = ctk.CTkFrame(scroll, corner_radius=10)
        status_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(status_frame, text="Status Koneksi",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        self._lbl_status = ctk.CTkLabel(status_frame, text="⏳ Memeriksa...",
                                         font=ctk.CTkFont(size=13))
        self._lbl_status.pack(anchor="w", padx=16, pady=(0, 12))

        # ── Panduan Setup ──────────────────────────────────────────
        guide = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("#e8f4fd", "#1a2a3a"))
        guide.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(guide, text="📋  Panduan Setup Google Apps Script (Sekali saja)",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(14, 8))

        steps = [
            "1.  Buka Google Spreadsheet Anda",
            "2.  Klik menu  Extensions → Apps Script",
            "3.  Hapus kode default, paste kode dari file  google_apps_script.js",
            "4.  Klik Save (ikon floppy disk)",
            "5.  Klik  Deploy → New deployment",
            '6.  Pilih type: Web app → Execute as: Me → Who has access: Anyone',
            "7.  Klik  Deploy → copy URL yang muncul",
            "8.  Paste URL di kolom 'Web App URL' di bawah → klik Hubungkan",
        ]
        for step in steps:
            row = ctk.CTkFrame(guide, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(row, text=step, anchor="w",
                         font=ctk.CTkFont(size=11), wraplength=620).pack(side="left", fill="x")

        ctk.CTkButton(
            guide, text="📂  Buka File Kode Apps Script",
            fg_color="#2d3748", hover_color="#4a5568",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._open_script_file,
        ).pack(anchor="w", padx=16, pady=(10, 4))

        ctk.CTkButton(
            guide, text="📊  Buka Google Spreadsheet",
            fg_color="#27ae60", hover_color="#229954",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: webbrowser.open("https://sheets.google.com"),
        ).pack(anchor="w", padx=16, pady=(0, 14))

        # ── Web App URL ──────────────────────────────────────────────
        url_frame = ctk.CTkFrame(scroll, corner_radius=10)
        url_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(url_frame, text="🔗  Web App URL",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(
            url_frame,
            text="URL dari Deploy → New deployment di Google Apps Script",
            font=ctk.CTkFont(size=10), text_color="gray",
        ).pack(anchor="w", padx=16)

        self._entry_url = ctk.CTkEntry(
            url_frame,
            placeholder_text="https://script.google.com/macros/s/AKfy.../exec",
            height=38, font=ctk.CTkFont(size=11),
        )
        self._entry_url.pack(fill="x", padx=16, pady=(8, 4))

        # Isi URL yang sudah tersimpan
        saved_url = sync.get_webapp_url()
        if saved_url:
            self._entry_url.insert(0, saved_url)

        self._lbl_conn_err = ctk.CTkLabel(url_frame, text="", text_color="#e74c3c",
                                           font=ctk.CTkFont(size=11), wraplength=620)
        self._lbl_conn_err.pack(anchor="w", padx=16)

        ctk.CTkButton(
            url_frame, text="🔗  Hubungkan ke Google Sheets", height=42,
            fg_color="#27ae60", hover_color="#229954",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._do_connect,
        ).pack(anchor="w", padx=16, pady=(8, 14))

        # ── Disconnect ───────────────────────────────────────────────
        btm = ctk.CTkFrame(scroll, fg_color="transparent")
        btm.pack(fill="x")
        ctk.CTkButton(
            btm, text="🔌  Putuskan Koneksi", height=36,
            fg_color="#4a1a1a", hover_color="#c0392b",
            font=ctk.CTkFont(size=11),
            command=self._disconnect,
        ).pack(side="left")

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def _open_script_file(self) -> None:
        import subprocess
        import os
        from pathlib import Path
        script = Path(__file__).parent.parent.parent.parent / "google_apps_script.js"
        if script.exists():
            os.startfile(str(script))
        else:
            self._lbl_conn_err.configure(
                text="File google_apps_script.js tidak ditemukan di folder BAGASI")

    def _do_connect(self) -> None:
        url = self._entry_url.get().strip()
        if not url:
            self._lbl_conn_err.configure(text="⚠ URL tidak boleh kosong.")
            return
        if not url.startswith("https://script.google.com"):
            self._lbl_conn_err.configure(
                text="⚠ URL harus dimulai dengan https://script.google.com")
            return

        self._lbl_conn_err.configure(text="")
        self._lbl_status.configure(text="🔄 Menghubungkan...")

        def _thread():
            ok, msg = sync.connect(url)
            self.after(0, lambda: self._on_connect_done(ok, msg))

        threading.Thread(target=_thread, daemon=True).start()

    def _on_connect_done(self, ok: bool, msg: str) -> None:
        if ok:
            self._lbl_conn_err.configure(text="")
        else:
            self._lbl_conn_err.configure(text=f"❌ {msg}")
        self._refresh_status()

    def _disconnect(self) -> None:
        sync.disconnect()
        self._refresh_status()

    def _refresh_status(self) -> None:
        s = sync.get_status()
        icons = {
            "idle":         ("🟢", "Terhubung & siap sinkronisasi",          "#27ae60"),
            "syncing":      ("🔄", "Sedang menyinkronkan data...",            "#f39c12"),
            "error":        ("🔴", "Gagal — periksa URL atau koneksi internet", "#e74c3c"),
            "disconnected": ("⚪", "Belum terhubung",                         "gray"),
        }
        icon, text, color = icons.get(s, icons["disconnected"])
        self._lbl_status.configure(text=f"{icon}  {text}", text_color=color)
