"""Karyawan page — manajemen user (admin only)."""
import tkinter as tk
from tkinter import messagebox
from typing import Optional
import customtkinter as ctk

from ...models import database
from ...core.session import Session
from ...utils.formatters import tanggal_waktu
from ...utils.validators import ValidationError, require, validate_password, validate_username
from ..components.data_table import DataTable
from ..components.toast import show_toast


class KaryawanPage(ctk.CTkFrame):
    def __init__(self, parent, root_window, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._app_window = root_window
        self._build()
        self.refresh()

    def _build(self) -> None:
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(16, 0))
        ctk.CTkLabel(top, text="Manajemen Karyawan",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="＋  Tambah Karyawan", height=36, width=160,
                      command=self._show_tambah).pack(side="right")

        self._table_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self._table_wrap.pack(fill="both", expand=True, padx=24, pady=12)

    def refresh(self) -> None:
        for w in self._table_wrap.winfo_children():
            w.destroy()

        rows_raw = database.get_all_karyawan()
        rows = []
        for k in rows_raw:
            rows.append({
                "id":           k["username"],
                "username":     k["username"],
                "nama_lengkap": k["nama_lengkap"],
                "role":         "Admin" if k["is_admin"] else "Karyawan",
                "status":       "Aktif" if k["is_active"] else "Nonaktif",
                "dibuat":       tanggal_waktu(k["tanggal_dibuat"]),
                "_raw":         dict(k),
            })

        is_self   = lambda r: r["username"] == Session.username()
        is_master = lambda r: r["username"] == "admin"

        actions = [
            ("Edit",    "#1a3a5c", "#2563a8",  lambda r: self._show_edit(r["_raw"])),
            ("Nonaktif/Aktif", "#4a3a1a", "#e67e22", lambda r: self._toggle_aktif(r["_raw"])),
        ]

        columns = [
            ("Username",     "username",    120, "w"),
            ("Nama Lengkap", "nama_lengkap",200, "w"),
            ("Role",         "role",         90, "w"),
            ("Status",       "status",       90, "w"),
            ("Tgl Dibuat",   "dibuat",      150, "w"),
        ]

        table = DataTable(
            self._table_wrap,
            columns=columns, rows=rows,
            actions=actions,
            search_keys=["username", "nama_lengkap", "role"],
        )
        table.pack(fill="both", expand=True)

    def _show_tambah(self) -> None:
        self._user_form_dialog(None)

    def _show_edit(self, k: dict) -> None:
        self._user_form_dialog(k)

    def _user_form_dialog(self, k: Optional[dict]) -> None:
        is_edit = k is not None
        dlg = ctk.CTkToplevel(self)
        dlg.title("Edit Karyawan" if is_edit else "Tambah Karyawan")
        dlg.geometry("420x420"); dlg.grab_set(); dlg.resizable(False, False)

        ctk.CTkLabel(dlg, text="Edit Karyawan" if is_edit else "Tambah Karyawan",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 12))

        form = ctk.CTkFrame(dlg); form.pack(fill="x", padx=30)

        def row(label, ph, show=""):
            ctk.CTkLabel(form, text=label, anchor="w").pack(fill="x", padx=16, pady=(10, 2))
            e = ctk.CTkEntry(form, placeholder_text=ph, show=show, height=36)
            e.pack(fill="x", padx=16); return e

        e_user = row("Username *", "contoh: andi123")
        e_nama = row("Nama Lengkap *", "Nama lengkap karyawan")
        e_pw   = row("Password *" if not is_edit else "Password Baru (kosongkan jika tidak diubah)",
                     "Min. 6 karakter", show="*")

        var_admin = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(form, text="Berikan akses Admin", variable=var_admin).pack(
            anchor="w", padx=16, pady=(10, 4))

        if is_edit:
            e_user.insert(0, k["username"]); e_user.configure(state="disabled")
            e_nama.insert(0, k["nama_lengkap"])
            var_admin.set(bool(k["is_admin"]))

        lbl_err = ctk.CTkLabel(form, text="", text_color="#e74c3c",
                               font=ctk.CTkFont(size=11))
        lbl_err.pack(fill="x", padx=16)

        def submit():
            lbl_err.configure(text="")
            try:
                if not is_edit:
                    username = validate_username(e_user.get())
                nama = require(e_nama.get(), "Nama Lengkap")
                pw   = e_pw.get().strip()
                if not is_edit or pw:
                    pw = validate_password(pw)
            except ValidationError as ex:
                lbl_err.configure(text=str(ex)); return

            if not is_edit:
                if database.get_karyawan(username):
                    lbl_err.configure(text="Username sudah digunakan."); return
                database.insert_karyawan(username, nama, pw, var_admin.get(), must_change_password=False)
                show_toast(self._app_window, f"Karyawan '{username}' ditambahkan.", "success")
            else:
                database.update_karyawan(k["username"], nama, var_admin.get())
                if pw:
                    database.change_password(k["username"], pw)
                show_toast(self._app_window, "Data karyawan diperbarui.", "success")

            dlg.destroy(); self.refresh()

        ctk.CTkButton(dlg, text="Simpan", height=38, command=submit).pack(
            fill="x", padx=30, pady=(14, 0))
        e_user.focus() if not is_edit else e_nama.focus()

    def _toggle_aktif(self, k: dict) -> None:
        if k["username"] == Session.username():
            show_toast(self._app_window, "Tidak bisa menonaktifkan akun sendiri.", "warning"); return
        if k["username"] == "admin":
            show_toast(self._app_window, "Akun admin utama tidak dapat dinonaktifkan.", "warning"); return
        new_active = not bool(k["is_active"])
        label = "mengaktifkan" if new_active else "menonaktifkan"
        if messagebox.askyesno("Konfirmasi", f"Yakin ingin {label} akun '{k['username']}'?"):
            database.set_karyawan_active(k["username"], new_active)
            self.refresh()
            show_toast(self._app_window, f"Akun '{k['username']}' berhasil di{label[2:]}.", "success")
