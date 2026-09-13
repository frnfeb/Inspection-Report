from __future__ import annotations

import re


def _sanitize(part: str) -> str:
    part = part.strip()
    part = re.sub(r'[\\/:*?"<>|]', "_", part)
    part = re.sub(r"\s+", "_", part)
    return part or "_"


def build_filename(data: dict) -> str:
    tag_no = data.get("tagNo") or "TagNo"
    date_finish = data.get("dateFinish") or ""
    problem_title = data.get("problemTitle") or "Problem"
    nama = data.get("nama") or "Nama"

    year, month, day = "0000", "00", "00"
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", date_finish or "")
    if m:
        year, month, day = m.group(1), m.group(2), m.group(3)

    parts = [tag_no, year, month, day, problem_title, nama]
    return "_".join(_sanitize(p) for p in parts)
