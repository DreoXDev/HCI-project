from __future__ import annotations

import pandas as pd


UEQ_CATEGORIES = {
    "attrattivita": [0, 4, 5, 6, 11, 17],
    "apprendibilita": [3, 13, 16, 23],
    "efficienza": [8, 12, 19, 21],
    "controllabilita": [1, 10, 14, 18],
    "stimolazione": [2, 7, 15, 20],
    "originalita": [9, 22, 24, 25],
}


DEMOGRAPHIC_ROWS = {"genere", "eta", "situazione lavorativa", "istruzione"}


def numeric_items(df: pd.DataFrame) -> pd.DataFrame:
    rows = [idx for idx in df.index if idx not in DEMOGRAPHIC_ROWS and str(idx).upper() != "NPS"]
    return df.loc[rows].apply(pd.to_numeric, errors="coerce")


def item_summary(df: pd.DataFrame, system: str) -> pd.DataFrame:
    items = numeric_items(df)
    summary = pd.DataFrame(
        {
            "item": items.index,
            "mean": items.mean(axis=1),
            "median": items.median(axis=1),
            "std": items.std(axis=1),
            "min": items.min(axis=1),
            "max": items.max(axis=1),
        }
    )
    summary["system"] = system
    return summary


def ueq_summary(df: pd.DataFrame, system: str) -> pd.DataFrame:
    items = numeric_items(df)
    rows = []
    for category, indices in UEQ_CATEGORIES.items():
        available = [idx for idx in indices if idx < len(items)]
        values = items.iloc[available].stack() if available else pd.Series(dtype=float)
        rows.append({"system": system, "scale": category, "mean": values.mean(), "median": values.median(), "std": values.std()})
    return pd.DataFrame(rows)


def nps_summary(df: pd.DataFrame, system: str) -> pd.DataFrame:
    scores = pd.to_numeric(df.loc["NPS"], errors="coerce").dropna()
    detractors = int((scores <= 6).sum())
    passives = int(((scores >= 7) & (scores <= 8)).sum())
    promoters = int((scores >= 9).sum())
    total = len(scores)
    nps = ((promoters / total) - (detractors / total)) * 100 if total else 0
    return pd.DataFrame(
        [
            {
                "system": system,
                "detractors": detractors,
                "passives": passives,
                "promoters": promoters,
                "total": total,
                "nps": nps,
            }
        ]
    )


def subgroup_summary(df: pd.DataFrame, system: str, group_row: str = "situazione lavorativa") -> pd.DataFrame:
    if group_row not in df.index:
        return pd.DataFrame()
    items = numeric_items(df)
    user_groups = df.loc[group_row]
    user_scores = items.mean(axis=0).rename("ueq_mean").to_frame()
    user_scores[group_row] = user_groups
    result = user_scores.groupby(group_row)["ueq_mean"].agg(["count", "mean", "median", "std"]).reset_index()
    result["system"] = system
    return result
