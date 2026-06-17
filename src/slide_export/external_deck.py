from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from ..config import resolve_path
from .pdf_export import PdfExportError, export_pptx_to_pdf


class ExternalDeckImportError(RuntimeError):
    """Raised when an external deck cannot be rendered for report insertion."""


def user_task_deck_slide_specs(auto: dict[str, Any]) -> list[dict[str, Any]]:
    """Render the curated user-task deck and expose each page as a full slide."""

    source = auto.get("user_task_deck_source")
    if not source:
        return []
    images = render_user_task_deck_images(
        source,
        source_pdf=auto.get("user_task_deck_pdf"),
        output_dir=auto.get("user_task_deck_render_dir") or "outputs/slide_assets/imported_user_task_deck",
    )
    return [{"template_id": "full_slide_image", "image": _rel(path), "title": f"User task deck {idx:02d}"} for idx, path in enumerate(images, start=1)]


def render_user_task_deck_images(
    source_pptx: str | Path,
    *,
    source_pdf: str | Path | None = None,
    output_dir: str | Path = "outputs/slide_assets/imported_user_task_deck",
) -> list[Path]:
    pptx = resolve_path(source_pptx)
    if not pptx.exists():
        raise ExternalDeckImportError(f"User task deck non trovato: {pptx}")

    pdf = _pdf_for_deck(pptx, source_pdf)
    out_dir = resolve_path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("slide_*.png"):
        old.unlink()

    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise ExternalDeckImportError("pdftoppm non trovato: impossibile renderizzare il deck utente in immagini.")

    prefix = out_dir / "slide"
    command = [pdftoppm, "-png", "-r", "160", str(pdf), str(prefix)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    if completed.returncode != 0:
        raise ExternalDeckImportError(
            "Rendering del deck utente fallito.\n"
            f"Comando: {' '.join(command)}\n"
            f"Output: {completed.stdout.strip()}\n"
            f"Errore: {completed.stderr.strip()}"
        )

    rendered = sorted(out_dir.glob("slide-*.png"))
    final_paths: list[Path] = []
    for idx, path in enumerate(rendered, start=1):
        target = out_dir / f"slide_{idx:02d}.png"
        path.replace(target)
        final_paths.append(target)
    if not final_paths:
        raise ExternalDeckImportError(f"Nessuna immagine generata dal PDF: {pdf}")
    return final_paths


def _pdf_for_deck(pptx: Path, source_pdf: str | Path | None) -> Path:
    if source_pdf:
        pdf = resolve_path(source_pdf)
        if not pdf.exists():
            raise ExternalDeckImportError(f"PDF del deck utente non trovato: {pdf}")
        return pdf

    sidecar = pptx.with_suffix(".pdf")
    if sidecar.exists():
        return sidecar

    try:
        return export_pptx_to_pdf(pptx, output_dir=pptx.parent).pdf_path
    except PdfExportError as exc:
        raise ExternalDeckImportError(
            "Non riesco a ottenere il PDF del deck utente. Fornisci `user_task_deck_pdf` nella configurazione "
            "oppure installa LibreOffice per convertire il PPTX automaticamente."
        ) from exc


def _rel(path: Path) -> str:
    try:
        return path.relative_to(resolve_path(".")).as_posix()
    except ValueError:
        return str(path)
