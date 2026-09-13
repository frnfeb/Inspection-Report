"""
Cell mapping for V2.xlsx.

REVISION NOTE: the user edited their master template after the first
round of this backend (moved Replacement Parts from BC:BH to Y:AD,
which pushed every column after it +6, and added 2 new fields --
Test Run Full Close Pressure/Motor Current -- at BI3/BJ3). This file
was rebuilt from scratch against that new file by diffing every cell
and formula against the previous version, not by patching offsets by
hand. See the two flagged issues below -- those are things the user's
own edit appears to have broken, not something this backend can fix
by itself.

Sheet "ISI DATA" (raw data -- one single record lives in row 3):
  - Single-value fields: row 3, fixed column.
  - Repeating fields: consecutive rows in a single column, starting at
    row 3.
    - Phenomena "What Happen": column M, rows 3-8   (max 6, unchanged)
    - Content "Part":          column O, rows 3-6   (max 4, unchanged)
    - Content "Action":        column P, rows 3-6   (max 4, unchanged)
    - Replacement Parts:       columns Y-AD, rows 3-13 (max 11 -- the
      template's own print formulas (AUTO!A45:A55) only go 11 rows deep
      now, down from 12; the frontend UI still allows up to 12 rows, a
      12th row would simply never appear on the printed report)

FLAGGED ISSUES IN THE USER'S REVISED TEMPLATE (not something this code
can fix -- these are in the .xlsx itself):
  1. AUTO DARI ISI DATA!AC24 (Root Cause "Detail Cause" box) now pulls
     'ISI DATA'!AN3, which is the Motor (Vibration) status field -- not
     'ISI DATA'!U3 (Detail Root Cause), which no longer has ANY formula
     pulling it anywhere on the print sheet. Root Cause's detail text
     will not appear on the printed report until this formula is fixed
     in the master file. This backend still writes detailRootCause to
     U3 (harmless, just currently invisible on the printout).
  2. AUTO DARI ISI DATA!N10 (Inspector Name line) is still a hardcoded
     leftover string ("Farhan + 1 MP"), not a formula -- same issue as
     the previous version. Still handled via AUTO_DIRECT_CELLS below.
"""

# ---- ISI DATA: single-value fields (row 3) ------------------------------
ISI_DATA_SINGLE = {
    "nama": "A3",
    "plant": "B3",
    "tagNo": "C3",
    "equipmentName": "D3",
    "problemTitle": "E3",
    "mrsNo": "F3",
    "dateStart": "G3",
    "dateFinish": "H3",
    "repairHour": "I3",
    "inspectorPerson": "J3",
    "inspectorName": "K3",
    # L3 = formula (Person x Repair Hour), never write
    "phenomenaNoteJoined": "N3",       # synthetic: joined phenomenaNote[]
    "contentNote": "Q3",
    "directCause": "R3",               # joined checked labels
    "detailCause": "S3",
    "rootCause": "T3",                 # joined checked labels
    "detailRootCause": "U3",           # see flagged issue #1 above
    "nextAction": "V3",
    "counterMeasure": "W3",
    "recommendation": "X3",
    # AE3 = empty gap column, never write
    # AF3 = formula (test run date, auto), never write
    "attendsProcess": "AG3",
    "attendsRotary": "AH3",
    "pressure": "AI3",
    "flowRate": "AJ3",
    "motorCurrent": "AK3",
    "equipVibrationStatus": "AL3",
    "equipNoiseStatus": "AM3",
    "motorVibrationStatus": "AN3",
    "motorNoiseStatus": "AO3",
    "taskCategory": "AP3",
    # AQ3 = formula (vibration verdict), never write
    "csVertical": "AR3",
    "csHorizontal": "AS3",
    "csAxial": "AT3",
    "acsVertical": "AU3",
    "acsHorizontal": "AV3",
    "acsAxial": "AW3",
    "deVertical": "AX3",
    "deHorizontal": "AY3",
    "deAxial": "AZ3",
    "ndeVertical": "BA3",
    "ndeHorizontal": "BB3",
    "ndeAxial": "BC3",
    "csTemperature": "BD3",
    "acsTemperature": "BE3",
    "deTemperature": "BF3",
    "ndeTemperature": "BG3",
    "remarkTestRun": "BH3",
    "testRunFullClosePressure": "BI3",
    "testRunFullCloseMotorCurrent": "BJ3",
}

# fields that are numeric (written with set_number instead of set_text)
NUMERIC_FIELDS = {
    "repairHour", "inspectorPerson", "pressure", "flowRate", "motorCurrent",
    "csVertical", "csHorizontal", "csAxial", "acsVertical", "acsHorizontal",
    "acsAxial", "deVertical", "deHorizontal", "deAxial", "ndeVertical",
    "ndeHorizontal", "ndeAxial", "csTemperature", "acsTemperature",
    "deTemperature", "ndeTemperature", "testRunFullClosePressure",
    "testRunFullCloseMotorCurrent",
}

# ---- ISI DATA: repeating fields (column, start row, max rows) ----------
ISI_DATA_REPEAT = {
    "phenomenaWhatHappen": ("M", 3, 6),
    "contentPart": ("O", 3, 4),
    "contentAction": ("P", 3, 4),
}

# Replacement parts table: now Y:AD (was BC:BH), 11 rows (was 12) --
# see the module docstring for why.
PARTS_COLUMNS = {
    "partName": "Z",
    "partQty": "AA",
    "partModify": "AB",
    "partNewType": "AC",
    "partRemark": "AD",
}
PARTS_NO_COLUMN = "Y"
PARTS_START_ROW = 3
PARTS_MAX_ROWS = 11

