# Inspection Report by FRNFEB — Backend

Backend for the Rotary Maintenance inspection report digitization tool.
Fills `V2.xlsx`, recalculates it, and exports a 3-page PDF + a clean
`.xlsx`, without ever using openpyxl to save the workbook (see below).

## Running it

```bash
cd backend
pip install -r requirements.txt --break-system-packages   # if needed
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Requires **LibreOffice** (`soffice`) on PATH — used headless via the
pyuno bridge, never opened with the target file as a CLI argument (see
"Why pyuno" below).

Frontend: open `frontend/frontend/pages/report-form.html`. If the
backend isn't on `http://localhost:8000`, set
`window.MRG_API_BASE = "http://your-host:port"` before `generate.js`
loads (e.g. add a small inline `<script>` before its `<script src=...>`
tag).

## What was actually wrong with the two assumptions in the brief

1. **"Frontend sudah selesai 100%, tinggal baca `collectFormData()`"** —
   that function (and `initFormSubmit`) did not exist anywhere in the
   zip. The submit button only showed a "coming soon" toast. Added as a
   new file, `frontend/frontend/js/generate.js`, wired in with one
   `<script>` tag — no existing file's structure, fields, or design was
   touched.

2. **"Checkbox sudah diganti dropdown, tidak ada masalah form-control"**
   — false for the Cause section. `ISI DATA` has 28 legacy ActiveX
   checkboxes and `AUTO DARI ISI DATA` (the printed summary) has 14 more
   (Direct/Root Cause fishbone categories — Man/Material/Machine/
   Method/External/Bad Repair/etc). No VBA project and no `FmlaLink`
   exist anywhere in the file, so they're purely decorative — but they
   are real ActiveX controls, which is exactly the hang risk rule #4
   anticipated. CPL Pump's Good/Bad columns, by contrast, really are
   plain blank cells (no checkbox, no dropdown, no data validation at
   all in that sheet).

## Architecture

```
app/
  cell_map.py          field name -> cell reference, derived from
                        inspecting the real template (not guessed)
  xlsx_xml.py           raw XML cell read/write engine (zip surgery)
  fill_workbook.py       fills ISI DATA + CPL PUMP + the one direct
                        AUTO DARI ISI DATA cell + cause checkboxes
  photos_xml.py         adds the 3 inspection photos via raw
                        xl/drawings/drawing5.xml edits (no openpyxl)
  libreoffice_runner.py  pyuno automation: recalc, PDF export,
                        page setup, helper-sheet removal
  models.py, filename.py, main.py   FastAPI wiring
```

### Why raw XML instead of openpyxl for writing (rule #1)

Confirmed independently: openpyxl round-trips (load+save) silently drop
the legacy Data Validation extension and can disturb embedded
images/OLE objects even with zero edits. Every write in this backend
edits only the target `<c>` elements inside the relevant
`xl/worksheets/sheetN.xml` (and `xl/drawings/*.xml` for photos/
checkboxes) via string surgery, then re-zips with every other zip entry
copied byte-for-byte. Verified via `zipfile.testzip()` + an openpyxl
*read* pass after every write in this session.

### Why pyuno instead of a CLI `vnd.sun.star.script:` macro URI (rule #4)

The brief's own suggested technique (StarBasic macro registered under
the LibreOffice user profile, invoked via
`soffice ... "vnd.sun.star.script:Standard.Module1.RunJob?..."`)
reliably returned exit code 0 and did *nothing* in this environment —
no output files, no error. Rather than debug that further, this
backend starts a file-less `soffice --headless --accept=socket:...`
listener and drives it via the pyuno bridge from Python. The safety
property rule #4 actually cares about is preserved exactly:
`Desktop.loadComponentFromURL(url, "_blank", 0, (Hidden=True,
MacroExecutionMode=NEVER_EXECUTE))` — the file path is **never** passed
as a `soffice <file>` CLI argument, which is what risks an indefinite
hang on documents with legacy form controls (confirmed this template
has 42 of them).

### A LibreOffice PDF-export quirk that cost real debugging time

