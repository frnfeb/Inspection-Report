"""Fills the V2.xlsx template with submitted report data using only raw
XML surgery (see xlsx_xml.py) -- never openpyxl for writing."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

from . import cell_map as cm
from .xlsx_xml import WorkbookXmlEditor

SHEET_ISI_DATA = "xl/worksheets/sheet2.xml"
SHEET_CPL_PUMP = "xl/worksheets/sheet4.xml"
VML_CAUSE_CHECKBOXES = "xl/drawings/vmlDrawing2.vml"  # AUTO DARI ISI DATA

GOOD_MARK = "\u2713"  # checkmark

# Ordered so that when a caption occurs twice in the printed checkbox set,
# the FIRST occurrence (by document order / left cluster) is treated as
# the "Direct Cause" instance and the SECOND as "Root Cause". This is a
# documented assumption -- see cell_map.py / delivery notes.
DUPLICATED_CAPTIONS = {"Bad Repair (BR)", "Bad Scheduling (BS)", "Bad Prevention (BV)"}


def _num(v):
    if v is None or v == "":
        return None
    try:
        return float(v) if isinstance(v, str) and ("." in v) else int(v)
    except (TypeError, ValueError):
        return v


def fill_isi_data(editor: WorkbookXmlEditor, data: dict) -> None:
    sheet = editor.sheet(SHEET_ISI_DATA)

    for field, ref in cm.ISI_DATA_SINGLE.items():
        if field in ("phenomenaNoteJoined", "directCause", "rootCause", "contentNote"):
            continue  # handled specially below
        val = data.get(field)
        if val in (None, ""):
            continue
        if field in cm.NUMERIC_FIELDS:
            sheet.set_number(ref, _num(val))
        else:
            sheet.set_text(ref, val)

    # dates: template stores them as text in this sheet's raw layout; write
    # as plain text (YYYY-MM-DD from the <input type=date>) to avoid
    # depending on any particular date serial/format guess.
    for field in ("dateStart", "dateFinish"):
        val = data.get(field)
        if val:
            sheet.set_text(cm.ISI_DATA_SINGLE[field], val)

    # phenomena note -> joined into single N3 cell. Written even when
    # empty: a truly empty (missing) cell is coerced to 0 by the print
    # sheet's "=ISI DATA!Q3"-style formula, whereas an explicit empty
    # string reference renders as blank -- confirmed by rendering the
    # PDF with an empty Content Note and seeing a stray "0".
    notes = [n for n in (data.get("phenomenaNote") or []) if n]
    sheet.set_text(cm.ISI_DATA_SINGLE["phenomenaNoteJoined"], " / ".join(notes))

    # same 0-instead-of-blank issue applies to Content Note (Q3)
    sheet.set_text(cm.ISI_DATA_SINGLE["contentNote"], data.get("contentNote") or "")

    # direct / root cause -> joined checked labels into R3 / T3
    direct = [v for v in (data.get("directCause") or []) if v]
    root = [v for v in (data.get("rootCause") or []) if v]
    if direct:
        sheet.set_text(cm.ISI_DATA_SINGLE["directCause"], ", ".join(direct))
    if root:
        sheet.set_text(cm.ISI_DATA_SINGLE["rootCause"], ", ".join(root))

    # repeating: phenomena what-happen
    col, start, maxn = cm.ISI_DATA_REPEAT["phenomenaWhatHappen"]
    for i, v in enumerate((data.get("phenomenaWhatHappen") or [])[:maxn]):
        if v:
            sheet.set_text(f"{col}{start + i}", v)

    # repeating: content part / action (template only has 4 slots)
    for key in ("contentPart", "contentAction"):
        col, start, maxn = cm.ISI_DATA_REPEAT[key]
        vals = (data.get(key) or [])[:maxn]
        for i, v in enumerate(vals):
            if v:
                sheet.set_text(f"{col}{start + i}", v)

    # replacement parts table
    names = data.get("partName") or []
    qtys = data.get("partQty") or []
    modifies = data.get("partModify") or []
    newtypes = data.get("partNewType") or []
    remarks = data.get("partRemark") or []
    # The print sheet's Replacement Parts formulas (e.g. ='ISI DATA'!AA4)
    # are plain references with no blank-guard, so a truly-empty source
    # cell renders as a stray "0" in the PDF (same class of bug as the
    # Content Note fix above). Write every row up to PARTS_MAX_ROWS,
    # explicitly blanking out unused rows instead of skipping them.
    for i in range(cm.PARTS_MAX_ROWS):
        row = cm.PARTS_START_ROW + i
        name = names[i] if i < len(names) else ""
        if not name:
            sheet.set_text(f"{cm.PARTS_NO_COLUMN}{row}", "")
            sheet.set_text(f"{cm.PARTS_COLUMNS['partName']}{row}", "")
            sheet.set_text(f"{cm.PARTS_COLUMNS['partQty']}{row}", "")
            sheet.set_text(f"{cm.PARTS_COLUMNS['partModify']}{row}", "")
            sheet.set_text(f"{cm.PARTS_COLUMNS['partNewType']}{row}", "")
            sheet.set_text(f"{cm.PARTS_COLUMNS['partRemark']}{row}", "")
            continue
        sheet.set_number(f"{cm.PARTS_NO_COLUMN}{row}", i + 1)
        sheet.set_text(f"{cm.PARTS_COLUMNS['partName']}{row}", name)
        qty_val = qtys[i] if i < len(qtys) else ""
        if qty_val not in (None, ""):
            sheet.set_number(f"{cm.PARTS_COLUMNS['partQty']}{row}", _num(qty_val))
        else:
            sheet.set_text(f"{cm.PARTS_COLUMNS['partQty']}{row}", "")
        sheet.set_text(f"{cm.PARTS_COLUMNS['partModify']}{row}", modifies[i] if i < len(modifies) else "")
        sheet.set_text(f"{cm.PARTS_COLUMNS['partNewType']}{row}", newtypes[i] if i < len(newtypes) else "")
        sheet.set_text(f"{cm.PARTS_COLUMNS['partRemark']}{row}", remarks[i] if i < len(remarks) else "")


def fill_cpl_pump(editor: WorkbookXmlEditor, data: dict) -> None:
    sheet = editor.sheet(SHEET_CPL_PUMP)

    good_items = set(data.get("cplGood") or [])
    bad_items = set(data.get("cplBad") or [])
    conditions = data.get("cplCondition") or []
    afters = data.get("cplAfter") or []
    befores = data.get("cplBefore") or []
    units = data.get("cplUnit") or []
    unit_customs = data.get("cplUnitCustom") or []
    condition_customs = data.get("cplConditionCustom") or []
    action_customs = data.get("cplActionCustom") or []
    actions = data.get("cplAction") or []
    remarks = data.get("cplRemark") or []

    # The frontend submits these as parallel arrays in the same fixed
    # item order as CPL_PUMP_ITEM_ROW's iteration order in the HTML.
    item_names = list(cm.CPL_PUMP_ITEM_ROW.keys())
    # de-duplicate row targets (Lub Oil / Grease share row 69) without
    # losing data: if both have a value, keep the first non-empty one.
    written_rows = set()

    for i, item in enumerate(item_names):
        row = cm.CPL_PUMP_ITEM_ROW[item]
        cols = cm.CPL_PUMP_COLUMNS
        if item in good_items:
            sheet.set_text(f"{cols['good']}{row}", GOOD_MARK)
        if item in bad_items:
            sheet.set_text(f"{cols['bad']}{row}", GOOD_MARK)

        if row in written_rows:
            # second item sharing this row (Lub Oil/Grease) -- Good/Bad
            # marks above are still applied, but the free-text columns
            # already got the first item's values, so skip re-writing them.
            continue
        written_rows.add(row)

        if i < len(conditions) and conditions[i]:
            cond_val = conditions[i]
            if cond_val == "__custom__" and i < len(condition_customs):
                cond_val = condition_customs[i]
            sheet.set_text(f"{cols['condition']}{row}", cond_val)
        if i < len(afters) and afters[i]:
            sheet.set_text(f"{cols['after']}{row}", afters[i])
        if i < len(befores) and befores[i]:
            sheet.set_text(f"{cols['before']}{row}", befores[i])
        unit_val = None
        if i < len(units) and units[i]:
            unit_val = units[i]
            if unit_val == "__custom__" and i < len(unit_customs):
                unit_val = unit_customs[i]
        if unit_val:
            sheet.set_text(f"{cols['unit']}{row}", unit_val)
        if i < len(actions) and actions[i]:
            act_val = actions[i]
            if act_val == "__custom__" and i < len(action_customs):
                act_val = action_customs[i]
            sheet.set_text(f"{cols['action']}{row}", act_val)
        if i < len(remarks) and remarks[i]:
            sheet.set_text(f"{cols['remark']}{row}", remarks[i])

    # Coupling alignment table (rows 63-67) -- see cell_map.ALIGN_CELLS.
    # The label cell already reads e.g. "0°"; we make it "0°:1.2" (no
    # spaces, to fit the narrow column) and blank the adjacent
    # now-redundant ":" cell so it doesn't show as "1.2 :".
    ALIGN_COLON_NEXT = {"O": "P", "Q": "R", "T": "U", "V": "W"}
    for prefix, col in cm.ALIGN_CELLS.items():
        for angle, row in cm.ALIGN_ROWS.items():
            val = data.get(f"{prefix}{angle}")
            if val:
                sheet.set_text(f"{col}{row}", f"{angle}\u00b0:{val}")
                colon_col = ALIGN_COLON_NEXT.get(col)
                if colon_col:
                    sheet.set_text(f"{colon_col}{row}", "")


def fill_auto_direct(editor: WorkbookXmlEditor, data: dict) -> None:
    """A small number of print-sheet cells have no working formula link
    back to ISI DATA (see cell_map.AUTO_DIRECT_CELLS) and must be written
    directly."""
    sheet = editor.sheet(cm.AUTO_SHEET)
    for field, ref in cm.AUTO_DIRECT_CELLS.items():
        val = data.get(field)
        if val:
            sheet.set_text(ref, val)


def toggle_cause_checkboxes(zin_path: Path, out_vml: dict) -> None:
    """Not used directly -- see toggle_cause_checkboxes_in_editor for the
    zip-safe version that goes through the same save path as the sheet
    XML edits."""


def build_cause_checkbox_vml(original_vml: str, direct: list[str], root: list[str]) -> str:
    """Returns a modified copy of vmlDrawing2.vml (AUTO DARI ISI DATA cause
    checkboxes) with <x:Checked>1</x:Checked> inserted into the shapes
    whose caption matches a checked cause category.

    See DUPLICATED_CAPTIONS: for captions that appear twice in this file,
    the first occurrence maps to Direct Cause, the second to Root Cause.
    """
    direct_set, root_set = set(direct), set(root)
    seen_dup_count: dict[str, int] = {}

    def repl(match: re.Match) -> str:
        shape_xml = match.group(0)
        cap_m = re.search(r"<font[^>]*>(.*?)</font>", shape_xml, re.S)
        if not cap_m:
            return shape_xml
        caption = re.sub(r"\s+", " ", cap_m.group(1)).strip()

        if caption in DUPLICATED_CAPTIONS:
            occurrence = seen_dup_count.get(caption, 0)
            seen_dup_count[caption] = occurrence + 1
            is_checked = caption in (direct_set if occurrence == 0 else root_set)
        else:
            is_checked = caption in direct_set or caption in root_set

        if not is_checked:
            return shape_xml

        if "<x:Checked>" in shape_xml:
            return shape_xml
        return shape_xml.replace(
            "<x:ClientData ObjectType=\"Checkbox\">",
            "<x:ClientData ObjectType=\"Checkbox\"><x:Checked>1</x:Checked>",
            1,
        )

    return re.sub(r"<v:shape\b.*?</v:shape>", repl, original_vml, flags=re.S)


def patch_blank_guard_formulas(editor: WorkbookXmlEditor) -> None:
    """
    LibreOffice (unlike real Excel) coerces a directly-referenced blank
    cell to 0 even when the source cell holds an explicit empty string --
    confirmed by testing in isolation. This template has ~100 formulas
    on the print sheet that are bare references (='ISI DATA'!X3) with no
    blank-guard, so any optional field the operator leaves empty shows a
    stray "0" on the PDF instead of a blank. This rewrites every such
    bare reference to =IF('ISI DATA'!X3="","",'ISI DATA'!X3), matching
    the guard style the template's OWN author already uses on ~25 other
    cells. Structural/formatting-neutral: only the formula text changes.
    """
    sheet = editor.sheet(cm.AUTO_SHEET)
    pattern = re.compile(r"<f>('ISI DATA'!\$?[A-Z]+\$?\d+)</f>")

    def repl(m: re.Match) -> str:
        ref = m.group(1)
        return f'<f>IF({ref}="","",{ref})</f>'

    sheet.content = pattern.sub(repl, sheet.content)


def patch_root_cause_detail_formula(editor: WorkbookXmlEditor) -> None:
    """
    Fixes a formula bug in the user's revised template: AUTO DARI ISI
    DATA!AC24 (Root Cause's "Detail Cause" box) points at
    'ISI DATA'!AN3 (Motor Vibration status) instead of 'ISI DATA'!U3
    (Detail Root Cause) -- confirmed by inspecting the formula directly.
    Without this, whatever the operator picks for Motor Vibration status
    appears under Root Cause's detail text instead of what they actually
    typed.

    IMPORTANT: this targets the AC24 *cell* directly (not a text search
    for the formula content) because 'ISI DATA'!AN3 is referenced by 4
    different formula fragments in this sheet (AC24's own nested IF, and
    a separate, correct, unguarded reference at AE35) -- a plain
    string-replace on the formula text hit the wrong one the first time
    this was attempted (confirmed by testing: it silently corrupted
    AE35's Motor Vibration display instead of fixing AC24).

    This patches this backend's own copy of the template only -- the
    user's master .xlsx file has the same bug and should be checked
    separately if they edit the template again.
    """
    sheet = editor.sheet(cm.AUTO_SHEET)
    m = sheet._cell_pattern("AC24").search(sheet.content)
    if not m:
        return
    cell_xml = m.group(0)
    if "'ISI DATA'!AN3" not in cell_xml:
        return  # already fixed or unexpected content -- don't touch it
    fixed = cell_xml.replace("'ISI DATA'!AN3", "'ISI DATA'!U3")
    sheet.content = sheet.content[: m.start()] + fixed + sheet.content[m.end() :]


def fill_workbook(template_path: Path, data: dict, out_path: Path) -> None:
    editor = WorkbookXmlEditor(template_path)
    fill_isi_data(editor, data)
    fill_cpl_pump(editor, data)
    fill_auto_direct(editor, data)
    patch_root_cause_detail_formula(editor)
    patch_blank_guard_formulas(editor)
    editor.save(out_path)
    editor.close()

    # patch the cause checkboxes on the print sheet (separate zip entry,
    # done as a second pass on the file we just wrote so we still never
    # touch anything via openpyxl).
    direct = [v for v in (data.get("directCause") or []) if v]
    root = [v for v in (data.get("rootCause") or []) if v]
    if direct or root:
        _patch_zip_entry(
            out_path,
            VML_CAUSE_CHECKBOXES,
            lambda content: build_cause_checkbox_vml(content, direct, root),
        )


def _patch_zip_entry(xlsx_path: Path, entry_name: str, transform) -> None:
    tmp_path = xlsx_path.with_suffix(".tmp.xlsx")
    with zipfile.ZipFile(xlsx_path, "r") as zin, zipfile.ZipFile(
        tmp_path, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == entry_name:
                data = transform(data.decode("utf-8")).encode("utf-8")
            zout.writestr(item, data)
    tmp_path.replace(xlsx_path)
