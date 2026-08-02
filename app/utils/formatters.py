"""Display formatters."""
from datetime import datetime


def rupiah(amount: float) -> str:
    return f"Rp {amount:,.0f}".replace(",", ".")


def tanggal_indo(iso_str: str) -> str:
    """'2024-07-31T10:00:00' → '31 Jul 2024'"""
    try:
        dt = datetime.fromisoformat(iso_str)
        bulan = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                 "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        return f"{dt.day:02d} {bulan[dt.month]} {dt.year}"
    except Exception:
        return iso_str[:10] if iso_str else "-"


def tanggal_waktu(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso_str[:16] if iso_str else "-"


def berat_fmt(kg: float) -> str:
    if kg == int(kg):
        return f"{int(kg)} kg"
    return f"{kg:.1f} kg"
