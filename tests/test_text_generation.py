from __future__ import annotations

from pathlib import Path

from src.config import load_config
from src.text_generation.final_summary_text import generate_text_outputs


def test_generate_text_outputs_creates_report_sections() -> None:
    config = load_config("config.yaml")

    generate_text_outputs(config)

    assert Path("outputs/text_snippets/intro.md").exists()
    assert Path("outputs/generated_report_sections/05_conclusioni.md").exists()
    assert "Deliveroo" in Path("outputs/text_snippets/intro.md").read_text(encoding="utf-8")
