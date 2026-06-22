from __future__ import annotations

from math import isnan
from typing import Iterable

import numpy as np
from scipy import stats


def _clean(values: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    return arr[~np.isnan(arr)]


def _paired_clean(x: Iterable[float], y: Iterable[float]) -> tuple[np.ndarray, np.ndarray]:
    left = np.asarray(list(x), dtype=float)
    right = np.asarray(list(y), dtype=float)
    mask = ~(np.isnan(left) | np.isnan(right))
    return left[mask], right[mask]


def _flag(p_value: float | None) -> str:
    if p_value is None or np.isnan(p_value):
        return "not_applicable"
    return "significant" if p_value < 0.05 else "not_significant"


def compute_descriptives(values: Iterable[float]) -> dict[str, float | int]:
    raw = np.asarray(list(values), dtype=float)
    clean = raw[~np.isnan(raw)]
    if clean.size == 0:
        return {
            "n": 0,
            "mean": np.nan,
            "median": np.nan,
            "std": np.nan,
            "min": np.nan,
            "q1": np.nan,
            "q3": np.nan,
            "max": np.nan,
            "missing_count": int(np.isnan(raw).sum()),
        }
    return {
        "n": int(clean.size),
        "mean": float(np.mean(clean)),
        "median": float(np.median(clean)),
        "std": float(np.std(clean, ddof=1)) if clean.size > 1 else 0.0,
        "min": float(np.min(clean)),
        "q1": float(np.quantile(clean, 0.25)),
        "q3": float(np.quantile(clean, 0.75)),
        "max": float(np.max(clean)),
        "missing_count": int(np.isnan(raw).sum()),
    }


def cohens_d_paired(x: Iterable[float], y: Iterable[float]) -> float:
    left, right = _paired_clean(x, y)
    if left.size < 2:
        return np.nan
    diff = right - left
    sd = np.std(diff, ddof=1)
    return float(np.mean(diff) / sd) if sd else np.nan


def rank_biserial_from_wilcoxon(x: Iterable[float], y: Iterable[float]) -> float:
    left, right = _paired_clean(x, y)
    diff = right - left
    diff = diff[diff != 0]
    if diff.size == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(diff))
    positive = ranks[diff > 0].sum()
    negative = ranks[diff < 0].sum()
    denom = positive + negative
    return float((positive - negative) / denom) if denom else np.nan


def odds_ratio_2x2(table_2x2: Iterable[Iterable[int]]) -> float:
    table = np.asarray(list(table_2x2), dtype=float)
    if table.shape != (2, 2):
        return np.nan
    a, b, c, d = table.flatten()
    if b * c == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    return float((a * d) / (b * c))


def paired_t_test(x: Iterable[float], y: Iterable[float]) -> dict[str, float | int | str]:
    left, right = _paired_clean(x, y)
    if left.size < 2:
        return _result("Paired t-test", np.nan, np.nan, np.nan, "Cohen's dz", int(left.size), "insufficient paired data")
    test = stats.ttest_rel(left, right, nan_policy="omit")
    effect = cohens_d_paired(left, right)
    return _result("Paired t-test", float(test.statistic), float(test.pvalue), effect, "Cohen's dz", int(left.size), "")


def wilcoxon_signed_rank(x: Iterable[float], y: Iterable[float]) -> dict[str, float | int | str]:
    left, right = _paired_clean(x, y)
    if left.size < 2:
        return _result("Wilcoxon signed-rank", np.nan, np.nan, np.nan, "rank-biserial r", int(left.size), "insufficient paired data")
    if np.allclose(left, right, equal_nan=False):
        return _result("Wilcoxon signed-rank", 0.0, 1.0, 0.0, "rank-biserial r", int(left.size), "all paired differences are zero")
    test = stats.wilcoxon(left, right, zero_method="wilcox", alternative="two-sided")
    effect = rank_biserial_from_wilcoxon(left, right)
    return _result("Wilcoxon signed-rank", float(test.statistic), float(test.pvalue), effect, "rank-biserial r", int(left.size), "")


