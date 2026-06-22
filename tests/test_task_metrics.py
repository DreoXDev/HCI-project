from __future__ import annotations

import pandas as pd


def test_task_outcomes_have_distinct_completed_and_autonomous_columns() -> None:
    df = pd.read_csv("outputs/tables/task_outcomes_normalized.csv")
    assert {"completed", "completed_autonomously", "critical_error"}.issubset(df.columns)
    assert (df["completed"] >= df["completed_autonomously"]).all()

