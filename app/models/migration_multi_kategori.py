"""
Migration script: Single-kategori → Multi-kategori system.

PENTING: Backup database sebelum menjalankan script ini!

Cara menjalankan:
    python -m app.models.migration_multi_kategori

Perubahan:
- Buat tabel paket_kategori
- Migrate existing paket ke struktur baru
- Remove columns dari paket table
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "amanah_baggage.db"
BACKUP_PATH = Path(__file__).parent.parent.parent / "data" / f"amanah_baggage_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"


def backup_database() -> None:
    """Backup database sebelum migration."""
    import shutil
    if not DB_PATH.exists():
        print(f"❌ Database tidak ditemukan: {DB_PATH}")
        sys.exit(1)
    
    print(f"📦 Backing up database...")
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"✅ Backup created: {BACKUP_PATH}")


def migrate() -> None:
    """Run migration."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        print("\n🔄 Starting migration...")
        
        # 1. Create paket_kategori table
        print("📋 Creating paket_kategori table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paket_kategori (
                id              TEXT PRIMARY KEY,
                paket_id        TEXT NOT NULL,
                isi_barang      TEXT NOT NULL,
                kategori        TEXT NOT NULL,
                berat_kg        REAL NOT NULL,
                tarif_per_kg    REAL NOT NULL,
                total_harga     REAL NOT NULL,
                urutan          INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (paket_id) REFERENCES paket(id) ON DELETE CASCADE
            )
        """)
        
        # 2. Create index for performance
        print("📊 Creating index...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_paket_kategori_paket_id 
            ON paket_kategori(paket_id)
        """)
        
        # 3. Migrate existing data
        print("🔄 Migrating existing paket data...")
        cursor.execute("""
            SELECT id, kategori, berat_kg, tarif_per_kg, total_harga, catatan
            FROM paket
        """)
        pakets = cursor.fetchall()
        
        migrated = 0
        for p in pakets:
            import uuid
            kategori_id = str(uuid.uuid4())[:8].upper()
            isi_barang = p["catatan"] if p["catatan"] else f"Item {p['kategori']}"
            
            cursor.execute("""
                INSERT INTO paket_kategori 
                (id, paket_id, isi_barang, kategori, berat_kg, tarif_per_kg, total_harga, urutan)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (kategori_id, p["id"], isi_barang, p["kategori"], 
                  p["berat_kg"], p["tarif_per_kg"], p["total_harga"]))
            migrated += 1
        
        print(f"✅ Migrated {migrated} paket records to paket_kategori")
        
        # 4. Create new paket table without old columns
        print("🔧 Restructuring paket table...")
        
        # Create new table
        cursor.execute("""
            CREATE TABLE paket_new (
                id              TEXT PRIMARY KEY,
                no_resi         TEXT UNIQUE NOT NULL,
                kloter_id       TEXT NOT NULL,
                nama_penerima   TEXT NOT NULL,
                no_hp_penerima  TEXT NOT NULL,
                total_harga     REAL NOT NULL,
                status          TEXT NOT NULL DEFAULT 'Dalam Proses',
                tanggal_dibuat  TEXT NOT NULL,
                tanggal_selesai TEXT,
                penerima_bayar  TEXT,
                rekening_tujuan TEXT,
                dibuat_oleh     TEXT NOT NULL,
                updated_at      TEXT,
                FOREIGN KEY (kloter_id)   REFERENCES kloter(id),
                FOREIGN KEY (dibuat_oleh) REFERENCES karyawan(username)
            )
        """)
        
        # Copy data to new table (excluding removed columns)
        cursor.execute("""
            INSERT INTO paket_new 
            (id, no_resi, kloter_id, nama_penerima, no_hp_penerima, 
             total_harga, status, tanggal_dibuat, tanggal_selesai, 
             penerima_bayar, rekening_tujuan, dibuat_oleh, updated_at)
            SELECT 
                id, no_resi, kloter_id, nama_penerima, no_hp_penerima,
                total_harga, status, tanggal_dibuat, tanggal_selesai,
                penerima_bayar, rekening_tujuan, dibuat_oleh, updated_at
            FROM paket
        """)
        
        # Drop old table and rename new
        cursor.execute("DROP TABLE paket")
        cursor.execute("ALTER TABLE paket_new RENAME TO paket")
        
        print("✅ Paket table restructured")
        
        # 5. Commit all changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print(f"📁 Backup available at: {BACKUP_PATH}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        print(f"🔄 Database remains unchanged. Backup at: {BACKUP_PATH}")
        raise
    finally:
        conn.close()


def verify_migration() -> None:
    """Verify migration results."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    print("\n🔍 Verifying migration...")
    
    # Check paket_kategori exists and has data
    cursor.execute("SELECT COUNT(*) FROM paket_kategori")
    pk_count = cursor.fetchone()[0]
    print(f"  📊 paket_kategori records: {pk_count}")
    
    # Check paket table structure
    cursor.execute("PRAGMA table_info(paket)")
    columns = [row[1] for row in cursor.fetchall()]
    removed = ["nama_pengirim", "no_hp_pengirim", "kategori", "berat_kg", "tarif_per_kg", "catatan"]
    has_removed = any(col in columns for col in removed)
    
    if has_removed:
        print(f"  ⚠️  Old columns still exist: {[c for c in removed if c in columns]}")
    else:
        print(f"  ✅ Old columns removed successfully")
    
    conn.close()
    print("\n✅ Verification complete!")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 BAGASI Migration: Multi-Kategori System")
    print("=" * 60)
    
    # Confirmation
    response = input("\n⚠️  This will modify the database structure. Continue? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Migration cancelled.")
        sys.exit(0)
    
    # Backup
    backup_database()
    
    # Migrate
    migrate()
    
    # Verify
    verify_migration()
    
    print("\n🎉 All done! Please test the application thoroughly.")
