from __future__ import annotations

from pathlib import Path

from src.slide_export.slide_manifest import generate_slide_manifest


def test_generate_slide_manifest_creates_manifest() -> None:
    generate_slide_manifest()

    manifest = Path("outputs/slide_manifest.md")
    assert manifest.exists()
    assert "Slide Manifest" in manifest.read_text(encoding="utf-8")
