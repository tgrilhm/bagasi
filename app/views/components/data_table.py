"""
Reusable DataTable dengan search, sort, dan pagination.
"""
import tkinter as tk
from typing import Any, Callable, Optional
import customtkinter as ctk


class DataTable(ctk.CTkFrame):
    """
    Kolom: list of (header_label, key, width, align)
    Rows : list of dict
    on_row_click: callable(row_dict)
    actions: list of (label, color, hover_color, callback(row_dict))
    """

    PAGE_SIZES = [10, 25, 50]

    def __init__(
        self,
        parent,
        columns: list[tuple],
        rows: list[dict],
        on_row_click: Optional[Callable] = None,
        actions: Optional[list] = None,
        page_size: int = 10,
        search_keys: Optional[list[str]] = None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._columns      = columns
        self._all_rows     = rows
        self._on_row_click = on_row_click
        self._actions      = actions or []
        self._page_size    = page_size
        self._search_keys  = search_keys or [c[1] for c in columns]
        self._current_page = 0
        self._sort_key: Optional[str] = None
        self._sort_asc: bool = True
        self._search_var   = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())

        self._build_ui()
        self.set_rows(rows)

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        # Search bar
        search_bar = ctk.CTkFrame(self, fg_color="transparent")
        search_bar.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(search_bar, text="🔍", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 4))
        ctk.CTkEntry(
            search_bar,
            textvariable=self._search_var,
            placeholder_text="Cari...",
            height=32,
            width=260,
        ).pack(side="left")

        # Table frame
        self._table_frame = ctk.CTkFrame(self, corner_radius=8)
        self._table_frame.pack(fill="both", expand=True)

        # Header row
        self._header_frame = ctk.CTkFrame(self._table_frame, fg_color="#1a3a5c", corner_radius=0)
        self._header_frame.pack(fill="x")
        self._build_header()

        # Scroll body
        self._body = ctk.CTkScrollableFrame(
            self._table_frame, fg_color="transparent", corner_radius=0
        )
        self._body.pack(fill="both", expand=True)

        # Pagination
        self._pager = ctk.CTkFrame(self, fg_color="transparent")
        self._pager.pack(fill="x", pady=(6, 0))

    def _build_header(self) -> None:
        for w in self._header_frame.winfo_children():
            w.destroy()
        for label, key, width, align in self._columns:
            sort_icon = ""
            if self._sort_key == key:
                sort_icon = " ▲" if self._sort_asc else " ▼"
            btn = ctk.CTkButton(
                self._header_frame,
                text=f"{label}{sort_icon}",
                width=width,
                height=34,
                fg_color="transparent",
                hover_color="#254e7a",
                text_color="white",
                font=ctk.CTkFont(weight="bold", size=11),
                anchor="w",
                command=lambda k=key: self._sort_by(k),
            )
            btn.pack(side="left", padx=2)
        # Actions header spacer
        if self._actions:
            ctk.CTkLabel(
                self._header_frame,
                text="Aksi",
                width=len(self._actions) * 72,
                text_color="white",
                font=ctk.CTkFont(weight="bold", size=11),
            ).pack(side="right", padx=8)

    # ------------------------------------------------------------------
    def _on_search(self) -> None:
        self._current_page = 0
        self._render()

    def _sort_by(self, key: str) -> None:
        if self._sort_key == key:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_key = key
            self._sort_asc = True
        self._build_header()
        self._render()

    def _filtered_rows(self) -> list[dict]:
        q = self._search_var.get().lower().strip()
        rows = self._all_rows
        if q:
            rows = [
                r for r in rows
                if any(q in str(r.get(k, "")).lower() for k in self._search_keys)
            ]
        if self._sort_key:
            rows = sorted(
                rows,
                key=lambda r: str(r.get(self._sort_key, "")).lower(),
                reverse=not self._sort_asc,
            )
        return rows

    def _render(self) -> None:
        for w in self._body.winfo_children():
            w.destroy()
        for w in self._pager.winfo_children():
            w.destroy()

        filtered = self._filtered_rows()
        total    = len(filtered)
        pages    = max(1, (total + self._page_size - 1) // self._page_size)
        self._current_page = min(self._current_page, pages - 1)

        start = self._current_page * self._page_size
        page_rows = filtered[start: start + self._page_size]

        if not page_rows:
            ctk.CTkLabel(
                self._body,
                text="Tidak ada data.",
                text_color="gray",
                font=ctk.CTkFont(size=12),
            ).pack(pady=30)
        else:
            for i, row in enumerate(page_rows):
                self._build_row(i, row)

        # Pagination controls
        info = ctk.CTkLabel(
            self._pager,
            text=f"Menampilkan {start+1}–{min(start+self._page_size, total)} dari {total} data",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        info.pack(side="left")

        btn_frame = ctk.CTkFrame(self._pager, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame, text="‹ Prev", width=70, height=28,
            state="normal" if self._current_page > 0 else "disabled",
            command=self._prev_page,
        ).pack(side="left", padx=2)

        ctk.CTkLabel(
            btn_frame,
            text=f"{self._current_page + 1} / {pages}",
            font=ctk.CTkFont(size=11),
            width=60,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_frame, text="Next ›", width=70, height=28,
            state="normal" if self._current_page < pages - 1 else "disabled",
            command=self._next_page,
        ).pack(side="left", padx=2)

    def _build_row(self, idx: int, row: dict) -> None:
        bg = "#1e1e2e" if idx % 2 == 0 else "#16162a"
        frame = ctk.CTkFrame(self._body, fg_color=bg, corner_radius=0, cursor="hand2")
        frame.pack(fill="x", pady=1)

        # ── Action buttons FIRST (pack side="right" harus didahulukan) ──
        if self._actions:
            act_frame = ctk.CTkFrame(frame, fg_color="transparent")
            act_frame.pack(side="right", padx=6, pady=4)
            for lbl, fg_c, hov_c, cb in self._actions:
                ctk.CTkButton(
                    act_frame,
                    text=lbl, width=64, height=26,
                    fg_color=fg_c, hover_color=hov_c,
                    font=ctk.CTkFont(size=10),
                    command=lambda r=row, c=cb: c(r),
                ).pack(side="left", padx=2)

        # ── Kolom data ──
        for label, key, width, align in self._columns:
            val = row.get(key, "")
            if callable(val):
                val = val()
            ctk.CTkLabel(
                frame, text=str(val), width=width, anchor=align,
                font=ctk.CTkFont(size=11),
            ).pack(side="left", padx=6, pady=6)

        if self._on_row_click:
            frame.bind("<Button-1>", lambda e, r=row: self._on_row_click(r))

    def _prev_page(self) -> None:
        self._current_page -= 1
        self._render()

    def _next_page(self) -> None:
        self._current_page += 1
        self._render()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def set_rows(self, rows: list[dict]) -> None:
        self._all_rows     = rows
        self._current_page = 0
        self._render()

    def refresh(self, rows: list[dict]) -> None:
        self.set_rows(rows)
