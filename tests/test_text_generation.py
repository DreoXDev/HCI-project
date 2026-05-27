from __future__ import annotations

from pathlib import Path

from src.config import load_config
from src.text_generation.final_summary_text import generate_text_outputs


def test_generate_text_outputs_creates_snippets() -> None:
    config = load_config("config.yaml")

    generate_text_outputs(config)

    assert Path("outputs/texts/snippets/intro.md").exists()
    assert "Deliveroo" in Path("outputs/texts/snippets/intro.md").read_text(encoding="utf-8")

