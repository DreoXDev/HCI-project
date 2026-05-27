from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import load_config
from src.data_loading import users_time_long_to_legacy_wide
from src.users_time import analyze_users_time, summarize_users_time


def _analysis_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["U01", "Deliveroo", "T01", "Ricerca ristorante", 30, True, 0, 0],
            ["U02", "Deliveroo", "T01", "Ricerca ristorante", 50, True, 2, 1],
            ["U01", "Glovo", "T01", "Ricerca ristorante", 40, False, 1, 0],
            ["U02", "Glovo", "T01", "Ricerca ristorante", 60, True, 1, 1],
        ],
        columns=[
            "user_id",
            "app",
            "task_id",
            "task_name",
            "completion_time_sec",
            "success",
            "errors_count",
            "help_requests",
        ],
    )


def test_summary_calculates_mean_and_success_rate() -> None:
    summary = summarize_users_time(_analysis_df())

    deliveroo = summary[(summary["app"] == "Deliveroo") & (summary["task_id"] == "T01")].iloc[0]
    glovo = summary[(summary["app"] == "Glovo") & (summary["task_id"] == "T01")].iloc[0]
    assert deliveroo["mean_time_sec"] == 40
    assert deliveroo["success_rate"] == 1
    assert deliveroo["mean_errors"] == 1
    assert glovo["success_rate"] == 0.5


def test_long_users_time_can_feed_legacy_pipeline() -> None:
    wide = users_time_long_to_legacy_wide(_analysis_df())

    assert wide.loc[0, "Task 1 Deliveroo"] == "0.30-C"
    assert wide.loc[0, "Task 1 Glovo"] == "0.40-F"
    assert wide.loc[1, "Task 1 Deliveroo"] == "0.50-A"


def test_analyze_users_time_writes_outputs(tmp_path: Path) -> None:
    source = tmp_path / "users_time.csv"
    _analysis_df().to_csv(source, index=False)
    config = load_config("config.yaml")

    analyze_users_time(
        config,
        input_path=source,
        output_tables_dir=tmp_path / "tables",
        output_figures_dir=tmp_path / "figures",
        output_text_dir=tmp_path / "text",
        report_path=tmp_path / "reports" / "validation.md",
    )

    assert (tmp_path / "tables" / "users_time_summary.csv").exists()
    assert (tmp_path / "tables" / "markdown" / "users_time_summary.md").exists()
    assert (tmp_path / "tables" / "users_time_stat_tests.csv").exists()
    assert (tmp_path / "figures" / "dark" / "users_time_mean_by_task.png").exists()
    assert (tmp_path / "figures" / "presentation" / "users_time_mean_by_task.png").exists()
    for filename in [
        "users_time_boxplot_by_task.png",
        "users_time_success_rate.png",
        "users_time_errors_by_task.png",
    ]:
        assert (tmp_path / "figures" / "dark" / filename).exists()
        assert (tmp_path / "figures" / "presentation" / filename).exists()
    assert (tmp_path / "text" / "users_time_interpretation.md").exists()


def test_absent_file_does_not_crash_when_disabled(tmp_path: Path) -> None:
    config = load_config("config.yaml")
    config["users_time"]["enabled"] = False

    result = analyze_users_time(config, input_path=tmp_path / "missing.csv", report_path=tmp_path / "report.md")

    assert result["summary"].empty
    assert (tmp_path / "report.md").exists()
