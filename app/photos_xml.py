"""
Adds the Before/After/Additional inspection photos to the BUKTI FOTO sheet
by patching xl/drawings/drawing5.xml (+ its .rels + new media entries)
directly -- no openpyxl involved, so the existing company-logo drawing and
every other part of the file stays byte-identical.

Anchoring: each photo slot in the template is a ~20-row-tall blank area
(rows 9-28 = slot 1, 29-48 = slot 2, 49-68 = slot 3) under columns B..W.
We anchor each picture as a twoCellAnchor spanning that same block so it
sits inside the printed cell instead of floating over neighbouring text.
"""
from __future__ import annotations

import base64
import io
import re
import zipfile
from pathlib import Path

from PIL import Image

from . import cell_map as cm

DRAWING = "xl/drawings/drawing5.xml"
DRAWING_RELS = "xl/drawings/_rels/drawing5.xml.rels"
CONTENT_TYPES = "[Content_Types].xml"

SLOT_ANCHOR = {
    "before": (0, 8, 22, 27),      # (from_col, from_row, to_col, to_row) 0-indexed
    "after": (0, 28, 22, 47),
    "additional": (0, 48, 22, 67),
}


def _decode_data_url(data_url: str) -> tuple[bytes, str]:
    """Returns (jpeg_bytes, 'jpeg'). Always normalizes to JPEG so we only
    ever need the jpeg Default content-type entry, which the template
    already declares."""
    m = re.match(r"^data:image/[^;]+;base64,(.*)$", data_url, re.S)
    raw = base64.b64decode(m.group(1) if m else data_url)
    img = Image.open(io.BytesIO(raw))
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=87)
    return out.getvalue(), "jpeg"


def _pic_xml(rid: str, pic_id: int, name: str, anchor: tuple[int, int, int, int]) -> str:
    from_col, from_row, to_col, to_row = anchor
    return (
        f'<xdr:twoCellAnchor editAs="oneCell">'
        f"<xdr:from><xdr:col>{from_col}</xdr:col><xdr:colOff>19050</xdr:colOff>"
        f"<xdr:row>{from_row}</xdr:row><xdr:rowOff>19050</xdr:rowOff></xdr:from>"
        f"<xdr:to><xdr:col>{to_col}</xdr:col><xdr:colOff>0</xdr:colOff>"
        f"<xdr:row>{to_row}</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:to>"
        f"<xdr:pic><xdr:nvPicPr>"
        f'<xdr:cNvPr id="{pic_id}" name="{name}"/>'
        f'<xdr:cNvPicPr><a:picLocks noChangeAspect="1"/></xdr:cNvPicPr>'
        f"</xdr:nvPicPr>"
        f'<xdr:blipFill><a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="{rid}"/>'
        f"<a:stretch><a:fillRect/></a:stretch></xdr:blipFill>"
        f'<xdr:spPr bwMode="auto"><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></xdr:spPr>'
        f"</xdr:pic><xdr:clientData/></xdr:twoCellAnchor>"
    )


def insert_photos(xlsx_path: Path, photos: dict[str, str]) -> None:
    """photos: {'before': dataUrl, 'after': dataUrl, 'additional': dataUrl}
    (any subset; missing/empty entries are skipped)."""
    photos = {k: v for k, v in photos.items() if v}
    if not photos:
        return

    with zipfile.ZipFile(xlsx_path, "r") as zin:
        drawing_xml = zin.read(DRAWING).decode("utf-8")
        rels_xml = zin.read(DRAWING_RELS).decode("utf-8")
        existing_names = set(zin.namelist())

    # find next free media filename index
    existing_media = [n for n in existing_names if n.startswith("xl/media/image")]
    next_idx = 1
    nums = [int(re.search(r"(\d+)", n).group(1)) for n in existing_media if re.search(r"(\d+)", n)]
    if nums:
        next_idx = max(nums) + 1

    # find next free rId in the drawing's rels
    rid_nums = [int(m) for m in re.findall(r'Id="rId(\d+)"', rels_xml)]
    next_rid = (max(rid_nums) + 1) if rid_nums else 1
    # find next free shape id in the drawing (cNvPr id must be unique)
    id_nums = [int(m) for m in re.findall(r'<xdr:cNvPr id="(\d+)"', drawing_xml)]
    next_pic_id = (max(id_nums) + 1) if id_nums else 100

    new_media: dict[str, bytes] = {}
    new_rels_entries = []
    new_pic_entries = []

    for slot, data_url in photos.items():
        anchor = SLOT_ANCHOR.get(slot)
        if anchor is None:
            continue
        jpeg_bytes, ext = _decode_data_url(data_url)
        media_name = f"xl/media/image{next_idx}.{ext}"
        new_media[media_name] = jpeg_bytes

        rid = f"rId{next_rid}"
        new_rels_entries.append(
            f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
            f'Target="../media/image{next_idx}.{ext}"/>'
        )
        new_pic_entries.append(_pic_xml(rid, next_pic_id, f"Photo {slot}", anchor))

        next_idx += 1
        next_rid += 1
        next_pic_id += 1

    new_drawing_xml = drawing_xml.replace("</xdr:wsDr>", "".join(new_pic_entries) + "</xdr:wsDr>")
    new_rels_xml = rels_xml.replace("</Relationships>", "".join(new_rels_entries) + "</Relationships>")

    tmp_path = xlsx_path.with_suffix(".tmpphotos.xlsx")
    with zipfile.ZipFile(xlsx_path, "r") as zin, zipfile.ZipFile(
        tmp_path, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            if item.filename == DRAWING:
                data = new_drawing_xml.encode("utf-8")
            elif item.filename == DRAWING_RELS:
                data = new_rels_xml.encode("utf-8")
            else:
                data = zin.read(item.filename)
            zout.writestr(item, data)
        for name, data in new_media.items():
            zout.writestr(name, data)
    tmp_path.replace(xlsx_path)


def set_photo_notes(sheet, photos_notes: dict[str, str]) -> None:
    """Optional free-text note per photo slot (column X), via the same
    SheetXml object used for the rest of BUKTI FOTO if we ever add notes
    from the frontend. Currently the frontend doesn't collect per-photo
    notes, so this is unused but kept for completeness."""
    for slot, note in photos_notes.items():
        if not note:
            continue
        cell = cm.BUKTI_FOTO_SLOTS.get(slot, {}).get("note_cell")
        if cell:
            sheet.set_text(cell, note)
