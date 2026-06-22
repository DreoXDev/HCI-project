from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .config import resolve_path
from .tables import export_table


PRIORITY_ORDER = {"A": 0, "B": 1, "C": 2, "unrated": 9, "": 9}


def generate_final_problem_tables(
    *,
    clean_problems_path: str | Path = "data/processed/heuristics/clean_problems.csv",
    severity_summary_path: str | Path = "data/processed/heuristics/problem_severity_summary.csv",
    output_dir: str | Path = "outputs/tables",
) -> list[Path]:
    clean_path = resolve_path(clean_problems_path)
    summary_path = resolve_path(severity_summary_path)
    if not clean_path.exists() or not summary_path.exists():
        return []
    clean = pd.read_csv(clean_path, encoding="utf-8-sig")
    summary = pd.read_csv(summary_path, encoding="utf-8-sig")
    final = build_final_problem_table(clean, summary)
    out = resolve_path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for app, suffix in [("Deliveroo", "deliveroo"), ("Glovo", "glovo")]:
        app_table = final[final["app"].astype(str).str.casefold() == app.casefold()].copy()
        full_path = out / f"final_problems_{suffix}.csv"
        slide_path = out / f"final_problems_{suffix}_slide.csv"
        app_table.to_csv(full_path, index=False, encoding="utf-8-sig")
        slide = app_table[
            ["problem_id", "title", "description", "heuristic", "severity_mean", "severity_median", "severity_std", "priority_band"]
        ].rename(
            columns={
                "problem_id": "ID",
                "title": "Titolo",
                "description": "Descrizione",
                "heuristic": "Euristiche",
                "severity_mean": "Severita media",
                "severity_median": "Severita mediana",
                "severity_std": "Dev. st.",
                "priority_band": "Priorita",
            }
        )
        slide.to_csv(slide_path, index=False, encoding="utf-8-sig")
        markdown_path = out / "markdown" / f"problems_{suffix}_by_severity.md"
        export_table(slide, markdown_path, 2)
        paths.extend([full_path, slide_path, markdown_path])
    return paths


def build_final_problem_table(clean: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    clean = clean.copy()
    summary = summary.copy()
    if "problem_id" not in clean or "problem_id" not in summary:
        return pd.DataFrame()
    for column in ["source_count", "notes"]:
        if column not in clean:
            clean[column] = ""
    metric_columns = ["problem_id", "mean_severity", "median_severity", "std_severity", "ratings_count"]
    metrics = summary[[column for column in metric_columns if column in summary.columns]].copy()
    merged = clean.merge(metrics, on="problem_id", how="left")
    merged["severity_mean"] = pd.to_numeric(merged["mean_severity"], errors="coerce").round(2)
    merged["severity_median"] = pd.to_numeric(merged.get("median_severity"), errors="coerce").round(2)
    merged["severity_std"] = pd.to_numeric(merged.get("std_severity"), errors="coerce").fillna(0).round(2)
    merged["priority_band"] = merged["severity_mean"].map(_priority_band)
    merged["priority_rank"] = merged["priority_band"].map(PRIORITY_ORDER).fillna(9).astype(int)
    merged["source_count_sort"] = pd.to_numeric(merged.get("source_count", 0), errors="coerce").fillna(0)
    merged = merged.sort_values(
        ["app", "priority_rank", "severity_mean", "severity_median", "severity_std", "problem_id"],
        ascending=[True, True, False, False, False, True],
        kind="mergesort",
    )
    columns = [
        "problem_id",
        "app",
        "title",
        "description",
        "heuristic",
        "source_count",
        "notes",
        "severity_mean",
        "severity_median",
        "severity_std",
        "ratings_count",
        "priority_band",
        "priority_rank",
    ]
    return merged[[column for column in columns if column in merged.columns]].copy()


def _priority_band(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "unrated"
    if pd.isna(number):
        return "unrated"
    if number >= 3.25:
        return "A"
    if number >= 2.0:
        return "B"
    return "C"
