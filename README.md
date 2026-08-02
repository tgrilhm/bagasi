# BAGASI

Aplikasi desktop untuk manajemen pengiriman bagasi/paket Amanah Baggage. Aplikasi ini dibuat dengan Python dan CustomTkinter, memakai SQLite sebagai database lokal, serta mendukung ekspor resi dan sinkronisasi data ke Google Sheets melalui Google Apps Script Web App.

## Fitur

- Login pengguna dan manajemen karyawan.
- Dashboard ringkasan paket, kloter aktif, dan pendapatan.
- Manajemen kloter pengiriman.
- Manajemen paket per kloter.
- Nomor resi otomatis dengan format `AMH-MMDD-NNN`.
- Ekspor data ke Excel.
- Generate resi dalam format PDF/gambar.
- Sinkronisasi kloter dan paket ke Google Sheets via Apps Script.
- Tema gelap/terang.

## Struktur Proyek

```text
BAGASI/
+-- app/
|   +-- core/          # Entry aplikasi, session, shell UI
|   +-- models/        # Entity dan akses SQLite
|   +-- services/      # Integrasi Google Sheets
|   +-- utils/         # Exporter, formatter, generator resi, validator
|   +-- views/         # Komponen dan halaman UI
+-- main.py            # Entry point aplikasi
+-- requirements.txt   # Dependency Python
+-- google_apps_script.js
```

## Persyaratan

- Python 3.11 atau lebih baru.
- Git.
- Google Apps Script Web App jika ingin memakai sinkronisasi Google Sheets.

## Instalasi

Clone repository:

```bash
git clone https://github.com/tgrilhm/bagasi.git
cd bagasi
```

Buat virtual environment:

```bash
python -m venv .venv
```

Aktifkan virtual environment di Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependency:

```bash
pip install -r requirements.txt
```

## Menjalankan Aplikasi

```bash
python main.py
```

Saat pertama dijalankan, aplikasi akan membuat database lokal di:

```text
data/amanah_baggage.db
```

Login awal:

```text
Username: admin
Password: admin123
```

Segera ubah password setelah login pertama, terutama jika aplikasi dipakai untuk data operasional nyata.

## Google Sheets Sync

Aplikasi memakai Google Apps Script Web App, bukan OAuth langsung. File `google_apps_script.js` dapat digunakan sebagai script di Google Apps Script.

Alur umum:

1. Buat Google Sheet untuk tujuan sinkronisasi.
2. Buat project Google Apps Script.
3. Tempel isi `google_apps_script.js`.
4. Deploy sebagai Web App.
5. Masukkan URL Web App di halaman Pengaturan aplikasi.

Konfigurasi lokal akan disimpan di:

```text
data/gs_config.json
```

File ini tidak dipush ke GitHub karena berisi konfigurasi lokal.

## File Yang Tidak Dipush

Repository ini sengaja mengabaikan file runtime dan file sensitif, seperti:

- `data/*.db`
- `data/credentials.json`
- `data/gs_config.json`
- `client_secret*.json`
- `exports/`
- `build/`
- `dist/`
- `__pycache__/`

Jangan commit file credential, database produksi, hasil export pelanggan, atau secret Google ke repository publik.

## Build Executable

Jika ingin membuat executable Windows, project ini pernah memakai PyInstaller melalui file `.spec`, tetapi artifact build tidak disimpan di repository. Jalankan build dari environment lokal sesuai kebutuhan.

## Lisensi

Belum ditentukan.
