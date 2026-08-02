"""Kloter page — list, filter, sort, aksi per baris."""
import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional
import customtkinter as ctk

from ...models import database
from ...models.entities import StatusKloter
from ...core.session import Session
from ...services.sheets_sync import sync as gs_sync
from ...utils.formatters import rupiah, tanggal_waktu
from ...utils.validators import ValidationError, require
from ..components.badge import StatusBadge
from ..components.toast import show_toast
from ..components.data_table import DataTable


class KloterPage(ctk.CTkFrame):
    def __init__(self, parent, on_open_kloter: Callable, root_window, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_open_kloter = on_open_kloter
        self._app_window     = root_window
        self._tab_var        = tk.StringVar(value="Semua")
        self._build()
        self.refresh()

    def _build(self) -> None:
        # Header
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(16, 0))
        ctk.CTkLabel(top, text="Manajemen Kloter",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="＋  Kloter Baru", height=36, width=140,
                      command=self._show_buat_dialog).pack(side="right")

        # Tab filter
        tab_bar = ctk.CTkFrame(self, fg_color="transparent")
        tab_bar.pack(fill="x", padx=24, pady=(10, 0))
        self._tab_btns: dict[str, ctk.CTkButton] = {}
        for status in ["Semua", "Terbuka", "Dikirim", "Selesai"]:
            btn = ctk.CTkButton(
                tab_bar, text=status, width=90, height=30,
                fg_color="transparent",
                border_width=1, border_color="#3d4f6a",
                text_color="gray",
                hover_color="#1e2d4a",
                command=lambda s=status: self._switch_tab(s),
            )
            btn.pack(side="left", padx=2)
            self._tab_btns[status] = btn

        # Table container
        self._table_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self._table_wrap.pack(fill="both", expand=True, padx=24, pady=12)

    def _switch_tab(self, status: str) -> None:
        for s, btn in self._tab_btns.items():
            if s == status:
                btn.configure(fg_color="#1e3a6e", text_color="white", border_color="#1e3a6e")
            else:
                btn.configure(fg_color="transparent", text_color="gray", border_color="#3d4f6a")
        self._tab_var.set(status)
        self.refresh()

    def refresh(self) -> None:
        for w in self._table_wrap.winfo_children():
            w.destroy()

        status_filter = self._tab_var.get()
        raw = database.get_all_kloter(None if status_filter == "Semua" else status_filter)

        rows = []
        for k in raw:
            s = database.get_kloter_summary(k["id"])
            rows.append({
                "id":            k["id"],
                "nama_kloter":   k["nama_kloter"],
                "status":        k["status"],
                "total_paket":   str(s["total_paket"]),
                "total_berat":   f"{s['total_berat']:.2f} kg",
                "pendapatan":    rupiah(s["total_pendapatan"]),
                "dibuat_oleh":   k["dibuat_oleh"],
                "tanggal":       tanggal_waktu(k["tanggal_dibuat"]),
                "_raw":          dict(k),
            })

        columns = [
            ("ID Kloter",    "id",           90,  "w"),
            ("Nama Kloter",  "nama_kloter",  180, "w"),
            ("Status",       "status",       90,  "w"),
            ("Paket",        "total_paket",  60,  "center"),
            ("Total Berat",  "total_berat",  110, "e"),
            ("Pendapatan",   "pendapatan",   150, "e"),
            ("Dibuat Oleh",  "dibuat_oleh",  110, "w"),
            ("Tanggal",      "tanggal",      140, "w"),
        ]

        actions = [
            ("Buka",   "#1e3a6e", "#2563a8", lambda r: self._on_open_kloter(r["_raw"])),
            ("Edit",   "#2d4a2d", "#27ae60", lambda r: self._show_edit_dialog(r["_raw"])),
        ]
        if Session.is_admin():
            actions.append(
                ("Hapus", "#4a1a1a", "#c0392b", lambda r: self._hapus(r["_raw"]))
            )

        table = DataTable(
            self._table_wrap,
            columns=columns,
            rows=rows,
            on_row_click=lambda r: self._on_open_kloter(r["_raw"]),
            actions=actions,
            search_keys=["nama_kloter", "id", "status", "dibuat_oleh"],
        )
        table.pack(fill="both", expand=True)

        # Update tab styling (tanpa memanggil _switch_tab untuk hindari recursion)
        current_tab = self._tab_var.get()
        for s, btn in self._tab_btns.items():
            if s == current_tab:
                btn.configure(fg_color="#1e3a6e", text_color="white", border_color="#1e3a6e")
            else:
                btn.configure(fg_color="transparent", text_color="gray", border_color="#3d4f6a")

    # ------------------------------------------------------------------
    def _show_buat_dialog(self) -> None:
        dlg = ctk.CTkToplevel(self._app_window)
        dlg.title("Buat Kloter Baru")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.lift()
        dlg.focus_set()

        # Tengah layar
        w, h = 440, 300
        sw = dlg.winfo_screenwidth()
        sh = dlg.winfo_screenheight()
        dlg.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        ctk.CTkLabel(dlg, text="Buat Kloter Baru",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 14))
        form = ctk.CTkFrame(dlg)
        form.pack(fill="x", padx=30)

        ctk.CTkLabel(form, text="Nama Kloter *", anchor="w").pack(fill="x", padx=16, pady=(14, 2))
        e_nama = ctk.CTkEntry(form, height=36, placeholder_text="Contoh: Kloter Pagi 1")
        e_nama.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(form, text="Catatan (opsional)", anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        e_catatan = ctk.CTkEntry(form, height=36, placeholder_text="Catatan tambahan...")
        e_catatan.pack(fill="x", padx=16, pady=(0, 6))

        lbl_err = ctk.CTkLabel(form, text="", text_color="#e74c3c",
                               font=ctk.CTkFont(size=11))
        lbl_err.pack(fill="x", padx=16)

        def submit():
            lbl_err.configure(text="")
            try:
                nama = require(e_nama.get(), "Nama Kloter")
            except ValidationError as e:
                lbl_err.configure(text=str(e)); return
            catatan = e_catatan.get().strip() or None
            kloter_id = database.insert_kloter(nama, Session.username(), catatan)
            dlg.destroy()
            self.refresh()
            gs_sync.push_kloter(kloter_id)
            show_toast(self._app_window, f"Kloter '{nama}' berhasil dibuat.", "success")

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(fill="x", padx=30, pady=(14, 0))
        ctk.CTkButton(btn_row, text="Buat Kloter", height=40,
                      command=submit).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="Batal", height=40,
                      fg_color="#2d3748", hover_color="#4a5568",
                      command=dlg.destroy).pack(side="left", fill="x", expand=True)
        e_nama.bind("<Return>", lambda e: submit())
        e_nama.focus()

    def _show_edit_dialog(self, kloter: dict) -> None:
        dlg = ctk.CTkToplevel(self._app_window)
        dlg.title("Edit Kloter")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.lift()
        dlg.focus_set()

        # Tengah layar
        w, h = 460, 420
        sw = dlg.winfo_screenwidth()
        sh = dlg.winfo_screenheight()
        dlg.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        ctk.CTkLabel(dlg, text="Edit Kloter",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 14))
        form = ctk.CTkFrame(dlg)
        form.pack(fill="x", padx=30)

        ctk.CTkLabel(form, text="Nama Kloter *", anchor="w").pack(fill="x", padx=16, pady=(14, 2))
        e_nama = ctk.CTkEntry(form, height=36)
        e_nama.insert(0, kloter["nama_kloter"])
        e_nama.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(form, text="Catatan (opsional)", anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        e_catatan = ctk.CTkEntry(form, height=36)
        if kloter.get("catatan"):
            e_catatan.insert(0, kloter["catatan"])
        e_catatan.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(form, text="Status *", anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        statuses = StatusKloter.values()
        var_status = tk.StringVar(value=kloter.get("status", "Terbuka"))
        ctk.CTkComboBox(form, values=statuses, variable=var_status,
                        state="readonly", height=36).pack(fill="x", padx=16, pady=(0, 6))

        lbl_err = ctk.CTkLabel(form, text="", text_color="#e74c3c",
                               font=ctk.CTkFont(size=11))
        lbl_err.pack(fill="x", padx=16)

        def submit():
            lbl_err.configure(text="")
            try:
                nama = require(e_nama.get(), "Nama Kloter")
            except ValidationError as e:
                lbl_err.configure(text=str(e)); return
            catatan   = e_catatan.get().strip() or None
            new_status = var_status.get()
            database.update_kloter(kloter["id"], nama, catatan)
            if new_status != kloter.get("status"):
                database.update_kloter_status(kloter["id"], new_status)
            dlg.destroy()
            self.refresh()
            show_toast(self._app_window, "Kloter berhasil diperbarui.", "success")

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(fill="x", padx=30, pady=(14, 0))
        ctk.CTkButton(btn_row, text="Simpan", height=40,
                      command=submit).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="Batal", height=40,
                      fg_color="#2d3748", hover_color="#4a5568",
                      command=dlg.destroy).pack(side="left", fill="x", expand=True)
        e_nama.focus()

    def _hapus(self, kloter: dict) -> None:
        s = database.get_kloter_summary(kloter["id"])
        if not messagebox.askyesno(
            "Konfirmasi Hapus",
            f"Hapus kloter '{kloter['nama_kloter']}'?\n"
            f"Ini akan menghapus {s['total_paket']} paket.\nTidak dapat dibatalkan!",
            icon="warning"
        ):
            return
        database.delete_kloter(kloter["id"])
        self.refresh()
        show_toast(self._app_window, "Kloter berhasil dihapus.", "info")
