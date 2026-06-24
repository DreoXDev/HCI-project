from __future__ import annotations

import pytest

from scripts.validate_quantitative_report import transform_ueq_raw_to_standard, transform_ueq_response
from src.analysis.ueq_benchmark import classify_ueq_benchmark


def test_ueq_raw_to_standard_positive_right() -> None:
    cfg = {"reversed": False}
    assert transform_ueq_raw_to_standard(1, cfg) == -3
    assert transform_ueq_raw_to_standard(4, cfg) == 0
    assert transform_ueq_raw_to_standard(7, cfg) == 3


def test_ueq_raw_to_standard_positive_left() -> None:
    cfg = {"reversed": True}
    assert transform_ueq_raw_to_standard(1, cfg) == 3
    assert transform_ueq_raw_to_standard(4, cfg) == 0
    assert transform_ueq_raw_to_standard(7, cfg) == -3


def test_ueq_response_transform_uses_positive_side() -> None:
    assert transform_ueq_response(1, "right") == -3
    assert transform_ueq_response(4, "right") == 0
    assert transform_ueq_response(7, "right") == 3
    assert transform_ueq_response(1, "left") == 3
    assert transform_ueq_response(4, "left") == 0
    assert transform_ueq_response(7, "left") == -3


def test_ueq_response_transform_rejects_raw_values_outside_scale() -> None:
    with pytest.raises(ValueError, match="outside 1..7"):
        transform_ueq_response(8, "right")


def test_ueq_benchmark_classification_uses_scale_specific_thresholds() -> None:
    assert classify_ueq_benchmark("Attractiveness", 0.68) == "Bad"
    assert classify_ueq_benchmark("Attractiveness", 0.69) == "Below Average"
    assert classify_ueq_benchmark("Attractiveness", 1.18) == "Above Average"
    assert classify_ueq_benchmark("Attractiveness", 1.58) == "Good"
    assert classify_ueq_benchmark("Attractiveness", 1.84) == "Excellent"
    assert classify_ueq_benchmark("Novelty", 0.17) == "Below Average"
