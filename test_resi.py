"""
Script test untuk generate sample resi PDF
Jalankan: python test_resi.py
"""
from datetime import datetime
from pathlib import Path
from app.utils.pdf_generator import cetak_resi

# Data sample
sample_paket = {
    "id": "TEST001",
    "no_resi": "AMH-0731-001",
    "nama_penerima": "Ahmad Zainudin",
    "no_hp_penerima": "081234567890",
    "kategori": "Pakaian",
    "berat_kg": 5.5,
    "tarif_per_kg": 15000,
    "total_harga": 82500,
    "catatan": "Handle with care - Barang pecah belah",
    "tanggal_dibuat": datetime.now().isoformat(),
    "dibuat_oleh": "Admin"
}

sample_kloter = {
    "id": "KLTR001",
    "nama_kloter": "Kloter Juli 2026 - Batch 1",
    "status": "Terbuka"
}

# Generate PDF
output_path = Path("test_receipt_sample.pdf")
try:
    cetak_resi(sample_paket, sample_kloter, output_path)
    print(f"[OK] Receipt PDF berhasil dibuat: {output_path.absolute()}")
    print(f"[OK] Ukuran: 80mm x 200mm")
    print(f"[OK] Silakan buka file untuk melihat hasilnya")
    
    # Auto open
    import os
    os.startfile(str(output_path.absolute()))
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
