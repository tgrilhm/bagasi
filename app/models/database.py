"""
Database layer — SQLite dengan parameterized queries (ECC security rules).
"""
import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

DB_PATH = Path(__file__).parent.parent.parent / "data" / "amanah_baggage.db"

# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

@contextmanager
def get_conn() -> Generator[sqlite3.Connection, None, None]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        raise exc
    finally:
        conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Schema init
# ---------------------------------------------------------------------------

def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS karyawan (
                username             TEXT PRIMARY KEY,
                nama_lengkap         TEXT NOT NULL,
                password_hash        TEXT NOT NULL,
                is_admin             INTEGER NOT NULL DEFAULT 0,
                is_active            INTEGER NOT NULL DEFAULT 1,
                must_change_password INTEGER NOT NULL DEFAULT 0,
                tanggal_dibuat       TEXT NOT NULL,
                last_login           TEXT
            );

            CREATE TABLE IF NOT EXISTS kloter (
                id              TEXT PRIMARY KEY,
                nama_kloter     TEXT NOT NULL,
                tanggal_dibuat  TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'Terbuka',
                dibuat_oleh     TEXT NOT NULL,
                catatan         TEXT,
                tanggal_dikirim TEXT,
                tanggal_selesai TEXT,
                updated_at      TEXT,
                FOREIGN KEY (dibuat_oleh) REFERENCES karyawan(username)
            );

            CREATE TABLE IF NOT EXISTS paket (
                id              TEXT PRIMARY KEY,
                no_resi         TEXT UNIQUE NOT NULL,
                kloter_id       TEXT NOT NULL,
                nama_pengirim   TEXT NOT NULL,
                no_hp_pengirim  TEXT NOT NULL,
                nama_penerima   TEXT NOT NULL,
                no_hp_penerima  TEXT NOT NULL,
                kategori        TEXT NOT NULL,
                berat_kg        REAL NOT NULL,
                tarif_per_kg    REAL NOT NULL,
                total_harga     REAL NOT NULL,
                status          TEXT NOT NULL DEFAULT 'Dalam Proses',
                catatan         TEXT,
                tanggal_dibuat  TEXT NOT NULL,
                tanggal_selesai TEXT,
                penerima_bayar  TEXT,
                rekening_tujuan TEXT,
                dibuat_oleh     TEXT NOT NULL,
                updated_at      TEXT,
                FOREIGN KEY (kloter_id)   REFERENCES kloter(id),
                FOREIGN KEY (dibuat_oleh) REFERENCES karyawan(username)
            );
        """)

        # Migrate: add status & payment columns if not exist
        for col_sql in [
            "ALTER TABLE paket ADD COLUMN status TEXT NOT NULL DEFAULT 'Dalam Proses'",
            "ALTER TABLE paket ADD COLUMN tanggal_selesai TEXT",
            "ALTER TABLE paket ADD COLUMN penerima_bayar TEXT",
            "ALTER TABLE paket ADD COLUMN rekening_tujuan TEXT",
        ]:
            col_name = col_sql.split("ADD COLUMN ")[1].split()[0]
            try:
                conn.execute(f"SELECT {col_name} FROM paket LIMIT 1")
            except sqlite3.OperationalError:
                conn.execute(col_sql)
        conn.commit()

        # Seed admin default
        row = conn.execute(
            "SELECT username FROM karyawan WHERE username = ?", ("admin",)
        ).fetchone()
        if not row:
            conn.execute(
                """INSERT INTO karyawan
                   (username, nama_lengkap, password_hash, is_admin, is_active,
                    must_change_password, tanggal_dibuat)
                   VALUES (?, ?, ?, 1, 1, 0, ?)""",
                ("admin", "Administrator", hash_password("admin123"), _now()),
            )


def _now() -> str:
    return datetime.now().isoformat()


def _gen_id() -> str:
    import uuid
    return str(uuid.uuid4())[:8].upper()


# ---------------------------------------------------------------------------
# Nomor Resi  AMH-MMDD-NNN
# ---------------------------------------------------------------------------

def generate_no_resi() -> str:
    today = datetime.now()
    prefix = f"AMH-{today.strftime('%m%d')}-"
    with get_conn() as conn:
        row = conn.execute(
            "SELECT no_resi FROM paket WHERE no_resi LIKE ? ORDER BY no_resi DESC LIMIT 1",
            (f"{prefix}%",),
        ).fetchone()
    if row:
        last_num = int(row["no_resi"].split("-")[-1])
        return f"{prefix}{last_num + 1:03d}"
    return f"{prefix}001"


# ---------------------------------------------------------------------------
# Karyawan
# ---------------------------------------------------------------------------

def get_karyawan(username: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM karyawan WHERE username = ?", (username,)
        ).fetchone()


def get_all_karyawan() -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM karyawan ORDER BY nama_lengkap"
        ).fetchall()


def verify_login(username: str, password: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM karyawan WHERE username = ? AND password_hash = ? AND is_active = 1",
            (username, hash_password(password)),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE karyawan SET last_login = ? WHERE username = ?",
                (_now(), username),
            )
        return row


def insert_karyawan(
    username: str, nama_lengkap: str, password: str,
    is_admin: bool, must_change_password: bool = True
) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO karyawan
               (username, nama_lengkap, password_hash, is_admin, is_active,
                must_change_password, tanggal_dibuat)
               VALUES (?, ?, ?, ?, 1, ?, ?)""",
            (username, nama_lengkap, hash_password(password),
             int(is_admin), int(must_change_password), _now()),
        )


