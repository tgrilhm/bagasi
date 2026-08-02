"""
Google Sheets Sync — via Google Apps Script Web App.

Tidak membutuhkan OAuth atau credentials.json.
Cukup URL Web App dari Apps Script.

Usage:
    from app.services.sheets_sync import sync
    sync.push_paket("paket_id")
    sync.push_kloter("kloter_id")
    sync.get_status()   # "idle" | "syncing" | "error" | "disconnected"
"""
import json
import logging
import queue
import threading
import urllib.request
import urllib.error
from pathlib import Path
from typing import Callable, Optional

log = logging.getLogger(__name__)

DATA_DIR       = Path(__file__).parent.parent.parent / "data"
GS_CONFIG_FILE = DATA_DIR / "gs_config.json"

# Pertahankan agar settings_page tidak error
CREDS_FILE = DATA_DIR / "credentials.json"


def _load_config() -> dict:
    if GS_CONFIG_FILE.exists():
        try:
            return json.loads(GS_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_config(cfg: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    GS_CONFIG_FILE.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _post(url: str, payload: dict, timeout: int = 15) -> dict:
    """Kirim HTTP POST ke Apps Script Web App."""
    body = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class SheetsSync:
    """Singleton — sinkronisasi ke Google Sheets via Apps Script Web App."""

    def __init__(self) -> None:
        self._url: str = ""
        self._status   = "disconnected"
        self._queue: queue.Queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._lock   = threading.Lock()
        self._callbacks: list[Callable[[str], None]] = []

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def on_status_change(self, cb: Callable[[str], None]) -> None:
        self._callbacks.append(cb)

    def get_status(self) -> str:
        return self._status

    def get_webapp_url(self) -> str:
        return _load_config().get("webapp_url", "")

    def get_spreadsheet_id(self) -> str:
        return _load_config().get("spreadsheet_id", "")

    def is_configured(self) -> bool:
        url = self.get_webapp_url()
        return bool(url and url.startswith("https://script.google.com"))

    def connect(self, webapp_url: str = "") -> tuple[bool, str]:
        """
        Test koneksi ke Apps Script Web App.
        webapp_url: URL deployment dari Google Apps Script.
        Returns (ok, message).
        """
        url = webapp_url or self.get_webapp_url()
        if not url:
            return False, "Web App URL belum diisi."
        if not url.startswith("https://"):
            return False, "URL tidak valid. Harus dimulai dengan https://"
        try:
            result = _post(url, {"action": "ping"}, timeout=10)
            if result.get("status") == "ok":
                cfg = _load_config()
                cfg["webapp_url"] = url
                _save_config(cfg)
                self._url = url
                self._set_status("idle")
                self._ensure_worker()
                return True, "Terhubung ke Google Sheets ✅"
            else:
                return False, f"Respons tidak valid: {result}"
        except urllib.error.HTTPError as e:
            return False, f"HTTP Error {e.code}: {e.reason}"
        except Exception as exc:
            self._set_status("error")
            log.exception("Sheets connect error")
            return False, str(exc)

    def push_kloter(self, kloter_id) -> None:
        """Antri sync satu kloter (terima int atau str)."""
        if self._status not in ("idle", "syncing") or not self._url:
            return
        self._queue.put(("kloter", str(kloter_id)))

    def push_paket(self, paket_id) -> None:
        """Antri sync satu paket (terima int atau str)."""
        if self._status not in ("idle", "syncing") or not self._url:
            return
        self._queue.put(("paket", str(paket_id)))

    def disconnect(self) -> None:
        self._url = ""
        self._set_status("disconnected")

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _set_status(self, s: str) -> None:
        if self._status == s:
            return
        self._status = s
        for cb in list(self._callbacks):
            try:
                cb(s)
            except Exception:
                pass

    def _ensure_worker(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self) -> None:
        while True:
            try:
                kind, item_id = self._queue.get(timeout=2)
                self._set_status("syncing")
                try:
                    if kind == "kloter":
                        self._sync_kloter(item_id)
                    else:
                        self._sync_paket(item_id)
                except Exception:
                    log.exception(f"Sync error: {kind}/{item_id}")
                    self._set_status("error")
                else:
                    if self._queue.empty():
                        self._set_status("idle")
            except queue.Empty:
                pass

    def _sync_kloter(self, kloter_id: str) -> None:
        from ..models import database
        row = database.get_kloter(kloter_id)
        if not row:
            return
        r = dict(row)
        payload = {
            "action": "upsert_kloter",
            "row": [
                r["nama_kloter"],              # Nama Kloter (lookup key)
                r.get("dibuat_oleh", ""),
                r.get("catatan") or "",
                r.get("status", ""),
                r.get("tanggal_dibuat", ""),
                r.get("tanggal_selesai") or "",
            ],
        }
        with self._lock:
            result = _post(self._url, payload)
            if result.get("status") != "ok":
                raise RuntimeError(result.get("message", "unknown error"))

    def _sync_paket(self, paket_id: str) -> None:
        from ..models import database
        row = database.get_paket(paket_id)
        if not row:
            return
        r = dict(row)
        k = database.get_kloter(r["kloter_id"])
        nama_kloter = dict(k)["nama_kloter"] if k else r["kloter_id"]

        # Status pembayaran: otomatis dari penerima_bayar
        status_bayar = "Sudah Dibayarkan" if r.get("penerima_bayar") else "Belum Dibayarkan"

        payload = {
            "action": "upsert_paket",
            "row": [
                r["no_resi"],                      # No Resi (lookup key)
                r.get("nama_pengirim") or "",      # Nama Pengirim
                r.get("no_hp_pengirim") or "",     # No HP Pengirim
                r.get("nama_penerima") or "",      # Nama Penerima
                r.get("no_hp_penerima") or "",     # No HP Penerima
                r.get("kategori") or "",           # Jenis
                r.get("berat_kg", 0),              # Berat (kg)
                r.get("tarif_per_kg", 0),          # Harga/kg
                r.get("total_harga", 0),           # Total Harga
                r.get("penerima_bayar") or "",     # Penerima Bayar
                r.get("rekening_tujuan") or "",    # Rekening Tujuan
                status_bayar,                      # Status Bayar
            ],
        }
        with self._lock:
            result = _post(self._url, payload)
            if result.get("status") != "ok":
                raise RuntimeError(result.get("message", "unknown error"))




# Singleton global
sync = SheetsSync()

# Auto-load URL dari config
_cfg = _load_config()
if _cfg.get("webapp_url"):
    sync._url = _cfg["webapp_url"]
    sync._status = "idle"
    sync._ensure_worker()
