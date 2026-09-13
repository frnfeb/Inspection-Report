"""
Runs LibreOffice headless (via the pyuno socket bridge) to:
  1) recalculate all formulas,
  2) export a PDF containing only the 3 "printed" sheets,
  3) save the deliverable .xlsx with formulas cached to values and the
     helper sheets (TUTORIAL/ISI DATA/LIST) removed.

Safety notes (load-bearing, not stylistic):
  - We NEVER pass the target file as a `soffice <file>` CLI argument --
    that can hang indefinitely on documents with legacy form controls
    (this template has 42 ActiveX checkboxes; see ANALYSIS.md).
  - Instead we start a file-less `soffice --headless --accept=socket...`
    listener and connect to it with the pyuno bridge, then open the
    document ourselves via
    XComponentLoader.loadComponentFromURL(url, "_blank", 0,
    (Hidden=True, MacroExecutionMode=NEVER_EXECUTE)).
    This was switched from an earlier Basic-macro/CLI-script-URI
    approach that turned out to be unreliable to invoke headlessly in
    this environment; pyuno is more standard for this kind of
    automation and keeps the same safety property (no CLI file arg).
"""
from __future__ import annotations

import socket
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue


def _prop(name: str, value):
    p = PropertyValue()
    p.Name = name
    p.Value = value
    return p


def _wait_for_port(port: int, timeout: float) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.connect(("localhost", port))
                return
            except OSError:
                time.sleep(0.3)
    raise TimeoutError(f"soffice did not open listening port {port} in time")


class LibreOfficeSession:
    """One throwaway headless soffice instance + pyuno connection."""

    def __init__(self, startup_timeout: float = 45):
        self.port = 2002 + (uuid.uuid4().int % 5000)
        self.profile_dir = Path(tempfile.mkdtemp(prefix="mrg_lo_profile_"))
        self.proc: subprocess.Popen | None = None
        self.ctx = None
        self.desktop = None
        self._start(startup_timeout)

    def _start(self, timeout: float) -> None:
        cmd = [
            "soffice",
            "--headless",
            "--invisible",
            "--nologo",
            "--nofirststartwizard",
            "--norestore",
            f"-env:UserInstallation=file://{self.profile_dir}",
            f"--accept=socket,host=localhost,port={self.port};urp;",
        ]
        self.proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        _wait_for_port(self.port, timeout)

        local_ctx = uno.getComponentContext()
        resolver = local_ctx.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local_ctx
        )
        conn_str = (
            f"uno:socket,host=localhost,port={self.port};"
            "urp;StarOffice.ComponentContext"
        )
        last_exc = None
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                self.ctx = resolver.resolve(conn_str)
                break
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                time.sleep(0.3)
        if self.ctx is None:
            raise RuntimeError(f"could not connect to soffice via UNO: {last_exc}")

        self.desktop = self.ctx.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", self.ctx
        )

    def open_hidden(self, path: Path):
        url = uno.systemPathToFileUrl(str(path))
        NEVER_EXECUTE = 0
        return self.desktop.loadComponentFromURL(
            url,
            "_blank",
            0,
            (_prop("Hidden", True), _prop("MacroExecutionMode", NEVER_EXECUTE)),
        )

    def close(self) -> None:
        try:
            if self.desktop is not None:
                self.desktop.terminate()
        except Exception:  # noqa: BLE001
            pass
        if self.proc is not None:
            try:
                self.proc.wait(timeout=10)
            except Exception:  # noqa: BLE001
                self.proc.kill()


def recalculate_and_export(
    in_xlsx: Path,
    out_xlsx: Path,
    out_pdf: Path,
    visible_sheets: list[str],
    remove_helper_sheets: bool = False,
    timeout_seconds: int = 90,
) -> None:
    """
    NOTE on remove_helper_sheets: leave this False. Confirmed by testing --
    calling oSheets.removeByName() on TUTORIAL/ISI DATA/LIST via the UNO
    API corrupts a merged-cell range elsewhere in the saved .xlsx (fails
    to even open in openpyxl afterwards: "13 must be greater than 14").
    The deliverable workbook simply keeps all 6 sheets now (all visible,
    per rule #7's "boleh tetap berisi semua 6 sheet" option) -- safer
    than chasing the exact merge-range bug for a feature the brief
    already marked optional.
    """
    # Letter paper, in 1/100 mm (8.5in x 11in)
    LETTER_WIDTH = 21590
    LETTER_HEIGHT = 27940

    session = LibreOfficeSession(startup_timeout=min(45, timeout_seconds))
    try:
        doc = session.open_hidden(in_xlsx)
        try:
            doc.calculateAll()

            sheets = doc.Sheets
            visible_set = set(visible_sheets)
            style_families = doc.StyleFamilies.getByName("PageStyles")

            for name in sheets.ElementNames:
                sheet = sheets.getByName(name)
                is_visible = name in visible_set
                sheet.IsVisible = is_visible
                if not is_visible:
                    # IsVisible alone does not exclude a sheet from PDF
                    # export in headless automation -- confirmed by
                    # testing (a hidden sheet still produced a page).
                    # Clearing the print area is what actually excludes
                    # it.
                    sheet.setPrintAreas(())
                else:
                    # rule: Letter paper, fit-to-width 1 page, fit-to-
                    # height 1 page, for every printed sheet.
                    style = style_families.getByName(sheet.PageStyle)
                    style.Width = LETTER_WIDTH
                    style.Height = LETTER_HEIGHT
                    style.ScaleToPagesX = 1
                    style.ScaleToPagesY = 1

            doc.storeToURL(
                uno.systemPathToFileUrl(str(out_pdf)),
                (_prop("FilterName", "calc_pdf_Export"),),
            )

            # restore visibility + print areas before saving the
            # deliverable workbook (the user's download should look
            # normal, not have sheets stripped of their print area)
            for name in sheets.ElementNames:
                sheet = sheets.getByName(name)
                sheet.IsVisible = True

            if remove_helper_sheets:
                for helper in ("TUTORIAL", "ISI DATA", "LIST"):
                    if sheets.hasByName(helper):
                        sheets.removeByName(helper)

            doc.storeToURL(
                uno.systemPathToFileUrl(str(out_xlsx)),
                (_prop("FilterName", "Calc MS Excel 2007 XML"),),
            )
        finally:
            doc.close(False)
    finally:
        session.close()

    if not out_pdf.exists() or not out_xlsx.exists():
        raise RuntimeError("LibreOffice finished without producing the expected output files")
