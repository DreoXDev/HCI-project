from __future__ import annotations

from ..config import resolve_path
from .asset_export import export_slide_assets


def generate_slide_manifest() -> None:
    assets = export_slide_assets()
    manifest = resolve_path("outputs/slide_manifest.md")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Slide Manifest",
        "",
        "## 1. Introduzione",
        "- Testo: `outputs/text_snippets/intro.md`",
        "- Sezione report: `outputs/generated_report_sections/01_introduzione.md`",
        "",
        "## 2. Valutazione euristica",
        "- Testo: `outputs/text_snippets/heuristics.md`",
        "- Grafici/tabelle: `outputs/slide_assets/02_heuristics/`",
        "",
        "## 3. User Test",
        "- Testo: `outputs/text_snippets/user_tests.md`",
        "- Grafici: `outputs/slide_assets/03_user_tests/`",
        "",
        "## 4. Questionario UEQ e NPS",
        "- Testo: `outputs/text_snippets/questionnaire.md`",
        "- NPS: `outputs/text_snippets/nps.md`",
        "- Grafici: `outputs/slide_assets/04_questionnaire/`",
        "",
        "## 5. Conclusioni",
        "- Testo: `outputs/text_snippets/conclusions.md`",
        "- Sintesi: `outputs/slide_assets/05_conclusions/`",
        "",
        "## Asset copiati",
        *[f"- `{asset}`" for asset in assets],
        "",
        "## Note",
        "- Se un asset non compare, significa che il dato corrispondente manca o non e stato generato.",
        "- Le euristiche importate da Formbricks possono richiedere consolidamento manuale prima dell'analisi finale.",
    ]
    manifest.write_text("\n".join(lines), encoding="utf-8")
