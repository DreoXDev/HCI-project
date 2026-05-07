from __future__ import annotations

import re

import pandas as pd
from scipy import stats

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
    return pd.DataFrame(long_rows), pd.DataFrame(summary_rows)


def compute_user_test_statistics(df: pd.DataFrame, config: dict) -> list[str]:
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    parsed = add_parsed_task_columns(df, systems)
    snippets = []
    for task in range(1, 4):
        s1 = parsed[f"Task {task} {systems[0]} seconds"]
        s2 = parsed[f"Task {task} {systems[1]} seconds"]
        result = stats.ttest_rel(s1, s2, nan_policy="omit")
        snippets.append(gorilla_ttest(systems[0], systems[1], f"Task {task}", result.pvalue, s1.mean(), s2.mean()))
    return snippets
