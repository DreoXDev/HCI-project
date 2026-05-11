from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..config import resolve_path


class PdfExportError(RuntimeError):
    """Raised when a PPTX cannot be exported to PDF."""


@dataclass(frozen=True)
class PdfExportResult:
    pptx_path: Path
    pdf_path: Path
    executable: Path


def find_libreoffice() -> Path | None:
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return Path(found)
    for candidate in (
        Path("C:/Program Files/LibreOffice/program/soffice.exe"),
        Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe"),
    ):
        if candidate.exists():
            return candidate
    return None


def export_pptx_to_pdf(pptx_path: str | Path, output_dir: str | Path | None = None) -> PdfExportResult:
    pptx = resolve_path(pptx_path)
    if not pptx.exists():
        raise PdfExportError(f"Presentazione PPTX non trovata: {pptx}")
    executable = find_libreoffice()
    if executable is None:
        raise PdfExportError(
            "LibreOffice non trovato. Installa LibreOffice e verifica che `soffice` o `libreoffice` sia accessibile dal PATH."
        )
    out_dir = resolve_path(output_dir) if output_dir else pptx.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    command = [
        str(executable),
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(pptx),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    if completed.returncode != 0:
        raise PdfExportError(
            "Export PDF fallito con LibreOffice.\n"
            f"Comando: {' '.join(command)}\n"
            f"Output: {completed.stdout.strip()}\n"
            f"Errore: {completed.stderr.strip()}"
        )
    pdf = out_dir / f"{pptx.stem}.pdf"
    if not pdf.exists():
        raise PdfExportError(f"LibreOffice non ha prodotto il PDF atteso: {pdf}")
    return PdfExportResult(pptx_path=pptx, pdf_path=pdf, executable=executable)

