"""
Generate PDF resi & laporan kloter menggunakan ReportLab.
Design profesional dengan warna brand Amanah Baggage.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)

from .formatters import berat_fmt, rupiah, tanggal_indo, tanggal_waktu

# Brand colors
BRAND_DARK  = colors.HexColor("#0f1729")
BRAND_BLUE  = colors.HexColor("#1a3a5c")
BRAND_LIGHT = colors.HexColor("#2563a8")
BRAND_ACCENT= colors.HexColor("#7eb3e8")
TEXT_DARK   = colors.HexColor("#1a1a1a")
TEXT_GRAY   = colors.HexColor("#666666")
BG_LIGHT    = colors.HexColor("#f4f7fb")
BG_ROW_ALT  = colors.HexColor("#eef3fb")
SUCCESS     = colors.HexColor("#27ae60")

COMPANY     = "Amanah Baggage"
TAGLINE     = "Jasa Pengiriman Bagasi Terpercaya"

# Resi page size: 80mm × 200mm (increased height for better layout)
RESI_SIZE   = (80 * mm, 200 * mm)


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def _styles():
    base = getSampleStyleSheet()
    return {
        "company": ParagraphStyle("company", fontSize=14, fontName="Helvetica-Bold",
                                   textColor=colors.white, alignment=1, spaceAfter=1),
        "tagline":  ParagraphStyle("tagline",  fontSize=7, fontName="Helvetica",
                                   textColor=BRAND_ACCENT, alignment=1),
        "resi_no":  ParagraphStyle("resi_no",  fontSize=16, fontName="Helvetica-Bold",
                                   textColor=BRAND_BLUE, alignment=1, spaceBefore=3, spaceAfter=3),
        "kloter":   ParagraphStyle("kloter",   fontSize=8, fontName="Helvetica",
                                   textColor=BRAND_LIGHT, alignment=1),
        "section":  ParagraphStyle("section",  fontSize=7.5, fontName="Helvetica-Bold",
                                   textColor=BRAND_BLUE, spaceBefore=4, spaceAfter=2),
        "label":    ParagraphStyle("label",    fontSize=8, fontName="Helvetica",
                                   textColor=TEXT_GRAY),
        "value":    ParagraphStyle("value",    fontSize=8.5, fontName="Helvetica-Bold",
                                   textColor=TEXT_DARK),
        "total_l":  ParagraphStyle("total_l",  fontSize=9, fontName="Helvetica-Bold",
                                   textColor=colors.white),
        "total_v":  ParagraphStyle("total_v",  fontSize=13, fontName="Helvetica-Bold",
                                   textColor=colors.white, alignment=2),
        "footer":   ParagraphStyle("footer",   fontSize=7, fontName="Helvetica",
                                   textColor=TEXT_GRAY, alignment=1),
        # Laporan styles
        "h1":  ParagraphStyle("h1",  fontSize=18, fontName="Helvetica-Bold",
                               textColor=BRAND_BLUE, spaceAfter=2),
        "sub": ParagraphStyle("sub", fontSize=10, fontName="Helvetica",
                               textColor=TEXT_GRAY, spaceAfter=0),
        "th":  ParagraphStyle("th",  fontSize=9, fontName="Helvetica-Bold",
                               textColor=colors.white),
        "td":  ParagraphStyle("td",  fontSize=8.5, fontName="Helvetica",
                               textColor=TEXT_DARK),
        "td_r":ParagraphStyle("td_r",fontSize=8.5, fontName="Helvetica",
                               textColor=TEXT_DARK, alignment=2),
        "td_c":ParagraphStyle("td_c",fontSize=8.5, fontName="Helvetica",
                               textColor=TEXT_DARK, alignment=1),
        "td_b":ParagraphStyle("td_b",fontSize=8.5, fontName="Helvetica-Bold",
                               textColor=BRAND_BLUE, alignment=2),
    }


# ---------------------------------------------------------------------------
# Resi PDF
# ---------------------------------------------------------------------------

def cetak_resi(paket: dict, kloter: dict, kategoris: list, output_path: Path) -> Path:
    """Generate resi PDF untuk paket dengan multiple kategoris."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    s = _styles()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=RESI_SIZE,
        leftMargin=5*mm, rightMargin=5*mm,
        topMargin=5*mm, bottomMargin=5*mm,
    )

    story = []

    # Header brand
    header_data = [[
        Paragraph(COMPANY, s["company"]),
        Paragraph(TAGLINE, s["tagline"]),
    ]]
    header_tbl = Table(header_data, colWidths=[70*mm])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), BRAND_DARK),
        ("TOPPADDING",  (0,0), (-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING",(0,0), (-1,-1), 8),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 3*mm))

    # Nomor Resi box
    resi_data = [[
        Paragraph("NOMOR RESI", ParagraphStyle("rl", fontSize=7, fontName="Helvetica-Bold",
                  textColor=BRAND_LIGHT, alignment=1, spaceAfter=2)),
        Paragraph(paket["no_resi"], s["resi_no"]),
        Paragraph(kloter["nama_kloter"], s["kloter"]),
    ]]
    resi_tbl = Table(resi_data, colWidths=[68*mm])
    resi_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), BG_LIGHT),
        ("BOX",         (0,0), (-1,-1), 1, BRAND_LIGHT),
        ("TOPPADDING",  (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(resi_tbl)
    story.append(Spacer(1, 3*mm))

    # Penerima section
    def info_section(title: str, nama: str, hp: str):
        data = [
            [Paragraph(title, s["section"])],
            [Table([[Paragraph("Nama", s["label"]), Paragraph(nama, s["value"])],
                    [Paragraph("No HP", s["label"]), Paragraph(hp, s["value"])]],
                   colWidths=[16*mm, 50*mm],
                   style=[("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)])],
        ]
        tbl = Table(data, colWidths=[68*mm])
        tbl.setStyle(TableStyle([
            ("BOX",         (0,0), (-1,-1), 0.5, colors.HexColor("#d0e0f0")),
            ("TOPPADDING",  (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
        ]))
        return tbl

    # Penerima
    story.append(info_section(
        "PENERIMA",
        paket.get("nama_penerima") or "—",
        paket.get("no_hp_penerima") or "—",
    ))
    story.append(Spacer(1, 3*mm))

    # Detail barang - combined format
    detail_rows = [
        [Paragraph("DETAIL BARANG", s["section"])],
    ]
    
    # Format kategori gabungan seperti Excel
    if kategoris:
        kat_parts = []
        total_berat = 0
        for kat in kategoris:
            kat_parts.append(f"{kat['kategori']} - {kat['isi_barang']} ({kat['berat_kg']}kg)")
            total_berat += kat['berat_kg']
        detail_str = ", ".join(kat_parts)
    else:
        detail_str = "—"
        total_berat = 0
    
    items = [
        ("Detail Kategori", detail_str),
        ("Total Berat", f"{total_berat:.2f} kg"),
        ("Tanggal", tanggal_indo(paket["tanggal_dibuat"])),
    ]

    inner = [[Paragraph(k, s["label"]), Paragraph(v, s["value"])] for k, v in items]
    detail_rows.append([Table(inner, colWidths=[16*mm, 50*mm],
                              style=[("TOPPADDING",(0,0),(-1,-1),2),
                                     ("BOTTOMPADDING",(0,0),(-1,-1),2)])])
    detail_tbl = Table(detail_rows, colWidths=[68*mm])
    detail_tbl.setStyle(TableStyle([
        ("BOX",         (0,0), (-1,-1), 0.5, colors.HexColor("#d0e0f0")),
        ("TOPPADDING",  (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(detail_tbl)
    story.append(Spacer(1, 3*mm))

    # Total box
    total_data = [[
        Paragraph("TOTAL PEMBAYARAN", s["total_l"]),
        Paragraph(rupiah(paket["total_harga"]), s["total_v"]),
    ]]
    total_tbl = Table(total_data, colWidths=[34*mm, 34*mm])
    total_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), BRAND_BLUE),
        ("TOPPADDING",  (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING",(0,0), (-1,-1), 8),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(total_tbl)
    story.append(Spacer(1, 3*mm))

    # Footer
    cetak_oleh = f"Dicetak: {datetime.now().strftime('%d/%m/%Y %H:%M')}  •  Oleh: {paket['dibuat_oleh']}"
    story.append(HRFlowable(width="100%", thickness=0.5, color=TEXT_GRAY))
    story.append(Spacer(1, 1*mm))
    story.append(Paragraph(cetak_oleh, s["footer"]))
    story.append(Paragraph(f"Terima kasih telah menggunakan {COMPANY}", s["footer"]))

    doc.build(story)
    return output_path


# ---------------------------------------------------------------------------
# Laporan Kloter PDF
# ---------------------------------------------------------------------------

def cetak_laporan_kloter(
    kloter: dict, paket_list: list[dict],
    summary: dict, output_path: Path
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    s = _styles()
    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )
    story = []

    # Header
    header_data = [[
        Table([[Paragraph(COMPANY, s["h1"])],
               [Paragraph(TAGLINE, s["sub"])]],
              style=[("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]),
        Table([[Paragraph("LAPORAN KLOTER", ParagraphStyle("lt", fontSize=13,
               fontName="Helvetica-Bold", textColor=BRAND_BLUE, alignment=2))],
               [Paragraph(f"Dicetak: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                ParagraphStyle("lt2", fontSize=9, textColor=TEXT_GRAY, alignment=2))],
               [Paragraph(f"Oleh: {kloter.get('dibuat_oleh','')}", 
                ParagraphStyle("lt3", fontSize=9, textColor=TEXT_GRAY, alignment=2))]],
              style=[("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]),
    ]]
    hdr_tbl = Table(header_data, colWidths=[90*mm, 90*mm])
    hdr_tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(hdr_tbl)
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_BLUE, spaceAfter=8))

    # Info kloter
    sc = {"Terbuka": "#27ae60", "Dikirim": "#e67e22", "Selesai": "#7f8c8d"}
    status_color = colors.HexColor(sc.get(kloter["status"], "#555"))

    info_items = [
        ("Nama Kloter",    kloter["nama_kloter"]),
        ("Status",         kloter["status"]),
        ("Tanggal Dibuat", tanggal_waktu(kloter["tanggal_dibuat"])),
        ("Dibuat Oleh",    kloter["dibuat_oleh"]),
    ]
    if kloter.get("catatan"):
        info_items.append(("Catatan", kloter["catatan"]))

    info_data = [[Paragraph(k, ParagraphStyle("il", fontSize=9, fontName="Helvetica-Bold",
                 textColor=BRAND_BLUE)),
                  Paragraph(v, ParagraphStyle("iv", fontSize=9, fontName="Helvetica",
                 textColor=TEXT_DARK))]
                 for k, v in info_items]
    info_tbl = Table(info_data, colWidths=[45*mm, 130*mm])
    info_tbl.setStyle(TableStyle([
        ("BACKGROUND",      (0,0), (-1,-1), BG_LIGHT),
        ("ROWBACKGROUNDS",  (0,0), (-1,-1), [BG_LIGHT, colors.white]),
        ("TOPPADDING",      (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",   (0,0), (-1,-1), 5),
        ("LEFTPADDING",     (0,0), (-1,-1), 10),
        ("BOX",             (0,0), (-1,-1), 0.5, colors.HexColor("#d0e0f0")),
        ("LINEBELOW",       (0,0), (-1,-2), 0.5, colors.HexColor("#e0e8f0")),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 5*mm))

    # Summary cards
    sum_data = [[
        Paragraph(f"<b>{summary['total_paket']}</b><br/><font size='8' color='#666'>Total Paket</font>",
                  ParagraphStyle("sc", alignment=1, fontSize=14, fontName="Helvetica-Bold",
                                 textColor=BRAND_BLUE, leading=20)),
        Paragraph(f"<b>{summary['total_berat']:.2f} kg</b><br/><font size='8' color='#666'>Total Berat</font>",
                  ParagraphStyle("sc", alignment=1, fontSize=14, fontName="Helvetica-Bold",
                                 textColor=BRAND_BLUE, leading=20)),
        Paragraph(f"<b>{rupiah(summary['total_pendapatan'])}</b><br/><font size='8' color='#666'>Total Pendapatan</font>",
                  ParagraphStyle("sc", alignment=1, fontSize=14, fontName="Helvetica-Bold",
                                 textColor=SUCCESS, leading=20)),
    ]]
    sum_tbl = Table(sum_data, colWidths=[58*mm, 58*mm, 64*mm])
    sum_tbl.setStyle(TableStyle([
        ("BOX",         (0,0), (-1,-1), 0.5, colors.HexColor("#d0e0f0")),
        ("INNERGRID",   (0,0), (-1,-1), 0.5, colors.HexColor("#d0e0f0")),
        ("TOPPADDING",  (0,0), (-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
    ]))
    story.append(sum_tbl)
    story.append(Spacer(1, 5*mm))

    # Table paket
    header_row = [
        Paragraph("No", s["th"]),
        Paragraph("No Resi", s["th"]),
        Paragraph("Penerima / No HP", s["th"]),
        Paragraph("Kategori", s["th"]),
        Paragraph("Berat", s["th"]),
        Paragraph("Tarif/kg", s["th"]),
        Paragraph("Total", s["th"]),
    ]
    table_data = [header_row]
    for i, p in enumerate(paket_list, 1):
        bg = BG_ROW_ALT if i % 2 == 0 else colors.white
        table_data.append([
            Paragraph(str(i), s["td_c"]),
            Paragraph(p["no_resi"], s["td"]),
            Paragraph(f"{p['nama_penerima']}<br/><font size='7.5' color='#999'>{p['no_hp_penerima']}</font>", s["td"]),
            Paragraph(p["kategori"], s["td_c"]),
            Paragraph(berat_fmt(p["berat_kg"]), s["td_c"]),
            Paragraph(rupiah(p["tarif_per_kg"]), s["td_r"]),
            Paragraph(rupiah(p["total_harga"]), s["td_b"]),
        ])

    # Total row
    table_data.append([
        Paragraph("", s["td"]), Paragraph("", s["td"]),
        Paragraph("", s["td"]), Paragraph("", s["td"]),
        Paragraph("", s["td"]),
        Paragraph("TOTAL", ParagraphStyle("tot", fontSize=9, fontName="Helvetica-Bold",
                           textColor=colors.white, alignment=2)),
        Paragraph(rupiah(summary["total_pendapatan"]),
                  ParagraphStyle("totv", fontSize=9, fontName="Helvetica-Bold",
                                 textColor=colors.white, alignment=2)),
    ])

    n = len(table_data)
    tbl = Table(table_data, colWidths=[10*mm, 25*mm, 45*mm, 18*mm, 16*mm, 20*mm, 25*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),  (-1,0),  BRAND_BLUE),
        ("BACKGROUND",    (0,-1), (-1,-1), BRAND_LIGHT),
        ("TEXTCOLOR",     (0,0),  (-1,0),  colors.white),
        ("TOPPADDING",    (0,0),  (-1,-1), 5),
        ("BOTTOMPADDING", (0,0),  (-1,-1), 5),
        ("LEFTPADDING",   (0,0),  (-1,-1), 6),
        ("RIGHTPADDING",  (0,0),  (-1,-1), 6),
        ("LINEBELOW",     (0,0),  (-1,-2), 0.3, colors.HexColor("#d0e0f0")),
        ("BOX",           (0,0),  (-1,-1), 0.5, colors.HexColor("#d0e0f0")),
        ("VALIGN",        (0,0),  (-1,-1), "MIDDLE"),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 5*mm))

    # Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=TEXT_GRAY))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f"{COMPANY}  —  Laporan Resmi  |  Total Pendapatan: {rupiah(summary['total_pendapatan'])}",
        ParagraphStyle("foot", fontSize=8, textColor=TEXT_GRAY, alignment=1)
    ))

    doc.build(story)
    return output_path
