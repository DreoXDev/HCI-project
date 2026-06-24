from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.analysis.ueq_benchmark import (
    PROJECT_BENCHMARK_SNAPSHOT,
    UEQ_INTERNAL_SCALE_ORDER,
    check_project_benchmark_snapshot,
    classify_ueq_benchmark,
    thresholds_dataframe,
)


def test_ueq_benchmark_threshold_boundaries() -> None:
    assert classify_ueq_benchmark("Attrattività", 0.68) == "Bad"
    assert classify_ueq_benchmark("Attrattività", 0.69) == "Below Average"
    assert classify_ueq_benchmark("Attrattività", 1.18) == "Above Average"
    assert classify_ueq_benchmark("Attrattività", 1.58) == "Good"
    assert classify_ueq_benchmark("Attrattività", 1.84) == "Excellent"


def test_ueq_benchmark_scale_specific_boundaries() -> None:
    assert classify_ueq_benchmark("Originalità", 0.15) == "Bad"
    assert classify_ueq_benchmark("Originalità", 0.16) == "Below Average"
    assert classify_ueq_benchmark("Originalità", 0.70) == "Above Average"
    assert classify_ueq_benchmark("Stimolazione", 0.33) == "Bad"
    assert classify_ueq_benchmark("Stimolazione", 0.50) == "Below Average"
    assert classify_ueq_benchmark("Controllabilità", 1.14) == "Above Average"
    assert classify_ueq_benchmark("Dependability", 1.70) == "Excellent"


def test_ueq_benchmark_thresholds_are_not_uniform() -> None:
    thresholds = thresholds_dataframe()
    assert thresholds["bad_upper"].nunique() > 1
    novelty = thresholds[thresholds["scale"] == "Originalità"].iloc[0]
    attractiveness = thresholds[thresholds["scale"] == "Attrattività"].iloc[0]
    assert novelty["bad_upper"] < attractiveness["bad_upper"]


def test_project_ueq_benchmark_classification_snapshot() -> None:
    path = Path("outputs/tables/ueq/ueq_benchmark_by_scale_app.csv")
    if not path.exists():
        pytest.skip("UEQ benchmark output not generated")
    table = pd.read_csv(path)
    checks = check_project_benchmark_snapshot(table)
    assert checks
    assert all(check.ok for check in checks), [(check.app, check.scale, check.mean, check.category, check.expected_mean, check.expected_category) for check in checks if not check.ok]
    assert len(checks) == len(PROJECT_BENCHMARK_SNAPSHOT)


def test_project_ueq_scale_outputs_are_complete_and_in_range() -> None:
    scale_path = Path("outputs/tables/ueq_scale_descriptives.csv")
    response_path = Path("outputs/tables/ueq/ueq_transformed_responses.csv")
    if not scale_path.exists() or not response_path.exists():
        pytest.skip("UEQ outputs not generated")
    scale_desc = pd.read_csv(scale_path)
    responses = pd.read_csv(response_path)

    assert scale_desc["mean"].between(-3, 3).all()
    for app in ["Deliveroo", "Glovo"]:
        app_scales = set(scale_desc[scale_desc["app"] == app]["scale"])
        assert app_scales == set(UEQ_INTERNAL_SCALE_ORDER)
        assert set(responses[responses["app"] == app]["item_id"]) == {f"Q{i:02d}" for i in range(1, 27)}
        counts = responses[responses["app"] == app].groupby("item_id")["respondent_id"].nunique()
        assert counts.nunique() == 1
        assert counts.iloc[0] == 24