# ---- CPL PUMP sheet: unchanged from the previous analysis ---------------
CPL_PUMP_COLUMNS = {
    "good": "G",
    "bad": "I",
    "condition": "K",
    "after": "O",
    "before": "T",
    "unit": "Y",
    "action": "AC",
    "remark": "AH",
}

CPL_PUMP_ITEM_ROW = {
    "Drive and Bearing": 7,
    "Non Drive Bearing": 9,
    "Impeller": 11,
    "Casing": 13,
    "Casing - Gap to Impeller": 13,        # shares row 13 with Casing (one merged block)
    "Flushing/Quenching": 15,
    "Bearing Housing": 16,
    "Bearing Housing - DE (0°-180°, Atas-Bawah)": 16,
    "Bearing Housing - DE (90°-270°)": 17,
    "Bearing Housing - NDE (0°-180°, Atas-Bawah)": 18,
    "Bearing Housing - NDE (90°-270°)": 19,
    "Mechaseal - Mating/Seal Ring": 21,
    "Mechaseal - V-Packing/O-Ring": 25,
    "Mechaseal - Spring & Collar": 27,
    "Mechaseal - Bellows": 30,
    "Gland Packing / Stuffing Box": 34,
    "Gland Packing - Lantern Ring": 37,
    "Shaft Sleeve": 39,
    "Gland Bush": 42,
    "Oil Seal": 45,
    "Shaft": 48,
    "Wear Ring": 52,
    "V-belts": 56,
    "Pulley": 58,
    "Pulley - Alignment (detail di bawah tabel)": 58,   # shares row 58; real
                                                          # data goes via ALIGN_CELLS
    "Coupling - Rubber & Bolt": 63,
    "Coupling - Disk Element": 65,
    "Coupling - Hub": 67,
    "Lub Oil": 69,
    "Grease": 69,
    "Sight Glass": 71,
    "Other": 72,
}
# All 32 items, confirmed two independent ways: (1) directly against the
# CPL PUMP sheet's own column-A labels and merged-cell ranges (rows
# 6-76), and (2) against the frontend's exact item-cell text + checkbox
# `value=` attributes (grep 'class="item-cell...' -- the very first pass
# at this early in the project used a regex that required the class
# attribute to be *exactly* "item-cell", so it silently skipped every
# sub-item, which carries an extra "sub" class -- 16 of the 32 items
# were never mapped at all until this rebuild).
#
# Insertion order above matches the frontend's DOM order exactly, since
# fill_cpl_pump zips this dict's keys positionally against the arrays
# the frontend submits (cplCondition[], cplAfter[], etc.) -- if this
# order ever drifts from the HTML again, every array-based field shifts
# silently. Re-verify with:
#   grep -oP 'class="item-cell[^"]*">[^<]*' pages/report-form.html

# Bearing Housing's Condition/Action/Remark/Good/Bad cells are merged
# across ALL FOUR of its rows (16:19) as one shared block -- only the
# top-left cell (row 16) of a merge actually displays a value in Excel/
# Calc, so those columns must always target row 16 regardless of which
# of the 5 Bearing Housing items was filled in. Only the After/Before
# reading itself differs per angle, using each item's own row.
CPL_PUMP_SHARED_TEXT_ROW_OVERRIDE = {
    "Bearing Housing - DE (0°-180°, Atas-Bawah)": 16,
    "Bearing Housing - DE (90°-270°)": 16,
    "Bearing Housing - NDE (0°-180°, Atas-Bawah)": 16,
    "Bearing Housing - NDE (90°-270°)": 16,
}

# Gland Packing/Stuffing Box: the Condition column's merge (K33:N36)
# starts one row ABOVE the Good/Bad/Action/Remark merges (which start at
# 34) -- an inconsistency in the sheet's own layout, not something to
# "fix" by picking one row for everything. Condition specifically must
# target row 33 (its merge's real top-left) or the text won't display.
CPL_PUMP_CONDITION_ROW_OVERRIDE = {
    "Gland Packing / Stuffing Box": 33,
}

# Coupling alignment table (rows 63-67) -- unchanged, see the previous
# analysis notes: frontend labels it "Pulley" but it's really Coupling's
# Round/Face table; values get written as "0°:1.2" into the existing
# angle-label cell (no separate blank cell exists for the reading).
ALIGN_ROWS = {"0": 64, "90": 65, "180": 66, "270": 67}
ALIGN_CELLS = {
    "alignRimAfter": "O",
    "alignFaceAfter": "Q",
    "alignRimBefore": "T",
    "alignFaceBefore": "V",
}

# AUTO DARI ISI DATA cells with no working formula link -- see flagged
# issue #2 above.
AUTO_SHEET = "xl/worksheets/sheet3.xml"
AUTO_DIRECT_CELLS = {
    "inspectorName": "N10",
}

# ---- BUKTI FOTO sheet: unchanged -----------------------------------------
BUKTI_FOTO_SLOTS = {
    "before": {"row": 9, "note_cell": "X9", "anchor_col": 1, "anchor_row": 8},
    "after": {"row": 29, "note_cell": "X29", "anchor_col": 1, "anchor_row": 28},
    "additional": {"row": 49, "note_cell": "X49", "anchor_col": 1, "anchor_row": 48},
}
