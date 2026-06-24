from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

import pytest


def _pptx_slide_texts(path: Path) -> list[str]:
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    with ZipFile(path) as deck:
        slides = sorted(
            [name for name in deck.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", name)],
            key=lambda name: int(re.search(r"slide(\d+)\.xml", name).group(1)),
        )
        texts = []
        for name in slides:
            root = ET.fromstring(deck.read(name))
            texts.append(" ".join(node.text or "" for node in root.findall(".//a:t", ns)))
    return texts


def test_final_deck_has_no_raw_ueq_mean_slide() -> None:
    pptx = Path("outputs/slides/final_report.pptx")
    if not pptx.exists():
        pytest.skip("final_report.pptx not generated")
    if pptx.stat().st_mtime < Path("src/slide_export/auto_deck.py").stat().st_mtime:
        pytest.skip("final_report.pptx predates slide generator changes")
    texts = _pptx_slide_texts(pptx)

    assert not any("Media risultati UEQ" in text for text in texts)
    assert any("UEQ - confronto sintetico delle scale" in text for text in texts)
    assert not any("UEQ benchmark - confronto sintetico" in text for text in texts)


def test_final_deck_uses_benchmark_only_for_official_categories() -> None:
    pptx = Path("outputs/slides/final_report.pptx")
    if not pptx.exists():
        pytest.skip("final_report.pptx not generated")
    if pptx.stat().st_mtime < Path("src/slide_export/auto_deck.py").stat().st_mtime:
        pytest.skip("final_report.pptx predates slide generator changes")
    texts = _pptx_slide_texts(pptx)

    official_category_terms = ("Bad", "Below Average", "Above Average", "Good", "Excellent")
    official_benchmark_slides = [text for text in texts if text.startswith("Benchmark UEQ - confronto sintetico")]
    assert official_benchmark_slides
    assert all(any(term in text for term in official_category_terms) for text in official_benchmark_slides)
