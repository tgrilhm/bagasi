# Quick Migration Runner
# Jalankan: python run_migration.py

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.migration_multi_kategori import backup_database, migrate, verify_migration

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 BAGASI Migration: Multi-Kategori System")
    print("=" * 60)
    
    response = input("\n⚠️  This will modify the database structure. Continue? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Migration cancelled.")
        sys.exit(0)
    
    try:
        backup_database()
        migrate()
        verify_migration()
        print("\n✅ Migration SUCCESS! Silakan restart aplikasi.")
    except Exception as e:
        print(f"\n❌ Migration FAILED: {e}")
        print("Database backup tersimpan, tidak ada perubahan pada DB.")
