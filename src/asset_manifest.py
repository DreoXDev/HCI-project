from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import resolve_path


SECTION_RULES = [
    ("intro", "Introduzione", ["intro", "sample"]),
    ("heuristics", "Valutazione euristica", ["heuristic", "problem_evaluator", "coverage", "dark_patterns"]),
    ("user_tests", "User test", ["user_test", "users_time", "task_"]),
    ("questionnaire", "Questionario UEQ/NPS", ["ueq", "questionnaire", "nps", "subgroup"]),
    ("conclusions", "Conclusioni", ["final", "conclusion", "recommendation", "limitation", "executive"]),
]


def classify_asset(path: Path) -> tuple[str, str]:
    text = str(path).replace("\\", "/").lower()
    for section, title, needles in SECTION_RULES:
        if any(needle in text for needle in needles):
            return section, title
    return "general", "Asset generale"


def build_assets_manifest(output_path: str | Path = "outputs/slide_pack/assets_manifest.csv") -> pd.DataFrame:
    roots = [
        resolve_path("outputs/figures/dark"),
        resolve_path("outputs/figures/presentation"),
        resolve_path("outputs/tables_md"),
        resolve_path("outputs/text_snippets"),
    ]
    rows = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".png", ".svg", ".md", ".csv"}):
            section, slide_title = classify_asset(path)
            asset_type = "figure" if path.suffix.lower() in {".png", ".svg"} else "text" if "text_snippets" in str(path) else "table"
            priority = "high" if section in {"heuristics", "user_tests", "questionnaire", "conclusions"} else "medium"
            rows.append(
                {
                    "section": section,
                    "slide_title": slide_title,
                    "asset_type": asset_type,
                    "path": str(path.relative_to(resolve_path("."))).replace("\\", "/"),
                    "priority": priority,
                    "notes": "Asset pronto per slide/report; verificare interpretazione manuale.",
                }
            )
    df = pd.DataFrame(rows, columns=["section", "slide_title", "asset_type", "path", "priority", "notes"])
    target = resolve_path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target, index=False)
    return df
