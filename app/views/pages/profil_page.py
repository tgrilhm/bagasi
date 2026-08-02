"""Profil page — ubah nama dan password sendiri."""
import customtkinter as ctk

from ...models import database
from ...core.session import Session
from ...utils.formatters import tanggal_waktu
from ...utils.validators import ValidationError, require, validate_password
from ..components.toast import show_toast


class ProfilPage(ctk.CTkFrame):
    def __init__(self, parent, root_window, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._app_window = root_window
        self._build()

    def _build(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=40, pady=20)

        ctk.CTkLabel(scroll, text="Profil Saya",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(scroll, text="Kelola informasi akun Anda.",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", pady=(2, 20))

        # Avatar card
        card = ctk.CTkFrame(scroll, corner_radius=12)
        card.pack(fill="x", pady=(0, 20))

        avatar = ctk.CTkFrame(card, width=64, height=64, corner_radius=32,
                               fg_color="#1e3a6e")
        avatar.pack_propagate(False)
        avatar.pack(side="left", padx=20, pady=16)
        ctk.CTkLabel(avatar, text=Session.nama()[:1].upper(),
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color="white").place(relx=.5, rely=.5, anchor="center")

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", pady=16)
        ctk.CTkLabel(info, text=Session.nama(),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(info, text=f"@{Session.username()}",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")
        role_color = "#f39c12" if Session.is_admin() else "#2980b9"
        role_text  = "Administrator" if Session.is_admin() else "Karyawan"
        ctk.CTkLabel(info, text=role_text, font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=role_color).pack(anchor="w", pady=(4, 0))

        # Info detail
        k = database.get_karyawan(Session.username())
        if k:
            ctk.CTkLabel(info,
                         text=f"Bergabung: {tanggal_waktu(k['tanggal_dibuat'])}",
                         font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", pady=(2, 0))

        # Form ubah nama
        self._build_form_nama(scroll)
        # Form ubah password
        self._build_form_password(scroll)

    def _section(self, parent, title: str, subtitle: str) -> ctk.CTkFrame:
        ctk.CTkLabel(parent, text=title,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(16, 2))
        ctk.CTkLabel(parent, text=subtitle,
                     font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", pady=(0, 8))
        frame = ctk.CTkFrame(parent, corner_radius=10)
        frame.pack(fill="x", pady=(0, 4))
        return frame

    def _build_form_nama(self, parent) -> None:
        card = self._section(parent, "Ubah Nama", "Perbarui nama tampilan Anda.")
        f = ctk.CTkFrame(card, fg_color="transparent"); f.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(f, text="Nama Lengkap Baru *", anchor="w",
                     font=ctk.CTkFont(size=11, weight="bold")).pack(fill="x", pady=(0, 4))
        e_nama = ctk.CTkEntry(f, height=38, placeholder_text="Nama lengkap baru")
        e_nama.insert(0, Session.nama())
        e_nama.pack(fill="x")

        lbl_err = ctk.CTkLabel(f, text="", text_color="#e74c3c", font=ctk.CTkFont(size=11))
        lbl_err.pack(anchor="w", pady=(4, 0))

        def save_nama():
            lbl_err.configure(text="")
            try:
                nama = require(e_nama.get(), "Nama Lengkap")
            except ValidationError as ex:
                lbl_err.configure(text=str(ex)); return
            database.update_karyawan(Session.username(), nama, Session.is_admin())
            # Update session
            u = database.get_karyawan(Session.username())
            if u:
                Session.login(dict(u))
            show_toast(self._app_window, "Nama berhasil diperbarui.", "success")

        ctk.CTkButton(f, text="Simpan Nama", height=36, width=140, command=save_nama).pack(
            anchor="w", pady=(10, 0))

    def _build_form_password(self, parent) -> None:
        card = self._section(parent, "Ubah Password", "Pastikan gunakan password yang kuat.")
        f = ctk.CTkFrame(card, fg_color="transparent"); f.pack(fill="x", padx=20, pady=16)

        def pw_row(label, ph):
            ctk.CTkLabel(f, text=label, anchor="w",
                         font=ctk.CTkFont(size=11, weight="bold")).pack(fill="x", pady=(6, 2))
            e = ctk.CTkEntry(f, height=38, placeholder_text=ph, show="*")
            e.pack(fill="x"); return e

        e_old  = pw_row("Password Lama *", "Masukkan password saat ini")
        e_new  = pw_row("Password Baru *", "Min. 6 karakter")
        e_conf = pw_row("Konfirmasi Password Baru *", "Ulangi password baru")

        lbl_err = ctk.CTkLabel(f, text="", text_color="#e74c3c", font=ctk.CTkFont(size=11))
        lbl_err.pack(anchor="w", pady=(4, 0))

        def save_pw():
            lbl_err.configure(text="")
            try:
                old  = require(e_old.get(), "Password Lama")
                new  = validate_password(e_new.get())
                conf = require(e_conf.get(), "Konfirmasi Password")
            except ValidationError as ex:
                lbl_err.configure(text=str(ex)); return

            if new != conf:
                lbl_err.configure(text="Password baru dan konfirmasi tidak cocok."); return

            # Verifikasi password lama
            if not database.verify_login(Session.username(), old):
                lbl_err.configure(text="Password lama salah."); return

            database.change_password(Session.username(), new)
            e_old.delete(0, "end"); e_new.delete(0, "end"); e_conf.delete(0, "end")
            show_toast(self._app_window, "Password berhasil diubah.", "success")

        ctk.CTkButton(f, text="Simpan Password", height=36, width=160, command=save_pw).pack(
            anchor="w", pady=(10, 0))
