from __future__ import annotations

from scripts.validate_quantitative_report import transform_ueq_raw_to_standard


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

