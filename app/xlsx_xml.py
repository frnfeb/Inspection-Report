"""
Raw XML cell writer for .xlsx files.

Per the hard rule for this project: NEVER use openpyxl to load+save the
whole workbook (it strips images / breaks extension data such as the
Data Validation lists in this template even with zero changes). Instead:
open the .xlsx as a zip, patch only the <c> (cell) elements we care about
inside the target xl/worksheets/sheetN.xml entries with regex/string
surgery, and re-zip with every other entry copied byte-for-byte.

This module knows how to:
  - set a cell's value (text -> inlineStr, number -> plain <v>)
  - insert a cell that doesn't exist yet in a row (borrowing the style
    index from a reference row so it doesn't look unformatted)
  - leave everything else (formulas, styles, drawings, validations,
    shared strings) completely untouched.
"""
from __future__ import annotations

import re
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path


def _col_to_num(col: str) -> int:
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n


def _split_ref(ref: str) -> tuple[str, int]:
    m = re.match(r"^([A-Z]+)(\d+)$", ref)
    if not m:
        raise ValueError(f"bad cell ref {ref!r}")
    return m.group(1), int(m.group(2))


def _escape_xml_text(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


@dataclass
class SheetXml:
    """In-memory, mutable copy of one xl/worksheets/sheetN.xml payload."""

    path_in_zip: str
    content: str
    _style_cache: dict = field(default_factory=dict)

    # -- row lookup --------------------------------------------------
    def _row_span(self, row: int) -> tuple[int, int] | None:
        m = re.search(rf'<row r="{row}"[^>]*>', self.content)
        if not m:
            return None
        start = m.start()
        # find matching </row> (rows never nest, first following </row>)
        end = self.content.index("</row>", start) + len("</row>")
        return start, end

    def _cell_pattern(self, ref: str) -> re.Pattern:
        # matches both self-closed <c r="A3" s="3"/> and full <c ...>...</c>
        return re.compile(
            rf'<c r="{ref}"(?P<attrs>[^>]*?)(?:/>|>(?P<body>.*?)</c>)',
            re.S,
        )

    def _guess_style(self, col: str, row: int) -> str | None:
        """Look for the same column's style in nearby rows (3..20) so a
        newly-inserted cell isn't left with default (unformatted) style."""
        key = col
        if key in self._style_cache:
            return self._style_cache[key]
        for r in range(row - 1, row + 30):
            if r == row:
                continue
            pat = re.compile(rf'<c r="{col}{r}"[^>]*?\bs="(\d+)"')
            m = pat.search(self.content)
            if m:
                self._style_cache[key] = m.group(1)
                return m.group(1)
        self._style_cache[key] = None
        return None

    def set_text(self, ref: str, value: str) -> None:
        if value is None:
            return
        value = str(value)
        self._set_cell(ref, text=value)

    def set_number(self, ref: str, value) -> None:
        if value is None or value == "":
            return
        self._set_cell(ref, number=value)

    # -- core --------------------------------------------------------
    def _set_cell(self, ref: str, text: str | None = None, number=None) -> None:
        col, row = _split_ref(ref)
        pat = self._cell_pattern(ref)
        m = pat.search(self.content)

        if number is not None:
            new_cell = f'<c r="{ref}"{{style}}><v>{number}</v></c>'
        else:
            esc = _escape_xml_text(text)
            # IMPORTANT: an explicit empty string must still be written as
            # a real inlineStr cell (t="inlineStr" with an empty <t/>),
            # NOT as a bare valueless <c/>. A formula that references a
            # truly-valueless cell directly (e.g. ='ISI DATA'!AA4, with no
            # IF-blank-guard) coerces it to 0 in Excel/Calc; a cell that
            # explicitly holds "" is returned as "" instead. Confirmed by
            # testing: the Replacement Parts table showed stray "0" rows
            # until this was fixed to emit inlineStr for "" too.
            new_cell = (
                f'<c r="{ref}"{{style}} t="inlineStr"><is><t xml:space="preserve">'
                f"{esc}</t></is></c>"
            )

        if m:
            # existing cell: keep its style attribute if present
            attrs = m.group("attrs") or ""
            sm = re.search(r'\bs="(\d+)"', attrs)
            style = f' s="{sm.group(1)}"' if sm else ""
            replacement = new_cell.format(style=style)
            self.content = self.content[: m.start()] + replacement + self.content[m.end() :]
            return

        # cell not present in the row at all -> insert it in the right
        # column-sorted position, borrowing a style from a nearby row.
        span = self._row_span(row)
        style_idx = self._guess_style(col, row)
        style = f' s="{style_idx}"' if style_idx else ""
        new_cell = new_cell.format(style=style)

        target_col_num = _col_to_num(col)
        if span is None:
            # whole row missing -- create it right before the next existing
            # row, or before </sheetData> if it's the very last one.
            self._insert_new_row(row, new_cell)
            return

        start, end = span
        row_body = self.content[start:end]
        # find insertion point: first cell in the row whose column index
        # is greater than ours
        cell_iter = list(re.finditer(r'<c r="([A-Z]+)(\d+)"', row_body))
        insert_at = None
        for cm in cell_iter:
            if _col_to_num(cm.group(1)) > target_col_num:
                insert_at = cm.start()
                break
        if insert_at is None:
            # append right before </row>
            insert_at = row_body.rindex("</row>")
        new_row_body = row_body[:insert_at] + new_cell + row_body[insert_at:]
        self.content = self.content[:start] + new_row_body + self.content[end:]

    def _insert_new_row(self, row: int, new_cell: str) -> None:
        # find the next row with a higher number to insert before it
        row_tags = list(re.finditer(r'<row r="(\d+)"', self.content))
        insert_pos = None
        for rm in row_tags:
            if int(rm.group(1)) > row:
                insert_pos = rm.start()
                break
        new_row = f'<row r="{row}">{new_cell}</row>'
        if insert_pos is None:
            idx = self.content.index("</sheetData>")
            self.content = self.content[:idx] + new_row + self.content[idx:]
        else:
            self.content = self.content[:insert_pos] + new_row + self.content[insert_pos:]


class WorkbookXmlEditor:
    """Loads a .xlsx as a zip, lets you patch individual worksheet XML
    payloads in memory, and writes out a new .xlsx with everything else
    copied byte-identical."""

    def __init__(self, src_path: str | Path):
        self.src_path = Path(src_path)
        self._zip = zipfile.ZipFile(self.src_path, "r")
        self._sheets: dict[str, SheetXml] = {}

    def sheet(self, sheet_file: str) -> SheetXml:
        """sheet_file e.g. 'xl/worksheets/sheet2.xml'"""
        if sheet_file not in self._sheets:
            raw = self._zip.read(sheet_file).decode("utf-8")
            self._sheets[sheet_file] = SheetXml(sheet_file, raw)
        return self._sheets[sheet_file]

    def save(self, dest_path: str | Path) -> None:
        dest_path = Path(dest_path)
        with zipfile.ZipFile(self.src_path, "r") as zin, zipfile.ZipFile(
            dest_path, "w", zipfile.ZIP_DEFLATED
        ) as zout:
            for item in zin.infolist():
                if item.filename in self._sheets:
                    data = self._sheets[item.filename].content.encode("utf-8")
                else:
                    data = zin.read(item.filename)
                zout.writestr(item, data)

    def close(self):
        self._zip.close()
