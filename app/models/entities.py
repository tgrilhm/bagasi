"""
Domain entities — immutable dataclasses (ECC python-patterns).
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class KategoriBarang(Enum):
    BIASA      = "Biasa"
    SKINCARE   = "Skincare"
    ELEKTRONIK = "Elektronik"

    @classmethod
    def values(cls) -> list[str]:
        return [k.value for k in cls]


class StatusKloter(Enum):
    TERBUKA = "Terbuka"
    DIKIRIM = "Dikirim"
    SELESAI = "Selesai"

    @classmethod
    def values(cls) -> list[str]:
        return [s.value for s in cls]

    def next_status(self) -> Optional["StatusKloter"]:
        flow = {
            StatusKloter.TERBUKA: StatusKloter.DIKIRIM,
            StatusKloter.DIKIRIM: StatusKloter.SELESAI,
        }
        return flow.get(self)


@dataclass(frozen=True)
class Paket:
    id: str
    no_resi: str
    kloter_id: str
    nama_pengirim: str
    no_hp_pengirim: str
    nama_penerima: str
    no_hp_penerima: str
    kategori: str
    berat_kg: float
    tarif_per_kg: float
    total_harga: float
    tanggal_dibuat: datetime
    dibuat_oleh: str
    status: str = "Dalam Proses"
    catatan: Optional[str] = None
    tanggal_selesai: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass(frozen=True)
class Kloter:
    id: str
    nama_kloter: str
    tanggal_dibuat: datetime
    status: str
    dibuat_oleh: str
    catatan: Optional[str] = None
    tanggal_dikirim: Optional[datetime] = None
    tanggal_selesai: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass(frozen=True)
class PaketKategori:
    id: str
    paket_id: str
    isi_barang: str
    kategori: str
    berat_kg: float
    tarif_per_kg: float
    total_harga: float
    urutan: int


@dataclass(frozen=True)
class Karyawan:
    username: str
    nama_lengkap: str
    password_hash: str
    is_admin: bool
    is_active: bool
    must_change_password: bool
    tanggal_dibuat: datetime
    last_login: Optional[datetime] = None
