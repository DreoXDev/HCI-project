from pathlib import Path

import pytest

from src.slide_export import pdf_export


def test_export_pdf_reports_missing_libreoffice(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pptx = tmp_path / "deck.pptx"
    pptx.write_bytes(b"fake")
    monkeypatch.setattr(pdf_export, "find_libreoffice", lambda: None)

    with pytest.raises(pdf_export.PdfExportError, match="LibreOffice non trovato"):
        pdf_export.export_pptx_to_pdf(pptx)


def test_export_pdf_requires_existing_pptx(tmp_path: Path) -> None:
    with pytest.raises(pdf_export.PdfExportError, match="PPTX non trovata"):
        pdf_export.export_pptx_to_pdf(tmp_path / "missing.pptx")

