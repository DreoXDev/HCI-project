from __future__ import annotations

from collections import Counter

import pandas as pd


HEURISTIC_CATEGORIES = {
    "E1": "Percezione",
    "E2": "Cognizione",
    "E3": "Errori",
    "E4": "Cognizione",
    "E5": "Errori",
    "E6": "Cognizione",
    "E7": "Cognizione",
    "E8": "Percezione",
    "E9": "Errori",
    "E10": "Cognizione",
}


def clean_heuristics(df: pd.DataFrame, system: str) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["system"] = system
    expert_columns = [column for column in cleaned.columns if str(column).startswith("Expert")]
    cleaned[expert_columns] = cleaned[expert_columns].apply(pd.to_numeric, errors="coerce")
    cleaned["severity_mean"] = cleaned[expert_columns].mean(axis=1)
    cleaned["severity_median"] = cleaned[expert_columns].median(axis=1)
    cleaned["evaluator_count"] = cleaned["Id valutatori"].fillna("").astype(str).apply(lambda x: len([p for p in x.split("-") if p]))
    cleaned["priority_score"] = cleaned["severity_mean"] * cleaned["evaluator_count"]
    return cleaned


def summarize_heuristics(df1: pd.DataFrame, df2: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    combined = pd.concat([clean_heuristics(df1, systems[0]), clean_heuristics(df2, systems[1])], ignore_index=True)
    summary = (
        combined.groupby("system")
        .agg(
            problems=("Problema", "count"),
            severity_mean=("severity_mean", "mean"),
            severity_median=("severity_median", "median"),
            priority_mean=("priority_score", "mean"),
        )
        .reset_index()
    )
    counts = []
    for _, row in combined.iterrows():
        for heuristic in str(row["Euristiche"]).split("-"):
            if heuristic:
                counts.append({"system": row["system"], "heuristic": heuristic, "category": HEURISTIC_CATEGORIES.get(heuristic, "Altro")})
    distribution = pd.DataFrame(counts)
    category_distribution = distribution.groupby(["system", "category"]).size().reset_index(name="count")
    heuristic_distribution = distribution.groupby(["system", "heuristic"]).size().reset_index(name="count")
    return summary, heuristic_distribution, category_distribution


def priority_table(df: pd.DataFrame) -> pd.DataFrame:
    columns = ["system", "Problem ID", "Problema", "severity_mean", "severity_median", "evaluator_count", "priority_score"]
    return df[[column for column in columns if column in df.columns]].sort_values("priority_score", ascending=False)


def evaluator_matrix(df: pd.DataFrame) -> pd.DataFrame:
    counter: Counter[str] = Counter()
    for ids in df["Id valutatori"].fillna("").astype(str):
        counter.update([item for item in ids.split("-") if item])
    return pd.DataFrame(counter.items(), columns=["evaluator", "problems_found"]).sort_values("evaluator")
