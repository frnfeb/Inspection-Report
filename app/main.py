from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .fill_workbook import fill_workbook
from .filename import build_filename
from .libreoffice_runner import recalculate_and_export
from .models import ReportPayload
from .photos_xml import insert_photos

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "template" / "V2.xlsx"
JOBS_DIR = BASE_DIR / "jobs"
JOBS_DIR.mkdir(exist_ok=True)
STATIC_DIR = BASE_DIR / "static"

PRINT_SHEETS = ["AUTO DARI ISI DATA", "CPL PUMP", "BUKTI FOTO"]

app = FastAPI(title="Inspection Report by FRNFEB - backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_jobs: dict[str, dict[str, Path]] = {}


@app.post("/api/generate")
def generate_report(payload: ReportPayload):
    data = payload.as_dict()
    job_id = uuid.uuid4().hex
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    filled_path = job_dir / "filled.xlsx"
    cached_path = job_dir / "cached.xlsx"
    pdf_path = job_dir / "report.pdf"

    try:
        # 1) raw XML surgery: ISI DATA + CPL PUMP + cause checkboxes
        fill_workbook(TEMPLATE_PATH, data, filled_path)

        # 2) photos, raw XML into drawing5.xml (BUKTI FOTO)
        photos = {
            "before": data.get("photoBefore"),
            "after": data.get("photoAfter"),
            "additional": data.get("photoAdditional"),
        }
        insert_photos(filled_path, photos)

        # 3) LibreOffice: recalculate formulas, export the 3-page PDF, and
        #    save the deliverable xlsx with formulas cached to values and
        #    helper sheets removed.
        recalculate_and_export(
            in_xlsx=filled_path,
            out_xlsx=cached_path,
            out_pdf=pdf_path,
            visible_sheets=PRINT_SHEETS,
            remove_helper_sheets=False,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}") from exc

    filename_base = build_filename(data)
    _jobs[job_id] = {
        "xlsx": cached_path,
        "pdf": pdf_path,
        "filename": filename_base,
    }
    return {"job_id": job_id, "filename": filename_base}


@app.get("/api/download/{job_id}/xlsx")
def download_xlsx(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return FileResponse(
        job["xlsx"],
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{job['filename']}.xlsx",
    )


@app.get("/api/download/{job_id}/pdf")
def download_pdf(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return FileResponse(
        job["pdf"],
        media_type="application/pdf",
        filename=f"{job['filename']}.pdf",
    )


@app.delete("/api/job/{job_id}")
def cleanup_job(job_id: str):
    job_dir = JOBS_DIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir, ignore_errors=True)
    _jobs.pop(job_id, None)
    return {"deleted": True}


# Serve the frontend (mounted LAST so it never shadows the /api/* routes
# above -- Starlette matches routes in registration order). This lets
# the whole app -- form + backend -- be deployed as a single service,
# no separate static host needed.
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
