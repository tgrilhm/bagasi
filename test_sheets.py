"""Test koneksi ke Google Sheets via Apps Script Web App."""
import json, urllib.request
from pathlib import Path

cfg_path = Path("data/gs_config.json")
if not cfg_path.exists():
    print("[ERROR] data/gs_config.json tidak ada")
    exit(1)

cfg = json.loads(cfg_path.read_text())
url = cfg.get("webapp_url", "")
sid = cfg.get("spreadsheet_id", "")

print(f"Web App URL : {url[:60]}..." if url else "Web App URL : (kosong)")
print(f"Spreadsheet : {sid}")

if not url:
    print("[ERROR] webapp_url belum diisi di gs_config.json")
    exit(1)

# Ping
try:
    body = json.dumps({"action": "ping"}).encode()
    req  = urllib.request.Request(url, data=body,
                                   headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    print(f"[OK] Ping berhasil: {result}")
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
    exit(1)

# Coba kirim data test (upsert_paket)
try:
    test_row = [
        "TEST-001", "TEST-RESI", "Kloter Test",
        "Pengirim Test", "08123456789",
        "Penerima Test", "08987654321",
        "Pakaian", 2, 100000, 200000,
        "Test dari Python", "Dalam Proses",
        "", "", "admin", "2026-08-01", ""
    ]
    body = json.dumps({"action": "upsert_paket", "row": test_row}).encode()
    req  = urllib.request.Request(url, data=body,
                                   headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    if result.get("status") == "ok":
        print("[OK] Upsert paket test berhasil!")
    else:
        print(f"[WARN] Upsert respons: {result}")
except Exception as e:
    print(f"[ERROR] Upsert paket: {type(e).__name__}: {e}")

print("\n=== SUKSES — Koneksi Apps Script berfungsi! ===")
