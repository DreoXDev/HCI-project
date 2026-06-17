from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import resolve_path


def read_csv_auto(path: str | Path, **kwargs) -> pd.DataFrame:
    """Read project CSV files, accepting the semicolon-separated original format."""
    df = pd.read_csv(resolve_path(path), sep=None, engine="python", **kwargs)
    df = df.rename(columns=lambda column: str(column).lstrip("\ufeff"))
    return df


def read_csv_optional(path: str | Path, **kwargs) -> pd.DataFrame:
    if not str(path).strip():
        return pd.DataFrame()
    target = resolve_path(path)
    if not target.exists() or not target.is_file():
        return pd.DataFrame()
    return read_csv_auto(target, **kwargs)


def load_users_time(path: str | Path) -> pd.DataFrame:
    df = read_csv_auto(path)
    long_columns = {"user_id", "app", "task_id", "completion_time_sec", "success"}
    if long_columns.issubset(df.columns):
        return users_time_long_to_legacy_wide(df)
    return df


def users_time_long_to_legacy_wide(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    task_order = {
        task_id: index + 1
        for index, task_id in enumerate(sorted(df["task_id"].dropna().astype(str).unique()))
    }
    for user_id, user_rows in df.groupby("user_id", sort=True):
        output_row: dict[str, object] = {"User": user_id}
        for row in user_rows.itertuples(index=False):
            task_number = task_order.get(str(row.task_id))
            if not task_number or task_number > 3:
                continue
            seconds = int(pd.to_numeric(getattr(row, "completion_time_sec"), errors="coerce"))
            minutes, remainder = divmod(seconds, 60)
            status = _legacy_success_status(getattr(row, "success"), getattr(row, "help_requests", 0))
            output_row[f"Task {task_number} {row.app}"] = f"{minutes}.{remainder:02d}-{status}"
        rows.append(output_row)
    return pd.DataFrame(rows)


def _legacy_success_status(value: object, help_requests: object = 0) -> str:
    text = str(value).strip().upper()
    if text in {"C", "A", "F"}:
        return text
    if text in {"TRUE", "1", "YES", "SI", "SÌ"}:
        help_count = pd.to_numeric(help_requests, errors="coerce")
        return "A" if pd.notna(help_count) and float(help_count) > 0 else "C"
    return "F"


def load_heuristics(path: str | Path) -> pd.DataFrame:
    df = read_csv_optional(path)
    if df.empty:
        return df
    first_col = df.columns[0]
    if str(first_col).startswith("Unnamed") or first_col == "":
        df = df.rename(columns={first_col: "Problem ID"})
    return df


def load_questionnaire(path: str | Path) -> pd.DataFrame:
    df = read_csv_optional(path)
    if df.empty:
        return pd.DataFrame()
    first_col = df.columns[0]
    df = df.rename(columns={first_col: "item"})
    return df.set_index("item")


def final_heuristics_as_legacy(system: str) -> pd.DataFrame:
    final_path = resolve_path("data/processed/heuristics/heuristic_final_dataset.csv")
    if not final_path.exists():
        return pd.DataFrame()
    final = pd.read_csv(final_path)
    required = {"problem_id", "app", "title", "heuristic", "expert_id", "severity"}
    if final.empty or not required.issubset(final.columns):
        return pd.DataFrame()
    subset = final[final["app"].astype(str).str.casefold() == system.casefold()].copy()
    if subset.empty:
        return pd.DataFrame()
    rows = []
    for problem_id, group in subset.groupby("problem_id", sort=True):
        first = group.iloc[0]
        row: dict[str, object] = {
            "Problem ID": problem_id,
            "Problema": first.get("title", ""),
            "Euristiche": str(first.get("heuristic", "")).replace(";", "-"),
            "Id valutatori": "-".join(group["expert_id"].dropna().astype(str).sort_values().unique()),
        }
        for expert_id, expert_group in group.groupby("expert_id", sort=True):
            row[f"Expert {expert_id}"] = pd.to_numeric(expert_group["severity"], errors="coerce").mean()
        rows.append(row)
    return pd.DataFrame(rows)


def load_all(config: dict) -> dict[str, pd.DataFrame]:
    paths = config["paths"]
    system_1 = config["project"]["system_1"]
    system_2 = config["project"]["system_2"]
    heuristics_1 = load_heuristics(paths.get("heuristics_system_1", ""))
    heuristics_2 = load_heuristics(paths.get("heuristics_system_2", ""))
    if heuristics_1.empty:
        heuristics_1 = final_heuristics_as_legacy(system_1)
    if heuristics_2.empty:
        heuristics_2 = final_heuristics_as_legacy(system_2)
    return {
        "users_time": load_users_time(paths["users_time"]),
        "heuristics_system_1": heuristics_1,
        "heuristics_system_2": heuristics_2,
        "questionnaire_system_1": load_questionnaire(paths["questionnaire_system_1"]),
        "questionnaire_system_2": load_questionnaire(paths["questionnaire_system_2"]),
    }
