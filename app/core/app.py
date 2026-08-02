"""Root window — shell enterprise: sidebar + topbar + content area."""
import threading
import customtkinter as ctk

from ..models.database import init_db
from ..core.session import Session
from ..services.sheets_sync import sync as gs_sync
from ..views.components.sidebar import Sidebar
from ..views.components.topbar import Topbar
from ..views.pages.login_page import LoginPage
from ..views.pages.dashboard_page import DashboardPage
from ..views.pages.kloter_page import KloterPage
from ..views.pages.paket_page import PaketPage
from ..views.pages.karyawan_page import KaryawanPage
from ..views.pages.profil_page import ProfilPage
from ..views.pages.settings_page import SettingsPage


class AmanahBaggageApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._theme_mode = "dark"
        ctk.set_appearance_mode(self._theme_mode)
        ctk.set_default_color_theme("blue")
        self._setup_window()
        init_db()
        self._show_login()
        # Auto-reconnect jika URL sudah tersimpan
        if gs_sync.is_configured():
            threading.Thread(target=gs_sync.connect, daemon=True).start()

    def _setup_window(self) -> None:
        self.title("Amanah Baggage — Sistem Manajemen Pengiriman")
        w, h = 1200, 750
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.minsize(960, 600)

    # ------------------------------------------------------------------
    def _show_login(self) -> None:
        self._clear_window()
        LoginPage(self, on_success=self._on_login_success).pack(fill="both", expand=True)

    def _on_login_success(self) -> None:
        self._build_shell()
        self._navigate("dashboard")

    def _build_shell(self) -> None:
        self._clear_window()
        self._shell = ctk.CTkFrame(self, fg_color="transparent")
        self._shell.pack(fill="both", expand=True)

        self._sidebar = Sidebar(self._shell, on_navigate=self._navigate)
        self._sidebar.pack(side="left", fill="y")

        right = ctk.CTkFrame(self._shell, fg_color="transparent", corner_radius=0)
        right.pack(side="left", fill="both", expand=True)

        self._topbar = Topbar(right, on_theme_toggle=self._toggle_theme)
        self._topbar.pack(fill="x")

        ctk.CTkFrame(right, height=1, fg_color="#2d3748", corner_radius=0).pack(fill="x")

        self._content = ctk.CTkFrame(right, fg_color="transparent", corner_radius=0)
        self._content.pack(fill="both", expand=True)

    def _clear_window(self) -> None:
        for w in self.winfo_children():
            w.destroy()

    def _clear_content(self) -> None:
        for w in self._content.winfo_children():
            w.destroy()

    # ------------------------------------------------------------------
    def _navigate(self, page_id: str) -> None:
        if page_id == "logout":
            self._logout()
            return

        self._clear_content()

        crumbs = {
            "dashboard":  "🏠  Dashboard",
            "kloter":     "📦  Kloter",
            "karyawan":   "👥  Manajemen Karyawan",
            "profil":     "👤  Profil Saya",
            "pengaturan": "⚙️  Pengaturan",
        }
        if hasattr(self, "_topbar"):
            self._topbar.set_breadcrumb(crumbs.get(page_id, page_id))
        if hasattr(self, "_sidebar"):
            self._sidebar.set_active(page_id)

        if page_id == "dashboard":
            DashboardPage(self._content,
                          on_open_kloter=self._open_kloter).pack(fill="both", expand=True)
        elif page_id == "kloter":
            KloterPage(self._content,
                       on_open_kloter=self._open_kloter,
                       root_window=self).pack(fill="both", expand=True)
        elif page_id == "karyawan" and Session.is_admin():
            KaryawanPage(self._content, root_window=self).pack(fill="both", expand=True)
        elif page_id == "profil":
            ProfilPage(self._content, root_window=self).pack(fill="both", expand=True)
        elif page_id == "pengaturan":
            SettingsPage(self._content, root_window=self).pack(fill="both", expand=True)

    def _open_kloter(self, kloter: dict) -> None:
        self._clear_content()
        if hasattr(self, "_topbar"):
            self._topbar.set_breadcrumb(
                f"📦  Kloter  ›  {kloter.get('nama_kloter','')}")
        if hasattr(self, "_sidebar"):
            self._sidebar.set_active("kloter")
        PaketPage(
            self._content,
            kloter=kloter,
            on_back=lambda: self._navigate("kloter"),
            root_window=self,
        ).pack(fill="both", expand=True)

    def _toggle_theme(self) -> None:
        self._theme_mode = "light" if self._theme_mode == "dark" else "dark"
        ctk.set_appearance_mode(self._theme_mode)
        if hasattr(self, "_topbar"):
            self._topbar.update_theme_icon(self._theme_mode)

    def _logout(self) -> None:
        Session.logout()
        self._clear_window()
        LoginPage(self, on_success=self._on_login_success).pack(fill="both", expand=True)


def run() -> None:
    AmanahBaggageApp().mainloop()
