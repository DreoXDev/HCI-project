from __future__ import annotations

import shutil
from pathlib import Path

from ..config import resolve_path


SLIDE_ASSETS = {
    "outputs/figures/heuristics/heuristics_distribution.png": "outputs/slide_assets/02_heuristics/slide_heuristics_distribution.png",
    "outputs/tables_md/problems_priority_table.md": "outputs/slide_assets/02_heuristics/slide_heuristics_priority_table.md",
    "outputs/figures/user_tests/effectiveness_deliveroo_vs_glovo.png": "outputs/slide_assets/03_user_tests/slide_user_test_effectiveness.png",
    "outputs/figures/user_tests/efficiency_boxplot.png": "outputs/slide_assets/03_user_tests/slide_efficiency_boxplot.png",
    "outputs/figures/questionnaire/ueq_scales.png": "outputs/slide_assets/04_questionnaire/slide_ueq_comparison.png",
    "outputs/figures/questionnaire/nps_comparison.png": "outputs/slide_assets/04_questionnaire/slide_nps_comparison.png",
    "outputs/tables_md/final_comparison.md": "outputs/slide_assets/05_conclusions/slide_final_score_card.md",
}


def export_slide_assets() -> list[str]:
    copied = []
    for source, destination in SLIDE_ASSETS.items():
        src = resolve_path(source)
        dst = resolve_path(destination)
        if not src.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(str(dst))
    return copied