def mcnemar_exact(table_2x2: Iterable[Iterable[int]]) -> dict[str, float | int | str]:
    table = np.asarray(list(table_2x2), dtype=int)
    if table.shape != (2, 2):
        return _result("McNemar exact", np.nan, np.nan, np.nan, "discordant odds ratio", 0, "invalid 2x2 table")
    b = int(table[0, 1])
    c = int(table[1, 0])
    n = int(table.sum())
    if b + c == 0:
        return _result("McNemar exact", 0.0, 1.0, 1.0, "discordant odds ratio", n, "no discordant pairs")
    p_value = stats.binomtest(min(b, c), b + c, 0.5, alternative="two-sided").pvalue
    effect = (b + 0.5) / (c + 0.5)
    return _result("McNemar exact", float(min(b, c)), float(p_value), float(effect), "discordant odds ratio", n, "")


def fisher_exact_2x2(table_2x2: Iterable[Iterable[int]]) -> dict[str, float | int | str]:
    table = np.asarray(list(table_2x2), dtype=int)
    if table.shape != (2, 2):
        return _result("Fisher exact", np.nan, np.nan, np.nan, "odds ratio", 0, "invalid 2x2 table")
    odds_ratio, p_value = stats.fisher_exact(table, alternative="two-sided")
    return _result("Fisher exact", float(odds_ratio), float(p_value), odds_ratio_2x2(table), "odds ratio", int(table.sum()), "")


def one_sample_test_against_threshold(values: Iterable[float], threshold: float) -> dict[str, float | int | str]:
    clean = _clean(values)
    if clean.size < 2:
        return _result("One-sample Wilcoxon", np.nan, np.nan, np.nan, "median delta", int(clean.size), "insufficient data")
    diff = clean - threshold
    if np.allclose(diff, 0):
        return _result("One-sample Wilcoxon", 0.0, 1.0, 0.0, "median delta", int(clean.size), "all values equal threshold")
    test = stats.wilcoxon(diff)
    return _result("One-sample Wilcoxon", float(test.statistic), float(test.pvalue), float(np.median(diff)), "median delta", int(clean.size), "")


def bootstrap_ci_mean(values: Iterable[float], n_boot: int = 10000, ci: float = 0.95) -> tuple[float, float]:
    clean = _clean(values)
    if clean.size == 0:
        return (np.nan, np.nan)
    rng = np.random.default_rng(20260622)
    means = rng.choice(clean, size=(n_boot, clean.size), replace=True).mean(axis=1)
    alpha = (1 - ci) / 2
    return (float(np.quantile(means, alpha)), float(np.quantile(means, 1 - alpha)))


def choose_paired_time_test(x: Iterable[float], y: Iterable[float]) -> dict[str, float | int | str]:
    left, right = _paired_clean(x, y)
    if left.size < 3:
        return wilcoxon_signed_rank(left, right)
    diff = right - left
    normal_p = stats.shapiro(diff).pvalue if left.size <= 5000 and not np.allclose(diff, diff[0]) else 0.0
    result = paired_t_test(left, right) if normal_p >= 0.05 else wilcoxon_signed_rank(left, right)
    result["notes"] = f"Shapiro-Wilk p on paired differences = {normal_p:.4f}"
    return result


def _result(
    test_name: str,
    statistic: float,
    p_value: float,
    effect_size: float,
    effect_size_name: str,
    n: int,
    notes: str,
) -> dict[str, float | int | str]:
    p = None if p_value is None or (isinstance(p_value, float) and isnan(p_value)) else float(p_value)
    return {
        "test_name": test_name,
        "statistic": statistic,
        "p_value": np.nan if p is None else p,
        "effect_size": effect_size,
        "effect_size_name": effect_size_name,
        "n": n,
        "interpretation_flag": _flag(p),
        "notes": notes,
    }

