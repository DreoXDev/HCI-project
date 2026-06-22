from __future__ import annotations

import numpy as np

from src.analysis.statistics import compute_descriptives, mcnemar_exact, wilcoxon_signed_rank


def test_compute_descriptives_counts_missing_values() -> None:
    result = compute_descriptives([1, 2, np.nan, 4])
    assert result["n"] == 3
    assert result["missing_count"] == 1
    assert result["median"] == 2


def test_mcnemar_exact_uses_discordant_pairs() -> None:
    result = mcnemar_exact([[10, 4], [0, 10]])
    assert result["test_name"] == "McNemar exact"
    assert result["n"] == 24
    assert result["p_value"] < 0.20


def test_wilcoxon_handles_all_zero_differences() -> None:
    result = wilcoxon_signed_rank([1, 2, 3], [1, 2, 3])
    assert result["p_value"] == 1.0
    assert result["interpretation_flag"] == "not_significant"

