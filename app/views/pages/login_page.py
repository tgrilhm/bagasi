"""Login page dengan tampilan enterprise."""
import tkinter as tk
from typing import Callable
import customtkinter as ctk

from ...models import database
from ...core.session import Session
from ...utils.validators import ValidationError, require


class LoginPage(ctk.CTkFrame):
    def __init__(self, parent, on_success: Callable, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_success  = on_success
        self._show_pw     = False
        self._build()

    def _build(self) -> None:
        # Split layout: kiri dekorasi, kanan form
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # Panel kiri — branding
        left = ctk.CTkFrame(self, fg_color="#0f1729", corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)

        ctk.CTkFrame(left, fg_color="transparent").pack(expand=True)
        ctk.CTkLabel(left, text="🧳",
                     font=ctk.CTkFont(size=64)).pack()
        ctk.CTkLabel(left, text="Amanah Baggage",
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color="white").pack(pady=(8, 4))
        ctk.CTkLabel(left, text="Sistem Manajemen Pengiriman Bagasi",
                     font=ctk.CTkFont(size=13),
                     text_color="#7eb3e8").pack()
        ctk.CTkFrame(left, fg_color="transparent").pack(expand=True)

        ctk.CTkLabel(left, text="© 2024 Amanah Baggage",
                     font=ctk.CTkFont(size=10),
                     text_color="#2a4a6a").pack(pady=16)

        # Panel kanan — form
        right = ctk.CTkFrame(self, corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")

        form_wrap = ctk.CTkFrame(right, fg_color="transparent")
        form_wrap.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8)

        ctk.CTkLabel(form_wrap, text="Masuk ke Akun",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(form_wrap, text="Masukkan username dan password Anda",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", pady=(4, 24))

        # Username
        ctk.CTkLabel(form_wrap, text="Username", anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(fill="x")
        self._e_user = ctk.CTkEntry(form_wrap, height=42, placeholder_text="Masukkan username")
        self._e_user.pack(fill="x", pady=(4, 12))

        # Password
        ctk.CTkLabel(form_wrap, text="Password", anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(fill="x")
        pw_row = ctk.CTkFrame(form_wrap, fg_color="transparent")
        pw_row.pack(fill="x", pady=(4, 4))
        self._e_pw = ctk.CTkEntry(pw_row, height=42,
                                   placeholder_text="Masukkan password", show="*")
        self._e_pw.pack(side="left", fill="x", expand=True)
        self._btn_eye = ctk.CTkButton(
            pw_row, text="👁", width=42, height=42,
            fg_color="transparent", hover_color="#2d2d2d",
            command=self._toggle_pw)
        self._btn_eye.pack(side="left", padx=(4, 0))

        # Error
        self._lbl_err = ctk.CTkLabel(
            form_wrap, text="", text_color="#e74c3c",
            font=ctk.CTkFont(size=11), wraplength=300, anchor="w")
        self._lbl_err.pack(fill="x", pady=(4, 0))

        # Submit
        ctk.CTkButton(
            form_wrap, text="Masuk  →", height=44,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._submit,
        ).pack(fill="x", pady=(16, 0))

        ctk.CTkLabel(form_wrap, text="Default admin: admin / admin123",
                     font=ctk.CTkFont(size=10), text_color="gray").pack(pady=(14, 0))

        self._e_user.bind("<Return>", lambda e: self._e_pw.focus())
        self._e_pw.bind("<Return>",   lambda e: self._submit())
        self._e_user.focus()

    def _toggle_pw(self) -> None:
        self._show_pw = not self._show_pw
        self._e_pw.configure(show="" if self._show_pw else "*")

    def _submit(self) -> None:
        self._lbl_err.configure(text="")
        try:
            username = require(self._e_user.get(), "Username")
            password = require(self._e_pw.get(), "Password")
        except ValidationError as e:
            self._lbl_err.configure(text=str(e))
            return

        row = database.verify_login(username, password)
        if row is None:
            self._lbl_err.configure(text="Username atau password salah.")
            self._e_pw.delete(0, "end")
            self._shake()
            return

        Session.login(dict(row))
        self._on_success()

    def _shake(self) -> None:
        """Feedback visual saat login gagal."""
        self.bell()  # System beep
        # Flash effect pada password entry
        orig_fg = self._e_pw.cget("fg_color")
        self._e_pw.configure(fg_color="#8b0000")  # Red flash
        self.after(100, lambda: self._e_pw.configure(fg_color=orig_fg))
