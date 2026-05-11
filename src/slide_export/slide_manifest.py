from __future__ import annotations

import json

from ..config import resolve_path


def generate_slide_manifest() -> None:
    manifest = resolve_path("outputs/slide_manifest.md")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Slide Manifest",
        "",
        "## Uso Grafici",
        "- `outputs/figures/presentation/`: grafici senza sfondo.",
        "- `outputs/figures/clean/`: copia pulita dei grafici scuri per export/report.",
        "- `outputs/figures/dark/`: grafici con sfondo scuro.",
        "",
        "## 1. Introduzione",
        "- Testo: `outputs/text_snippets/intro.md`",
        "- Sezione report: `outputs/generated_report_sections/01_introduzione.md`",
        "",
        "## 2. Valutazione euristica",
        "- Testo: `outputs/text_snippets/heuristics.md`",
        "- Dark: `outputs/figures/dark/heuristics/heuristics_distribution.png`",
        "- Transparent: `outputs/figures/presentation/heuristics/heuristics_distribution.png`",
        "",
        "## 3. User Test",
        "- Testo: `outputs/text_snippets/user_tests.md`",
        "- Dark: `outputs/figures/dark/user_tests/effectiveness_deliveroo_vs_glovo.png`",
        "- Transparent: `outputs/figures/presentation/user_tests/effectiveness_deliveroo_vs_glovo.png`",
        "",
        "## User Test - Tempi, efficacia ed errori",
        "",
        "### Tabelle",
        "- `outputs/tables/users_time_summary.md`",
        "- `outputs/tables/users_time_stat_tests.csv`",
        "",
        "### Grafici",
        "- Dark: `outputs/figures/dark/users_time_mean_by_task.png`",
        "- Transparent: `outputs/figures/presentation/users_time_mean_by_task.png`",
        "- Dark: `outputs/figures/dark/users_time_boxplot_by_task.png`",
        "- Transparent: `outputs/figures/presentation/users_time_boxplot_by_task.png`",
        "- Dark: `outputs/figures/dark/users_time_success_rate.png`",
        "- Transparent: `outputs/figures/presentation/users_time_success_rate.png`",
        "- Dark: `outputs/figures/dark/users_time_errors_by_task.png`",
        "- Transparent: `outputs/figures/presentation/users_time_errors_by_task.png`",
        "",
        "### Testi pronti per slide",
        "- `outputs/text/users_time_interpretation.md`",
        "",
        "## 4. Questionario UEQ e NPS",
        "- Testo: `outputs/text_snippets/questionnaire.md`",
        "- NPS: `outputs/text_snippets/nps.md`",
        "- Dark: `outputs/figures/dark/questionnaire/ueq_scales.png`",
        "- Transparent: `outputs/figures/presentation/questionnaire/ueq_scales.png`",
        "",
        "## 5. Conclusioni",
        "- Testo: `outputs/text_snippets/conclusions.md`",
        "- Manifest asset: `outputs/slide_pack/assets_manifest.csv`",
        "",
        "## Note",
        "- Se un asset non compare, significa che il dato corrispondente manca o non e stato generato.",
        "- Le euristiche importate da Formbricks richiedono review manuale in `data/processed/heuristics/consolidated_problems.csv` prima della survey severita.",
    ]
    manifest.write_text("\n".join(lines), encoding="utf-8")
    manifest_json = resolve_path("outputs/slide_manifest.json")
    manifest_json.write_text(
        json.dumps(
            {
                "slides": [
                    {"slide_number": 1, "section": "Introduzione", "variant": "neutral", "text": ["outputs/text_snippets/intro.md"]},
                    {
                        "slide_number": 2,
                        "section": "Valutazione euristica",
                        "variant": "neutral",
                        "charts": [
                            "outputs/figures/clean/heuristics/heuristics_distribution.png",
                            "outputs/figures/presentation/heuristics/heuristics_distribution.png",
                        ],
                    },
                    {
                        "slide_number": 3,
                        "section": "User test",
                        "variant": "neutral",
                        "charts": [
                            "outputs/figures/clean/user_tests/effectiveness_deliveroo_vs_glovo.png",
                            "outputs/figures/presentation/user_tests/effectiveness_deliveroo_vs_glovo.png",
                        ],
                    },
                    {
                        "slide_number": 4,
                        "section": "Questionario UEQ e NPS",
                        "variant": "neutral",
                        "charts": [
                            "outputs/figures/clean/questionnaire/ueq_scales.png",
                            "outputs/figures/presentation/questionnaire/ueq_scales.png",
                        ],
                    },
                ],
                "warnings": [],
            },
            indent=2,
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    report = resolve_path("outputs/reports/slide_generation_report.md")
    report.parent.mkdir(parents=True, exist_ok=True)
    if not report.exists():
        report.write_text(
            "\n".join(
                [
                    "# Slide generation report",
                    "",
                    "- Manifest Markdown: `outputs/slide_manifest.md`",
                    "- Manifest JSON: `outputs/slide_manifest.json`",
                    "- Output PPTX: `outputs/slides/final_report.pptx`",
                    "",
                ]
            ),
            encoding="utf-8",
        )
