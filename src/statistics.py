from __future__ import annotations

import math

import numpy as np
from scipy import stats


def mean_ci_proportion(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float, float]:
    if total == 0:
        return (np.nan, np.nan, np.nan)
    p = successes / total
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    margin = z * math.sqrt((p * (1 - p)) / total)
    return p, max(0, p - margin), min(1, p + margin)


def gorilla_ttest(system_1: str, system_2: str, label: str, pvalue: float, mean_1: float, mean_2: float) -> str:
    if np.isnan(pvalue):
        return f"Il test per {label} non e calcolabile con i dati disponibili."
    if pvalue < 0.05:
        better = system_1 if mean_1 < mean_2 else system_2
        return (
            f"Il test evidenzia una differenza statisticamente significativa tra {system_1} e {system_2} "
            f"per {label} (p = {pvalue:.3f}), con {better} mediamente più rapido."
        )
    return (
        f"Il test non evidenzia una differenza statisticamente significativa tra {system_1} e {system_2} "
        f"per {label} (p = {pvalue:.3f})."
    )
