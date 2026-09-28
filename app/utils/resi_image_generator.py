"""
Generator Resi JPG berbasis Pillow murni.
Tidak membutuhkan Chrome, browser, atau html2image.
Kompatibel dengan distribusi .exe (standalone).
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from .formatters import berat_fmt, rupiah, tanggal_indo

# ── Brand colors (RGB) ────────────────────────────────────────────────
C_DARK   = (15,  23,  41)   # #0f1729  header background
C_BLUE   = (26,  58,  92)   # #1a3a5c  resi box border / total bg
C_LIGHT  = (37,  99, 168)   # #2563a8  kloter label / section
C_ACCENT = (126, 179, 232)  # #7eb3e8  tagline
C_WHITE  = (255, 255, 255)
C_BLACK  = (26,  26,  26)   # #1a1a1a  value text
C_GRAY   = (102, 102, 102)  # #666666  label / footer text
C_BG     = (244, 247, 251)  # #f4f7fb  resi box fill
C_SECT   = (240, 247, 255)  # section title strip
C_BORDER = (208, 224, 240)  # #d0e0f0  section border

COMPANY = "Amanah Baggage"
TAGLINE = "Jasa Pengiriman Bagasi Terpercaya"
W       = 300   # canvas width px
MARGIN  = 12    # horizontal margin


# ── Font loader ───────────────────────────────────────────────────────

def _load_fonts() -> dict:
    """Load system fonts dengan fallback bertingkat."""
    REG = [
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    BOLD = [
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
    ]

    def _f(paths: list, size: int) -> ImageFont.FreeTypeFont:
        for p in paths:
            if Path(p).exists():
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()

    return {
        "company":  _f(BOLD, 15),
        "tagline":  _f(REG,  10),
        "resi_lbl": _f(BOLD,  9),
        "resi_no":  _f(BOLD, 20),
        "kloter":   _f(REG,  10),
        "section":  _f(BOLD, 10),
        "label":    _f(REG,  10),
        "value":    _f(BOLD, 11),
        "total_l":  _f(BOLD, 11),
        "total_v":  _f(BOLD, 22),
        "footer":   _f(REG,   9),
    }


# ── Drawing helpers ───────────────────────────────────────────────────

def _text_w(draw: ImageDraw.Draw, text: str, font) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def _center_text(draw: ImageDraw.Draw, y: int, text: str,
                 font, color: tuple) -> None:
    tw = _text_w(draw, text, font)
    draw.text(((W - tw) // 2, y), text, fill=color, font=font)


# ── Main painter ──────────────────────────────────────────────────────

class ResiPainter:
    """Menggambar resi ke canvas PIL dan export ke JPG."""

    ROW_H      = 22   # tinggi tiap baris data
    SECT_HEAD  = 28   # tinggi judul seksi
    SECTION_GAP = 8   # jarak antar seksi

    def __init__(self, paket: dict, kloter: dict, kategoris: list):
        self._p  = paket
        self._k  = kloter
        self._kategoris = kategoris
        self._f  = _load_fonts()

    # -- estimasi total tinggi canvas ---------------------------------
    def _calc_height(self) -> int:
        h  = 80              # header
        h += 10 + 88         # resi box + gap
        h += 10              # gap

        # penerima
        h += self.SECT_HEAD + 2 * self.ROW_H + self.SECTION_GAP
        # detail barang
        # Hitung jumlah baris: untuk setiap kategori (4 rows: nama, berat, tarif, subtotal)
        # + 1 row untuk tanggal + catatan jika ada
        num_kategori = len(self._kategoris) if self._kategoris else 1
        n  = (num_kategori * 4) + 1  # 4 rows per kategori + 1 tanggal
        if self._p.get("catatan"):
            n += 1
        h += self.SECT_HEAD + n * self.ROW_H + self.SECTION_GAP

        h += 10 + 75        # total box + gap
        h += 2              # separator
        h += 10 + 3 * 15    # footer
        h += 18             # bottom padding
        return h

    # -- render -------------------------------------------------------
    def render(self) -> Image.Image:
        height = self._calc_height()
        img    = Image.new("RGB", (W, height), C_WHITE)
        d      = ImageDraw.Draw(img)
        f      = self._f
        y      = 0

        # ── 1. Header ────────────────────────────────────────────────
        d.rectangle([0, y, W, y + 72], fill=C_DARK)
        _center_text(d, y + 13, COMPANY,  f["company"],  C_WHITE)
        _center_text(d, y + 36, TAGLINE,  f["tagline"],  C_ACCENT)
        y += 78

        # ── 2. Nomor Resi box ─────────────────────────────────────────
        y += 8
        bx = MARGIN
        bw = W - MARGIN
        by2 = y + 86
        d.rectangle([bx, y, bw, by2], fill=C_BG, outline=C_BLUE, width=2)
        _center_text(d, y +  8, "NOMOR RESI",
                     f["resi_lbl"], C_LIGHT)
        _center_text(d, y + 22, self._p.get("no_resi", ""),
                     f["resi_no"],  C_BLUE)
        _center_text(d, y + 56, self._k.get("nama_kloter", ""),
                     f["kloter"],   C_LIGHT)
        y = by2 + 12

        # ── 3. Penerima ───────────────────────────────────────────────
        y = self._section(d, y, "PENERIMA", [
            ("Nama",  self._p.get("nama_penerima")  or "—"),
            ("No HP", self._p.get("no_hp_penerima") or "—"),
        ])
        y += self.SECTION_GAP

        # ── 5. Detail Barang ──────────────────────────────────────────
        detail = []
        
        # Iterasi semua kategori barang
        if self._kategoris:
            for i, kat in enumerate(self._kategoris, 1):
                prefix = f"Kategori {i}" if len(self._kategoris) > 1 else "Kategori"
                berat = kat.get("berat_kg", 0)
                tarif = kat.get("tarif_per_kg", 0)
                subtotal = berat * tarif
                
                detail.append((prefix, kat.get("nama_kategori", "")))
                detail.append(("  Berat", berat_fmt(berat)))
                detail.append(("  Tarif/kg", rupiah(tarif)))
                detail.append(("  Sub Total", rupiah(subtotal)))
        else:
            # Fallback jika kategoris kosong (backward compatibility)
            berat = self._p.get("berat_kg", 0)
            tarif = self._p.get("tarif_per_kg", 0)
            subtotal = berat * tarif
            
            detail.append(("Kategori", self._p.get("kategori", "")))
            detail.append(("Berat", berat_fmt(berat)))
            detail.append(("Tarif/kg", rupiah(tarif)))
            detail.append(("Sub Total", rupiah(subtotal)))
        
        # Tanggal dibuat (hanya sekali untuk semua kategori)
        detail.append(("Tanggal", tanggal_indo(self._p.get("tanggal_dibuat", ""))))
        
        # Catatan opsional
        if self._p.get("catatan"):
            detail.append(("Catatan", str(self._p["catatan"])))
        
        y = self._section(d, y, "DETAIL BARANG", detail)
        y += 12

        # ── 6. Total Pembayaran ───────────────────────────────────────
        total_str = rupiah(self._p.get("total_harga", 0))
        d.rectangle([MARGIN, y, W - MARGIN, y + 70], fill=C_BLUE)
        _center_text(d, y +  8, "TOTAL PEMBAYARAN", f["total_l"], C_WHITE)
        _center_text(d, y + 26, total_str,           f["total_v"], C_WHITE)
        y += 80

        # ── 7. Separator + Footer ─────────────────────────────────────
        d.line([MARGIN, y, W - MARGIN, y], fill=(200, 200, 200), width=1)
        y += 8
        now_str  = datetime.now().strftime("%d/%m/%Y %H:%M")
        operator = self._p.get("dibuat_oleh", "")
        for line in [
            f"Dicetak: {now_str}",
            f"Oleh: {operator}",
            f"Terima kasih telah menggunakan {COMPANY}",
        ]:
            _center_text(d, y, line, f["footer"], C_GRAY)
            y += 14

        # Crop tepat ke konten
        return img.crop((0, 0, W, y + 12))

    # -- helper seksi ─────────────────────────────────────────────────
    def _section(self, d: ImageDraw.Draw, y: int,
                 title: str, rows: list) -> int:
        f  = self._f
        bx = MARGIN
        bw = W - MARGIN
        section_h = self.SECT_HEAD + len(rows) * self.ROW_H + 6
        by2 = y + section_h

        # Border
        d.rectangle([bx, y, bw, by2], fill=C_WHITE, outline=C_BORDER, width=1)
        # Title strip
        d.rectangle([bx + 1, y + 1, bw - 1, y + self.SECT_HEAD - 2],
                    fill=C_SECT)
        d.text((bx + 8, y + 6), title, fill=C_BLUE, font=f["section"])
        # Separator under title
        d.line([bx, y + self.SECT_HEAD, bw, y + self.SECT_HEAD],
               fill=C_BORDER, width=1)

        # Data rows
        label_w = 76
        for i, (lbl, val) in enumerate(rows):
            ry = y + self.SECT_HEAD + 4 + i * self.ROW_H
            d.text((bx + 8, ry),         lbl, fill=C_GRAY,  font=f["label"])
            d.text((bx + label_w, ry),   val, fill=C_BLACK, font=f["value"])

        return by2


# ── Public API ────────────────────────────────────────────────────────

def cetak_resi_image(paket: dict, kloter: dict, kategoris: list, output_path: Path) -> Path:
    """
    Generate resi JPG menggunakan Pillow (tanpa Chrome/html2image).

    Args:
        paket       : dict data paket dari database
        kloter      : dict data kloter dari database
        kategoris   : list of dict data kategori barang
        output_path : Path file output (ekstensi .jpg / .png)

    Returns:
        Path file JPG yang dihasilkan
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img      = ResiPainter(paket, kloter, kategoris).render()
    jpg_path = output_path.with_suffix(".jpg")
    img.save(str(jpg_path), "JPEG", quality=95)
    return jpg_path
