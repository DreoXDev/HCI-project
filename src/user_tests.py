from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from scipy import stats

from .config import resolve_path
from .statistics import gorilla_ttest, mean_ci_proportion


TASK_VALUE_RE = re.compile(r"^(?P<minutes>\d+)\.(?P<seconds>\d{1,2})-(?P<status>[CAF])$")


def parse_task_value(value: str) -> tuple[int, str]:
    match = TASK_VALUE_RE.match(str(value))
    if not match:
        raise ValueError(f"Valore task non valido: {value}")
    return int(match.group("minutes")) * 60 + int(match.group("seconds")), match.group("status")


def add_parsed_task_columns(df: pd.DataFrame, systems: list[str]) -> pd.DataFrame:
    parsed = df.copy()
    for system in systems:
        for task in range(1, 4):
            column = f"Task {task} {system}"
            values = parsed[column].apply(parse_task_value)
            parsed[f"{column} seconds"] = values.apply(lambda item: item[0])
            parsed[f"{column} status"] = values.apply(lambda item: item[1])
    return parsed


def compute_effectiveness(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    parsed = add_parsed_task_columns(df, systems)
    rows = []
    for system in systems:
        for task in range(1, 4):
            statuses = parsed[f"Task {task} {system} status"]
            total = len(statuses)
            completed = int((statuses == "C").sum())
            helped = int((statuses == "A").sum())
            failed = int((statuses == "F").sum())
            p, low, high = mean_ci_proportion(completed, total)
            rows.append(
                {
                    "system": system,
                    "task": task,
                    "completed": completed,
                    "helped": helped,
                    "failed": failed,
                    "total": total,
                    "completion_rate": p,
                    "ci_low": low,
                    "ci_high": high,
                }
            )
    return pd.DataFrame(rows)


def compute_efficiency(df: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    parsed = add_parsed_task_columns(df, systems)
    long_rows = []
    summary_rows = []
    for system in systems:
        for task in range(1, 4):
            seconds = parsed[f"Task {task} {system} seconds"]
            long_rows.extend({"system": system, "task": task, "seconds": value} for value in seconds)
            summary_rows.append(
                {
                    "system": system,
                    "task": task,
                    "mean_seconds": seconds.mean(),
                    "median_seconds": seconds.median(),
                    "std_seconds": seconds.std(),
                    "min_seconds": seconds.min(),
                    "max_seconds": seconds.max(),
                }
            )
    long_columns = ["system", "task", "seconds"]
    summary_columns = ["system", "task", "mean_seconds", "median_seconds", "std_seconds", "min_seconds", "max_seconds"]
    return pd.DataFrame(long_rows, columns=long_columns), pd.DataFrame(summary_rows, columns=summary_columns)


def compute_user_test_statistics(df: pd.DataFrame, config: dict) -> list[str]:
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    parsed = add_parsed_task_columns(df, systems)
    snippets = []
    for task in range(1, 4):
        s1 = parsed[f"Task {task} {systems[0]} seconds"]
        s2 = parsed[f"Task {task} {systems[1]} seconds"]
        if len(s1.dropna()) < 2 or len(s2.dropna()) < 2:
            snippets.append(f"Il test per Task {task} non e calcolabile con i dati disponibili.")
            continue
        result = stats.ttest_rel(s1, s2, nan_policy="omit")
        snippets.append(gorilla_ttest(systems[0], systems[1], f"Task {task}", result.pvalue, s1.mean(), s2.mean()))
    return snippets


def analyze_user_testing_observations(
    input_path: str | Path = "data/raw/user_testing_observations.csv",
    output_tables_dir: str | Path = "outputs/tables",
    output_text_dir: str | Path = "outputs/texts/snippets",
) -> dict[str, pd.DataFrame]:
    path = resolve_path(input_path)
    columns = ["app", "observations_count", "top_notes"]
    if not path.exists():
        return {"summary": pd.DataFrame(columns=columns), "observations": pd.DataFrame()}
    observations = pd.read_csv(path, encoding="utf-8-sig").dropna(how="all")
    if observations.empty or "app" not in observations.columns:
        return {"summary": pd.DataFrame(columns=columns), "observations": observations}
    note_col = "note" if "note" in observations.columns else "notes" if "notes" in observations.columns else ""
    rows = []
    for app, group in observations.groupby("app", dropna=False):
        notes = group[note_col].dropna().astype(str).tolist() if note_col else []
        rows.append(
            {
                "app": app,
                "observations_count": int(len(group)),
                "top_notes": " | ".join(note[:180] for note in notes[:3]),
            }
        )
    summary = pd.DataFrame(rows, columns=columns)
    tables_dir = resolve_path(output_tables_dir)
    markdown_dir = tables_dir / "markdown"
    tables_dir.mkdir(parents=True, exist_ok=True)
    markdown_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(tables_dir / "user_testing_observations_summary.csv", index=False, encoding="utf-8-sig")
    summary.to_markdown(markdown_dir / "user_testing_observations_summary.md", index=False)

    text_dir = resolve_path(output_text_dir)
    text_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# Problemi emersi dai test utenti", ""]
    if note_col:
        for row in observations.itertuples(index=False):
            app = getattr(row, "app", "")
            note = getattr(row, note_col, "")
            if str(note).strip():
                lines.append(f"- {app}: {str(note).strip()}")
    else:
        lines.append("- Note osservazionali non disponibili.")
    (text_dir / "user_testing_observations.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"summary": summary, "observations": observations}