def update_karyawan(username: str, nama_lengkap: str, is_admin: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE karyawan SET nama_lengkap = ?, is_admin = ? WHERE username = ?",
            (nama_lengkap, int(is_admin), username),
        )


def change_password(username: str, new_password: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE karyawan SET password_hash = ?, must_change_password = 0 WHERE username = ?",
            (hash_password(new_password), username),
        )


def set_karyawan_active(username: str, is_active: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE karyawan SET is_active = ? WHERE username = ?",
            (int(is_active), username),
        )


# ---------------------------------------------------------------------------
# Kloter
# ---------------------------------------------------------------------------

def get_all_kloter(status_filter: Optional[str] = None) -> list[sqlite3.Row]:
    with get_conn() as conn:
        if status_filter:
            return conn.execute(
                "SELECT * FROM kloter WHERE status = ? ORDER BY tanggal_dibuat DESC",
                (status_filter,),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM kloter ORDER BY tanggal_dibuat DESC"
        ).fetchall()


def get_kloter(kloter_id: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM kloter WHERE id = ?", (kloter_id,)
        ).fetchone()


def insert_kloter(nama: str, dibuat_oleh: str, catatan: Optional[str] = None) -> str:
    kloter_id = _gen_id()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO kloter (id, nama_kloter, tanggal_dibuat, status, dibuat_oleh, catatan)
               VALUES (?, ?, ?, 'Terbuka', ?, ?)""",
            (kloter_id, nama, _now(), dibuat_oleh, catatan),
        )
    return kloter_id


def update_kloter(kloter_id: str, nama: str, catatan: Optional[str]) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE kloter SET nama_kloter = ?, catatan = ?, updated_at = ? WHERE id = ?",
            (nama, catatan, _now(), kloter_id),
        )


def update_kloter_status(kloter_id: str, status: str) -> None:
    now = _now()
    with get_conn() as conn:
        if status == "Dikirim":
            conn.execute(
                "UPDATE kloter SET status = ?, tanggal_dikirim = ?, updated_at = ? WHERE id = ?",
                (status, now, now, kloter_id),
            )
        elif status == "Selesai":
            conn.execute(
                "UPDATE kloter SET status = ?, tanggal_selesai = ?, updated_at = ? WHERE id = ?",
                (status, now, now, kloter_id),
            )
        else:
            conn.execute(
                "UPDATE kloter SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, kloter_id),
            )


def delete_kloter(kloter_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM paket WHERE kloter_id = ?", (kloter_id,))
        conn.execute("DELETE FROM kloter WHERE id = ?", (kloter_id,))


def get_kloter_summary(kloter_id: str) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            """SELECT COUNT(*) as total_paket,
                      COALESCE(SUM(berat_kg), 0)    as total_berat,
                      COALESCE(SUM(total_harga), 0) as total_pendapatan
               FROM paket WHERE kloter_id = ?""",
            (kloter_id,),
        ).fetchone()
        return dict(row) if row else {"total_paket": 0, "total_berat": 0.0, "total_pendapatan": 0.0}


# ---------------------------------------------------------------------------
# Paket
# ---------------------------------------------------------------------------

def get_paket_by_kloter(kloter_id: str) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM paket WHERE kloter_id = ? ORDER BY tanggal_dibuat",
            (kloter_id,),
        ).fetchall()


def get_paket(paket_id: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM paket WHERE id = ?", (paket_id,)
        ).fetchone()


def get_paket_by_resi(no_resi: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM paket WHERE no_resi = ?", (no_resi,)
        ).fetchone()


def insert_paket(
    kloter_id: str,
    nama_pengirim: str,
    no_hp_pengirim: str,
    nama_penerima: str,
    no_hp_penerima: str,
    kategori: str,
    berat_kg: float,
    tarif_per_kg: float,
    dibuat_oleh: str,
    catatan: Optional[str] = None,
) -> str:
    paket_id = _gen_id()
    no_resi  = generate_no_resi()
    total    = round(berat_kg * tarif_per_kg, 2)
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO paket
               (id, no_resi, kloter_id, nama_pengirim, no_hp_pengirim,
                nama_penerima, no_hp_penerima, kategori, berat_kg,
                tarif_per_kg, total_harga, catatan, tanggal_dibuat, dibuat_oleh)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (paket_id, no_resi, kloter_id, nama_pengirim, no_hp_pengirim,
             nama_penerima, no_hp_penerima, kategori, berat_kg,
             tarif_per_kg, total, catatan, _now(), dibuat_oleh),
        )
    return paket_id


def update_paket(
    paket_id: str,
    nama_pengirim: str,
    no_hp_pengirim: str,
    nama_penerima: str,
    no_hp_penerima: str,
    kategori: str,
    berat_kg: float,
    tarif_per_kg: float,
    catatan: Optional[str],
) -> None:
    total = round(berat_kg * tarif_per_kg, 2)
    with get_conn() as conn:
        conn.execute(
            """UPDATE paket SET
               nama_pengirim = ?, no_hp_pengirim = ?,
               nama_penerima = ?, no_hp_penerima = ?,
               kategori = ?, berat_kg = ?, tarif_per_kg = ?,
               total_harga = ?, catatan = ?, updated_at = ?
               WHERE id = ?""",
            (nama_pengirim, no_hp_pengirim, nama_penerima, no_hp_penerima,
             kategori, berat_kg, tarif_per_kg, total, catatan, _now(), paket_id),
        )


def update_paket_status(
    paket_id: str,
    status: str,
    penerima_bayar: Optional[str] = None,
    rekening_tujuan: Optional[str] = None,
) -> None:
    """Update status paket beserta info pembayaran jika ada."""
    with get_conn() as conn:
        now = _now()
        if status == "Selesai":
            conn.execute(
                """UPDATE paket
                   SET status = ?, tanggal_selesai = ?, updated_at = ?,
                       penerima_bayar = ?, rekening_tujuan = ?
                   WHERE id = ?""",
                (status, now, now, penerima_bayar, rekening_tujuan, paket_id),
            )
        else:
            conn.execute(
                "UPDATE paket SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, paket_id),
            )


def delete_paket(paket_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM paket WHERE id = ?", (paket_id,))


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------

def get_dashboard_stats() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")
    with get_conn() as conn:
        paket_hari_ini = conn.execute(
            "SELECT COUNT(*) FROM paket WHERE tanggal_dibuat LIKE ?",
            (f"{today}%",),
        ).fetchone()[0]

        kloter_aktif = conn.execute(
            "SELECT COUNT(*) FROM kloter WHERE status = 'Terbuka'"
        ).fetchone()[0]

        pendapatan_hari_ini = conn.execute(
            "SELECT COALESCE(SUM(total_harga), 0) FROM paket WHERE tanggal_dibuat LIKE ?",
            (f"{today}%",),
        ).fetchone()[0]

        paket_bulan_ini = conn.execute(
            "SELECT COUNT(*) FROM paket WHERE tanggal_dibuat LIKE ?",
            (f"{month}%",),
        ).fetchone()[0]

        pendapatan_bulan_ini = conn.execute(
            "SELECT COALESCE(SUM(total_harga), 0) FROM paket WHERE tanggal_dibuat LIKE ?",
            (f"{month}%",),
        ).fetchone()[0]

        recent_paket = conn.execute(
            """SELECT p.no_resi, p.nama_penerima, p.kategori, p.total_harga,
                      p.tanggal_dibuat, p.dibuat_oleh, k.nama_kloter
               FROM paket p JOIN kloter k ON p.kloter_id = k.id
               ORDER BY p.tanggal_dibuat DESC LIMIT 8""",
        ).fetchall()

        kloter_aktif_list = conn.execute(
            """SELECT k.*, COUNT(p.id) as total_paket,
                      COALESCE(SUM(p.total_harga), 0) as total_pendapatan
               FROM kloter k LEFT JOIN paket p ON k.id = p.kloter_id
               WHERE k.status = 'Terbuka'
               GROUP BY k.id ORDER BY k.tanggal_dibuat DESC LIMIT 5""",
        ).fetchall()

    return {
        "paket_hari_ini":       paket_hari_ini,
        "kloter_aktif":         kloter_aktif,
        "pendapatan_hari_ini":  pendapatan_hari_ini,
        "paket_bulan_ini":      paket_bulan_ini,
        "pendapatan_bulan_ini": pendapatan_bulan_ini,
        "recent_paket":         [dict(r) for r in recent_paket],
        "kloter_aktif_list":    [dict(r) for r in kloter_aktif_list],
    }
