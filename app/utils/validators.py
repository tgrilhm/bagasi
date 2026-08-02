"""Input validation (ECC security rules)."""
import re


class ValidationError(Exception):
    pass


def require(value: str, label: str) -> str:
    v = value.strip()
    if not v:
        raise ValidationError(f"{label} tidak boleh kosong.")
    return v


def validate_no_hp(value: str, label: str = "No HP") -> str:
    v = re.sub(r"[\s\-]", "", value.strip())
    if not v:
        raise ValidationError(f"{label} tidak boleh kosong.")
    if not re.match(r"^(\+62|62|0)\d{8,12}$", v):
        raise ValidationError(f"{label} tidak valid. Contoh: 08123456789")
    return v


def validate_berat(value: str) -> float:
    v = value.strip().replace(",", ".")
    if not v:
        raise ValidationError("Berat tidak boleh kosong.")
    try:
        f = float(v)
    except ValueError:
        raise ValidationError("Berat harus angka. Contoh: 2.5")
    if f <= 0:
        raise ValidationError("Berat harus lebih dari 0.")
    if f > 9999:
        raise ValidationError("Berat tidak valid.")
    return f


def validate_tarif(value: str) -> float:
    v = value.strip().replace(",", ".")
    if not v:
        raise ValidationError("Tarif tidak boleh kosong.")
    try:
        f = float(v)
    except ValueError:
        raise ValidationError("Tarif harus angka. Contoh: 15000")
    if f <= 0:
        raise ValidationError("Tarif harus lebih dari 0.")
    return f


def validate_username(value: str) -> str:
    v = value.strip().lower()
    if not v:
        raise ValidationError("Username tidak boleh kosong.")
    if len(v) < 3:
        raise ValidationError("Username minimal 3 karakter.")
    if len(v) > 20:
        raise ValidationError("Username maksimal 20 karakter.")
    if not re.match(r"^[a-z0-9_]+$", v):
        raise ValidationError("Username hanya huruf, angka, dan underscore.")
    return v


def validate_password(value: str) -> str:
    if not value:
        raise ValidationError("Password tidak boleh kosong.")
    if len(value) < 6:
        raise ValidationError("Password minimal 6 karakter.")
    return value
