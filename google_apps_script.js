/**
 * Google Apps Script — Amanah Baggage Sync
 *
 * CARA INSTALL:
 * 1. Buka Google Spreadsheet Anda
 * 2. Extensions → Apps Script → hapus kode default, paste file ini
 * 3. Save → Deploy → New deployment
 * 4. Type: Web app | Execute as: Me | Who has access: Anyone
 * 5. Deploy → copy URL → paste di Pengaturan aplikasi
 *
 * Sheet yang akan dibuat otomatis:
 *   - "Paket"  : data semua paket
 *   - "Kloter" : data semua kloter
 */

// ── Konstanta nama sheet ─────────────────────────────────────────────────────
var SHEET_PAKET  = "Paket";
var SHEET_KLOTER = "Kloter";

// ── Header kolom ─────────────────────────────────────────────────────────────
var HEADER_PAKET = [
  "No Resi",
  "Nama Pengirim", "No HP Pengirim",
  "Nama Penerima", "No HP Penerima",
  "Jenis", "Berat (kg)", "Harga/kg (Rp)", "Total Harga (Rp)",
  "Penerima Bayar", "Rekening Tujuan",
  "Status Bayar"
];

var HEADER_KLOTER = [
  "Nama Kloter", "Dibuat Oleh", "Catatan",
  "Status", "Tgl Dibuat", "Tgl Selesai"
];

// ── Entry point ───────────────────────────────────────────────────────────────
function doPost(e) {
  try {
    var payload = JSON.parse(e.postData.contents);
    var action  = payload.action;
    var row     = payload.row || [];

    if (action === "ping") {
      return _json({ status: "ok", message: "Amanah Baggage Apps Script aktif" });
    }

    if (action === "upsert_paket") {
      _upsert(SHEET_PAKET, HEADER_PAKET, row, 0);  // kolom 0 = ID
      return _json({ status: "ok" });
    }

    if (action === "upsert_kloter") {
      _upsert(SHEET_KLOTER, HEADER_KLOTER, row, 0);  // kolom 0 = ID
      return _json({ status: "ok" });
    }

    return _json({ status: "error", message: "Unknown action: " + action });

  } catch (err) {
    return _json({ status: "error", message: err.toString() });
  }
}

// ── GET handler untuk ping via browser ───────────────────────────────────────
function doGet(e) {
  return _json({ status: "ok", message: "Amanah Baggage Apps Script siap" });
}

// ── Helper: upsert row berdasarkan ID ─────────────────────────────────────────
function _upsert(sheetName, headers, rowData, idCol) {
  var ss    = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(sheetName);

  // Buat sheet jika belum ada
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
    sheet.appendRow(headers);
    // Style header
    var headerRange = sheet.getRange(1, 1, 1, headers.length);
    headerRange.setBackground("#1A3A5C");
    headerRange.setFontColor("#FFFFFF");
    headerRange.setFontWeight("bold");
    sheet.setFrozenRows(1);
  }

  var id         = String(rowData[idCol]);
  var data       = sheet.getDataRange().getValues();
  var existingRow = -1;

  // Cari baris yang sudah ada berdasarkan ID (skip header = row 0)
  for (var i = 1; i < data.length; i++) {
    if (String(data[i][idCol]) === id) {
      existingRow = i + 1;  // 1-indexed di Sheets
      break;
    }
  }

  if (existingRow > 0) {
    // Update baris yang ada
    sheet.getRange(existingRow, 1, 1, rowData.length).setValues([rowData]);
  } else {
    // Tambah baris baru
    sheet.appendRow(rowData);
    // Alternating row color
    var lastRow = sheet.getLastRow();
    if (lastRow % 2 === 0) {
      sheet.getRange(lastRow, 1, 1, headers.length)
           .setBackground("#EEF3FB");
    }
  }

  // Auto-resize kolom (maksimal tiap 50 baris baru agar tidak lambat)
  if (sheet.getLastRow() % 50 === 0) {
    sheet.autoResizeColumns(1, headers.length);
  }
}

// ── Helper: return JSON response ─────────────────────────────────────────────
function _json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
