"""
Test script untuk generate receipt image
Jalankan: python test_resi_image.py
"""
from datetime import datetime
from pathlib import Path
from app.utils.resi_image_generator import cetak_resi_image

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
    "catatan": "Handle with care",
    "tanggal_dibuat": datetime.now().isoformat(),
    "dibuat_oleh": "Admin"
}

sample_kloter = {
    "id": "KLTR001",
    "nama_kloter": "Kloter Juli 2026 - Batch 1",
    "status": "Terbuka"
}

# Sample kategoris - multiple categories to test the new feature
sample_kategoris = [
    {
        "id": 1,
        "nama_kategori": "Pakaian",
        "berat_kg": 3.5,
        "tarif_per_kg": 15000
    },
    {
        "id": 2,
        "nama_kategori": "Elektronik",
        "berat_kg": 2.0,
        "tarif_per_kg": 25000
    }
]

# Generate Image
output_path = Path("test_receipt_sample.png")
try:
    print("[INFO] Generating receipt image...")
    cetak_resi_image(sample_paket, sample_kloter, sample_kategoris, output_path)
    print(f"[OK] Receipt image berhasil dibuat: {output_path.absolute()}")
    print(f"[OK] Format: PNG image (300px x 600px)")
    print(f"[OK] Silakan buka file untuk melihat hasilnya")
    
    # Auto open
    import os
    os.startfile(str(output_path.absolute()))
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
