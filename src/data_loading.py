from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import resolve_path


def read_csv_auto(path: str | Path, **kwargs) -> pd.DataFrame:
    """Read project CSV files, accepting the semicolon-separated original format."""
    return pd.read_csv(resolve_path(path), sep=None, engine="python", **kwargs)


def load_users_time(path: str | Path) -> pd.DataFrame:
    return read_csv_auto(path)


def load_heuristics(path: str | Path) -> pd.DataFrame:
    df = read_csv_auto(path)
    first_col = df.columns[0]
    if str(first_col).startswith("Unnamed") or first_col == "":
        df = df.rename(columns={first_col: "Problem ID"})
    return df


def load_questionnaire(path: str | Path) -> pd.DataFrame:
    df = read_csv_auto(path)
    first_col = df.columns[0]
    df = df.rename(columns={first_col: "item"})
    return df.set_index("item")


def load_all(config: dict) -> dict[str, pd.DataFrame]:
    paths = config["paths"]
    return {
        "users_time": load_users_time(paths["users_time"]),
        "heuristics_system_1": load_heuristics(paths["heuristics_system_1"]),
        "heuristics_system_2": load_heuristics(paths["heuristics_system_2"]),
        "questionnaire_system_1": load_questionnaire(paths["questionnaire_system_1"]),
        "questionnaire_system_2": load_questionnaire(paths["questionnaire_system_2"]),
    }
