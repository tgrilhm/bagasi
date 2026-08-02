"""Paket page — detail kloter, form popup modal, edit, cetak resi, export."""
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable, Optional
import customtkinter as ctk

from ...models import database
from ...models.entities import KategoriBarang, StatusKloter
from ...core.session import Session
from ...services.sheets_sync import sync as gs_sync
from ...utils.formatters import berat_fmt, rupiah, tanggal_waktu
from ...utils.validators import ValidationError, require, validate_berat, validate_no_hp, validate_tarif
from ...utils.pdf_generator import cetak_laporan_kloter
from ...utils.resi_image_generator import cetak_resi_image
from ...utils.excel_exporter import export_kloter
from ..components.toast import show_toast
from ..components.data_table import DataTable

KATEGORIS   = KategoriBarang.values()
STATUS_NEXT = {"Terbuka": "Dikirim", "Dikirim": "Selesai"}


# ══════════════════════════════════════════════════════════════════════
# Popup Modal — Tambah / Edit Paket
# ══════════════════════════════════════════════════════════════════════
class PaketFormDialog(ctk.CTkToplevel):
    """Modal popup untuk tambah / edit paket."""

    def __init__(self, parent, kloter: dict, on_saved: Callable,
                 edit_paket: Optional[dict] = None):
        super().__init__(parent)
        self._kloter     = kloter
        self._on_saved   = on_saved
        self._edit_paket = edit_paket

        title = "Edit Paket" if edit_paket else "Tambah Paket Baru"
        self.title(title)
        self.resizable(False, False)

        # Ukuran & posisi (tengah layar)
        w, h = 480, 580
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        # Blokir window induk
        self.grab_set()
        self.focus_set()
        self.lift()

        self._build(title)

    def _build(self, title: str) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(scroll, text=title,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(4, 12))

        def lbl(text: str) -> None:
            ctk.CTkLabel(scroll, text=text, anchor="w",
                         font=ctk.CTkFont(size=11, weight="bold")).pack(fill="x", pady=(6, 2))

        def entry(ph: str = "") -> ctk.CTkEntry:
            e = ctk.CTkEntry(scroll, height=36, placeholder_text=ph)
            e.pack(fill="x")
            return e

        def section_lbl(text: str) -> None:
            ctk.CTkLabel(scroll, text=text,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#7eb3e8").pack(anchor="w", pady=(12, 2))

        # ── Pengirim ──────────────────────────────────────────
        section_lbl("Pengirim")
        lbl("Nama Pengirim *")
        self._e_np  = entry("Nama pengirim")
        lbl("No HP Pengirim *")
        self._e_hpp = entry("08xxxxxxxxx")

        # ── Penerima ──────────────────────────────────────────
        section_lbl("Penerima")
        lbl("Nama Penerima *")
        self._e_nr  = entry("Nama penerima")
        lbl("No HP Penerima *")
        self._e_hpr = entry("08xxxxxxxxx")

        # ── Detail Barang ─────────────────────────────────────
        section_lbl("Detail Barang")
        lbl("Kategori *")
        self._var_kat = tk.StringVar(value=KATEGORIS[0])
        ctk.CTkComboBox(scroll, values=KATEGORIS, variable=self._var_kat,
                        state="readonly", height=36).pack(fill="x")

        lbl("Berat (kg) *")
        self._e_berat = entry("Contoh: 2.5")
        lbl("Tarif per kg (Rp) *")
        self._e_tarif = entry("Contoh: 15000")
        lbl("Catatan (opsional)")
        self._e_catatan = entry("Catatan tambahan...")

        # Preview total
        self._lbl_total = ctk.CTkLabel(scroll, text="Total: Rp 0",
                                       font=ctk.CTkFont(size=15, weight="bold"),
                                       text_color="#27ae60")
        self._lbl_total.pack(pady=(10, 4))

        self._e_berat.bind("<KeyRelease>", self._update_preview)
        self._e_tarif.bind("<KeyRelease>", self._update_preview)

        # Error label
        self._lbl_err = ctk.CTkLabel(scroll, text="", text_color="#e74c3c",
                                     font=ctk.CTkFont(size=11), wraplength=420)
        self._lbl_err.pack(pady=(2, 0))

        # Tombol
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", pady=(12, 4))
        ctk.CTkButton(btn_row, text="💾  Simpan", height=40,
                      command=self._submit).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="Batal", height=40,
                      fg_color="#2d3748", hover_color="#4a5568",
                      command=self.destroy).pack(side="left", fill="x", expand=True)

        # Pre-fill jika edit
        if self._edit_paket:
            p = self._edit_paket
            self._e_np.insert(0,  p.get("nama_pengirim", ""))
            self._e_hpp.insert(0, p.get("no_hp_pengirim", ""))
            self._e_nr.insert(0,  p.get("nama_penerima", ""))
            self._e_hpr.insert(0, p.get("no_hp_penerima", ""))
            self._var_kat.set(p.get("kategori", KATEGORIS[0]))
            self._e_berat.insert(0, str(p.get("berat_kg", "")))
            self._e_tarif.insert(0, str(p.get("tarif_per_kg", "")))
            if p.get("catatan"):
                self._e_catatan.insert(0, p["catatan"])
            self._update_preview()

        self._e_np.focus()

    def _update_preview(self, *_) -> None:
        try:
            b = float(self._e_berat.get().replace(",", ".") or 0)
            t = float(self._e_tarif.get().replace(",", ".") or 0)
            self._lbl_total.configure(text=f"Total: {rupiah(b * t)}")
        except ValueError:
            self._lbl_total.configure(text="Total: —")

    def _submit(self) -> None:
        self._lbl_err.configure(text="")
        try:
            nm_p  = require(self._e_np.get(),         "Nama Pengirim")
            hp_p  = validate_no_hp(self._e_hpp.get(), "No HP Pengirim")
            nm_r  = require(self._e_nr.get(),          "Nama Penerima")
            hp_r  = validate_no_hp(self._e_hpr.get(), "No HP Penerima")
            berat = validate_berat(self._e_berat.get())
            tarif = validate_tarif(self._e_tarif.get())
            kat   = self._var_kat.get()
            cat   = self._e_catatan.get().strip() or None
        except ValidationError as ex:
            self._lbl_err.configure(text=str(ex))
            return

        if self._edit_paket:
            database.update_paket(
                self._edit_paket["id"], nm_p, hp_p, nm_r, hp_r,
                kat, berat, tarif, cat)
            gs_sync.push_paket(self._edit_paket["id"])
            msg = "Paket berhasil diperbarui."
        else:
            new_id = database.insert_paket(
                self._kloter["id"], nm_p, hp_p, nm_r, hp_r,
                kat, berat, tarif, Session.username(), cat)
            gs_sync.push_paket(new_id)
            msg = "Paket berhasil ditambahkan."

        self.destroy()
        self._on_saved(msg)


