"""Request model for POST /api/generate.

Deliberately permissive (extra="allow", everything optional): the source
of truth for field names is the frontend's collectFormData() output, and
we'd rather accept an evolving frontend than 422 on fields we don't know
about yet. Fields we don't recognize are simply ignored by fill_workbook.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ReportPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    # Identification fields, used for the output filename
    tagNo: Optional[str] = None
    dateFinish: Optional[str] = None
    problemTitle: Optional[str] = None
    nama: Optional[str] = None

    # Everything else (30+ scalar fields, several arrays, photo data URLs)
    # flows through as extra fields and is looked up by key in
    # fill_workbook.py / photos_xml.py, so it is intentionally not
    # enumerated here field-by-field.

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()