Setting `Sheet.IsVisible = False` does **not** exclude a sheet from
`storeToURL(..., "calc_pdf_Export")` — a hidden sheet still produced a
page (confirmed by rendering: page 1 was the `TUTORIAL` sheet's own
baked-in worked example, "CA-1"/"PU-1502-A"/etc, which lives in
`sharedStrings.xml` referenced from `sheet1.xml`, nothing to do with
this backend's data). The fix that actually works:
`sheet.setPrintAreas(())` on every sheet that should NOT appear in the
PDF, in addition to `IsVisible = False`.

### Fit-to-page (rule #8)

`PageStyle.Width/Height` set to Letter (21590/27940, in 1/100mm — there
is no `PaperFormat` enum property on the Calc page style object despite
what some LO scripting examples show) and `ScaleToPagesX = ScaleToPagesY
= 1` on every sheet kept visible for export.

## Cell mapping — confirmed vs. assumed

Everything in `cell_map.py` was derived from the real file (openpyxl
dumps + raw XML), not guessed, **except** the following documented
assumptions:

| Field(s) | What was assumed | Why |
|---|---|---|
| `phenomenaNote[]` | All notes joined with " / " into one cell (`N3`) | Template only has one Note cell for Phenomena, even though the frontend collects one per row |
| `contentPart[]` / `contentAction[]` | Only the first 4 entries are used | Template only has 4 slots (`O3:O6` / `P3:P6`), frontend UI allows more |
| CPL Pump "Bearing Housing" | Only the DE/0° reading is written | The item has 4 physical sub-measurement rows (DE/NDE x 0°/90°); frontend collects one After/Before pair per item |
| CPL Pump "Lub Oil" / "Grease" | Share one printed row; first non-empty wins for text fields (Good/Bad marks are independent) | Template only has one "Lub oil / grease" row |
| Coupling alignment table (`alignRimBefore0` etc.) | Mapped to the *Coupling* item (rows 63-67), not *Pulley* as the frontend's own label says; value written as `"0°:1.2"` directly into the angle-label cell | Confirmed by rendering the PDF: Pulley's real row is a single tan-angle formula, the 4-angle Round/Face table is under Coupling. There is no separate blank cell for the number — the operator is expected to overwrite the label cell itself. |
| Cause checkboxes, 3 duplicated captions ("Bad Repair/Scheduling/Prevention") | First occurrence (document order) = Direct Cause, second = Root Cause | These 3 captions physically appear twice on the print sheet with no linked cell to disambiguate which is which |
| `AUTO DARI ISI DATA!N10` (Inspector name line) | Written directly, bypassing `ISI DATA!K3` | This cell has no formula at all — it's a stray leftover literal string ("Farhan + 1 MP") in the original template. Nothing else on the print sheet reads the inspector's name, so without this direct write it would never appear on the printed report no matter what the operator enters. |
| CPL Pump Good/Bad marks | Written as a plain "✓" character | Confirmed no checkbox/dropdown exists for these columns; any single character works, change `GOOD_MARK` in `fill_workbook.py` if you'd prefer e.g. "X" |
| Items not collected by the frontend (Flushing/Quenching, Mechaseal sub-parts, Gland Packing sub-parts, Coupling sub-item labels) | Left blank | Already blank in the template; the 16-item frontend checklist doesn't cover all ~32 rows of the real CPL-MRT-4202 form |

## Known cosmetic limitations (not data bugs)

- **PRESSURE / FLOW RATE / MOTOR CURRENT** show `##` in the Test Run
  section for values with more digits than the template's original
  column width allows (e.g. `5.2` fits, `120` may not). This is a
  pre-existing column-width constraint in the template; fixing it would
  mean resizing columns, which the brief explicitly said not to do.
- A blank optional Note field could show a stray `0` instead of being
  empty, because the print sheet's formula (`=ISI DATA!Q3` etc.)
  evaluates a truly-empty referenced cell as `0`. Fixed for Content
  Note and Phenomena Note by writing an explicit empty string instead
  of skipping the cell; if you spot the same `0` artifact anywhere else
  after testing with your own real data, the same one-line fix applies.

## Testing performed this session

- Round-tripped every write through openpyxl (read-only) to confirm
  correct values landed in the correct cells.
- Verified zip integrity (`zipfile.testzip()`) after every stage.
- Ran the full pipeline through actual LibreOffice (installed in this
  environment) twice with different sample payloads, rendered the
  resulting PDFs to images, and visually confirmed: logo intact, all
  3 pages present with correct page count, cause checkboxes ticked in
  the right positions, CPL Pump Good/Bad marks on the right rows,
  replacement parts table, all 3 inspection photos placed in their
  slots, and the Coupling alignment values.
- Exercised the actual FastAPI app (not just the underlying functions)
  via `TestClient`, including both download endpoints, confirming
  correct auto-generated filenames.

**Not tested**: real photos from an actual phone (only synthetic solid-
color JPEGs were used), the actual browser `report-form.html` +
`generate.js` flow end-to-end in a real browser (I don't have one in
this sandbox) — worth a manual click-through before relying on it,
concurrent job requests, and the `DELETE /api/job/{job_id}` cleanup
endpoint.