# ══════════════════════════════════════════════════════════════════════
# Popup Selesaikan Paket
# ══════════════════════════════════════════════════════════════════════
class PaketSelesaiDialog(ctk.CTkToplevel):
    """Popup konfirmasi selesaikan paket + info pembayaran."""

    def __init__(self, parent, paket: dict, on_confirmed: Callable):
        super().__init__(parent)
        self._paket        = paket
        self._on_confirmed = on_confirmed

        self.title("Selesaikan Paket")
        self.resizable(False, False)
        w, h = 420, 360
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.grab_set()
        self.focus_set()
        self.lift()
        self._build()

    def _build(self) -> None:
        pad = {"padx": 20, "pady": 6}

        ctk.CTkLabel(self, text="✅  Selesaikan Paket",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(16, 4))

        no_resi   = self._paket.get('no_resi', '')
        penerima  = self._paket.get('nama_penerima', '')
        total_str = rupiah(self._paket.get('total_harga', 0))
        info = f"No Resi  : {no_resi}\nPenerima : {penerima}\nTotal    : {total_str}"
        ctk.CTkLabel(self, text=info, justify="left",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkFrame(self, height=1, fg_color="#2d3748").pack(fill="x", padx=20)

        ctk.CTkLabel(self, text="Info Pembayaran (opsional)",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#7eb3e8").pack(anchor="w", padx=20, pady=(10, 2))

        ctk.CTkLabel(self, text="Penerima Bayar", anchor="w",
                     font=ctk.CTkFont(size=11)).pack(fill="x", padx=20)
        self._e_penerima = ctk.CTkEntry(self, height=34, placeholder_text="Nama penerima pembayaran")
        self._e_penerima.pack(fill="x", padx=20, pady=(2, 6))

        ctk.CTkLabel(self, text="Rekening Tujuan", anchor="w",
                     font=ctk.CTkFont(size=11)).pack(fill="x", padx=20)
        self._e_rekening = ctk.CTkEntry(self, height=34, placeholder_text="No. rekening / nama bank")
        self._e_rekening.pack(fill="x", padx=20, pady=(2, 6))

        # Pre-fill jika sudah ada
        if self._paket.get("penerima_bayar"):
            self._e_penerima.insert(0, self._paket["penerima_bayar"])
        if self._paket.get("rekening_tujuan"):
            self._e_rekening.insert(0, self._paket["rekening_tujuan"])

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(10, 16))
        ctk.CTkButton(
            btn_row, text="✅  Selesaikan", height=40,
            fg_color="#1e5c2d", hover_color="#27ae60",
            command=self._confirm,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(
            btn_row, text="Batal", height=40,
            fg_color="#2d3748", hover_color="#4a5568",
            command=self.destroy,
        ).pack(side="left", fill="x", expand=True)

    def _confirm(self) -> None:
        pb = self._e_penerima.get().strip() or None
        rk = self._e_rekening.get().strip() or None
        self.destroy()
        self._on_confirmed(pb, rk)


# ══════════════════════════════════════════════════════════════════════
# PaketPage
# ══════════════════════════════════════════════════════════════════════
class PaketPage(ctk.CTkFrame):
    def __init__(self, parent, kloter: dict, on_back: Callable, root_window, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._kloter  = kloter
        self._on_back = on_back
        self._win     = root_window
        self._build()
        self.refresh()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        # ── Top bar ────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(14, 0))

        ctk.CTkButton(top, text="← Kembali", width=100, height=32,
                      fg_color="#2d3748", hover_color="#4a5568",
                      command=self._on_back).pack(side="left")

        self._lbl_nama = ctk.CTkLabel(top, text="",
                                       font=ctk.CTkFont(size=18, weight="bold"))
        self._lbl_nama.pack(side="left", padx=12)

        self._badge = ctk.CTkLabel(top, text="",
                                    font=ctk.CTkFont(size=11, weight="bold"),
                                    corner_radius=10)
        self._badge.pack(side="left")

        # Tombol kanan atas
        btn_row = ctk.CTkFrame(top, fg_color="transparent")
        btn_row.pack(side="right")
        ctk.CTkButton(btn_row, text="📊 Export Excel", width=130, height=32,
                      fg_color="#1e5c2d", hover_color="#27ae60",
                      command=self._export_excel).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="🖨 Cetak Laporan", width=130, height=32,
                      fg_color="#1a3a5c", hover_color="#2563a8",
                      command=self._cetak_laporan).pack(side="left", padx=2)
        self._btn_status = ctk.CTkButton(btn_row, text="", width=120, height=32,
                                          fg_color="#5c3a1a", hover_color="#e67e22",
                                          command=self._ubah_status)
        self._btn_status.pack(side="left", padx=2)

        # ── Summary bar ────────────────────────────────────────
        self._summary_bar = ctk.CTkFrame(self, corner_radius=8)
        self._summary_bar.pack(fill="x", padx=24, pady=(10, 0))
        self._lbl_paket = self._sum_item("0",    "Total Paket")
        self._lbl_berat = self._sum_item("0 kg", "Total Berat")
        self._lbl_pend  = self._sum_item("Rp 0", "Total Pendapatan")

        # ── Timeline ───────────────────────────────────────────
        self._timeline = ctk.CTkFrame(self, fg_color="transparent")
        self._timeline.pack(fill="x", padx=24, pady=(8, 0))

        # ── Action bar ─────────────────────────────────────────
        act_bar = ctk.CTkFrame(self, fg_color="transparent")
        act_bar.pack(fill="x", padx=24, pady=(8, 0))
        self._btn_tambah = ctk.CTkButton(
            act_bar, text="＋  Tambah Paket", height=36, width=150,
            command=self._open_add_popup)
        self._btn_tambah.pack(side="left")

        # ── Tabel ─────────────────────────────────────────────
        self._table_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self._table_wrap.pack(fill="both", expand=True, padx=24, pady=10)

    def _sum_item(self, value: str, label: str) -> ctk.CTkLabel:
        box = ctk.CTkFrame(self._summary_bar, fg_color="transparent")
        box.pack(side="left", padx=20, pady=8)
        lbl = ctk.CTkLabel(box, text=value, font=ctk.CTkFont(size=18, weight="bold"))
        lbl.pack()
        ctk.CTkLabel(box, text=label, font=ctk.CTkFont(size=10), text_color="gray").pack()
        return lbl

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        row = database.get_kloter(self._kloter["id"])
        if row:
            self._kloter = dict(row)

        status = self._kloter.get("status", "Terbuka")
        sc = {"Terbuka": ("#27ae60", "#d5f5e3"),
              "Dikirim": ("#e67e22", "#fef5e7"),
              "Selesai": ("#7f8c8d", "#f2f3f4")}
        fg, bg = sc.get(status, ("#555", "#eee"))
        self._lbl_nama.configure(text=f"Kloter: {self._kloter['nama_kloter']}")
        self._badge.configure(text=f"  {status}  ", text_color=fg, fg_color=bg)

        for w in self._timeline.winfo_children():
            w.destroy()
        self._build_timeline(status)

        next_s = STATUS_NEXT.get(status)
        if next_s:
            self._btn_status.configure(text=f"→ {next_s}", state="normal")
        else:
            self._btn_status.configure(text="✓ Selesai", state="disabled")

        self._btn_tambah.configure(state="normal" if status == "Terbuka" else "disabled")

        s = database.get_kloter_summary(self._kloter["id"])
        self._lbl_paket.configure(text=str(s["total_paket"]))
        self._lbl_berat.configure(text=f"{s['total_berat']:.2f} kg")
        self._lbl_pend.configure(text=rupiah(s["total_pendapatan"]))

        self._rebuild_table(status)

    def _build_timeline(self, current: str) -> None:
        statuses = ["Terbuka", "Dikirim", "Selesai"]
        icons    = ["📋", "🚚", "✅"]
        idx = statuses.index(current) if current in statuses else 0
        for i, (s, icon) in enumerate(zip(statuses, icons)):
            col = "#27ae60" if i <= idx else "#3d4f6a"
            ctk.CTkLabel(self._timeline,
                         text=f"{icon} {s}",
                         font=ctk.CTkFont(size=11,
                             weight="bold" if i == idx else "normal"),
                         text_color=col).pack(side="left")
            if i < len(statuses) - 1:
                ctk.CTkLabel(self._timeline, text="  ──────  ",
                             text_color="#3d4f6a").pack(side="left")

    def _rebuild_table(self, status: str) -> None:
        for w in self._table_wrap.winfo_children():
            w.destroy()

        paket_list = database.get_paket_by_kloter(self._kloter["id"])
        rows = []
        for p in paket_list:
            r = dict(p)
            r["_berat_fmt"] = berat_fmt(r["berat_kg"])
            r["_tarif_fmt"] = rupiah(r["tarif_per_kg"])
            r["_total_fmt"] = rupiah(r["total_harga"])
            r["_tgl_fmt"]   = tanggal_waktu(r["tanggal_dibuat"])
            rows.append(r)

        is_open = status == "Terbuka"
        actions = []
        if is_open:
            actions.append(("✏ Edit",   "#1a3a5c", "#2563a8", self._open_edit_popup))
            actions.append(("🗑 Hapus",  "#4a1a1a", "#c0392b", self._hapus_paket))
        actions.append(("✅ Selesai", "#1a4a2a", "#27ae60", self._selesaikan_paket))
        actions.append(("🖨 Resi",    "#1e3a1e", "#27ae60", self._cetak_resi_paket))

        columns = [
            ("No Resi",       "no_resi",        120, "w"),
            ("Pengirim",      "nama_pengirim",   120, "w"),
            ("HP Pengirim",   "no_hp_pengirim",  105, "w"),
            ("Penerima",      "nama_penerima",   120, "w"),
            ("HP Penerima",   "no_hp_penerima",  105, "w"),
            ("Kategori",      "kategori",         85, "w"),
            ("Berat",         "_berat_fmt",       65, "center"),
            ("Tarif/kg",      "_tarif_fmt",       95, "e"),
            ("Total",         "_total_fmt",      110, "e"),
        ]

        table = DataTable(
            self._table_wrap,
            columns=columns, rows=rows,
            actions=actions,
            search_keys=["no_resi", "nama_pengirim", "nama_penerima", "kategori"],
        )
        table.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Popup handlers
    # ------------------------------------------------------------------

    def _open_add_popup(self) -> None:
        PaketFormDialog(
            self._win,
            kloter=self._kloter,
            on_saved=self._on_form_saved,
            edit_paket=None,
        )

    def _open_edit_popup(self, paket: dict) -> None:
        row = database.get_paket_by_resi(paket.get("no_resi", ""))
        edit_data = dict(row) if row else paket
        PaketFormDialog(
            self._win,
            kloter=self._kloter,
            on_saved=self._on_form_saved,
            edit_paket=edit_data,
        )

    def _on_form_saved(self, msg: str) -> None:
        self.refresh()
        show_toast(self._win, msg, "success")

    # ------------------------------------------------------------------
    # Aksi baris
    # ------------------------------------------------------------------

    def _selesaikan_paket(self, paket: dict) -> None:
        row = database.get_paket_by_resi(paket.get("no_resi", ""))
        if not row:
            return
        r = dict(row)
        if r.get("status") == "Selesai":
            show_toast(self._win, f"Paket {r['no_resi']} sudah selesai.", "info")
            return

        def _on_confirmed(penerima_bayar, rekening_tujuan):
            database.update_paket_status(
                r["id"], "Selesai", penerima_bayar, rekening_tujuan)
            gs_sync.push_paket(r["id"])
            self.refresh()
            show_toast(self._win, f"Paket {r['no_resi']} diselesaikan.", "success")

        PaketSelesaiDialog(self._win, r, _on_confirmed)

    def _hapus_paket(self, paket: dict) -> None:
        row = database.get_paket_by_resi(paket.get("no_resi", ""))
        if not row:
            return
        if not messagebox.askyesno("Konfirmasi Hapus",
                                   f"Hapus paket {row['no_resi']}?", icon="warning"):
            return
        database.delete_paket(row["id"])
        self.refresh()
        show_toast(self._win, "Paket dihapus.", "info")

    def _cetak_resi_paket(self, paket: dict) -> None:
        row = database.get_paket_by_resi(paket.get("no_resi", ""))
        if not row:
            return
        out_dir = Path(__file__).parent.parent.parent.parent / "exports" / "resi"
        out_dir.mkdir(parents=True, exist_ok=True)
        ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = out_dir / f"Resi_{row['no_resi']}_{ts}.jpg"
        try:
            result = cetak_resi_image(dict(row), self._kloter, out)
            import os; os.startfile(str(result))
            show_toast(self._win, f"Resi {row['no_resi']} berhasil dibuat.", "success")
        except Exception as e:
            messagebox.showerror("Gagal Cetak Resi", str(e))

    # ------------------------------------------------------------------
    # Kloter aksi
    # ------------------------------------------------------------------

    def _ubah_status(self) -> None:
        current = self._kloter.get("status", "Terbuka")
        next_s  = STATUS_NEXT.get(current)
        if not next_s:
            return
        if not messagebox.askyesno(
            "Konfirmasi",
            f"Ubah status kloter ke '{next_s}'?\nTidak dapat dibatalkan."
        ):
            return
        database.update_kloter_status(self._kloter["id"], next_s)
        self.refresh()
        show_toast(self._win, f"Status kloter diubah ke '{next_s}'.", "info")

    def _cetak_laporan(self) -> None:
        out_dir = filedialog.askdirectory(title="Pilih folder simpan laporan PDF")
        if not out_dir:
            return
        paket_list = [dict(p) for p in database.get_paket_by_kloter(self._kloter["id"])]
        summary    = database.get_kloter_summary(self._kloter["id"])
        ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_"
                            for c in self._kloter["nama_kloter"])
        out = Path(out_dir) / f"Laporan_{safe_name}_{ts}.pdf"
        try:
            cetak_laporan_kloter(self._kloter, paket_list, summary, out)
            import os; os.startfile(str(out))
            show_toast(self._win, "Laporan PDF berhasil dibuat.", "success")
        except Exception as e:
            messagebox.showerror("Gagal Cetak Laporan", str(e))

    def _export_excel(self) -> None:
        out_dir = filedialog.askdirectory(title="Pilih folder simpan Excel")
        if not out_dir:
            return
        paket_list = [dict(p) for p in database.get_paket_by_kloter(self._kloter["id"])]
        summary    = database.get_kloter_summary(self._kloter["id"])
        ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_"
                            for c in self._kloter["nama_kloter"])
        out = Path(out_dir) / f"Kloter_{safe_name}_{ts}.xlsx"
        try:
            export_kloter(self._kloter, paket_list, summary, out)
            import os; os.startfile(str(out))
            show_toast(self._win, "Excel berhasil dibuat.", "success")
        except Exception as e:
            messagebox.showerror("Gagal Export Excel", str(e))
