from __future__ import annotations

from pathlib import Path


def test_quantitative_assets_exist_after_validation_script() -> None:
    required = [
        Path("outputs/charts/effectiveness_outcome_matrix.png"),
        Path("outputs/charts/efficiency_summary.png"),
        Path("outputs/charts/ueq_benchmark_comparison.png"),
        Path("outputs/validation/quantitative_report_validation.md"),
    ]
    assert all(path.exists() and path.stat().st_size > 0 for path in required)
