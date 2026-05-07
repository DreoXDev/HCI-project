from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.users_time import normalize_boolean, validate_users_time_file, validate_users_time_long


def _valid_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "user_id": "U01",
                "app": "Deliveroo",
                "task_id": "T01",
                "task_name": "Ricerca ristorante",
                "completion_time_sec": 34,
                "success": "Si",
                "errors_count": 0,
                "help_requests": 0,
            },
            {
                "user_id": "U01",
                "app": "Glovo",
                "task_id": "T01",
                "task_name": "Ricerca ristorante",
                "completion_time_sec": 47,
                "success": "0",
                "errors_count": 1,
                "help_requests": 1,
            },
        ]
    )


def test_valid_users_time_passes_validation() -> None:
    result = validate_users_time_long(_valid_df())

    assert result.is_valid
    assert result.normalized["success"].tolist() == [True, False]


def test_missing_required_column_fails() -> None:
    result = validate_users_time_long(_valid_df().drop(columns=["task_id"]))

    assert not result.is_valid
    assert any("colonne obbligatorie mancanti" in message for message in result.messages)


def test_boolean_variants_are_normalized() -> None:
    assert normalize_boolean("Sì") is True
    assert normalize_boolean("si") is True
    assert normalize_boolean("true") is True
    assert normalize_boolean("1") is True
    assert normalize_boolean("No") is False
    assert normalize_boolean("false") is False
    assert normalize_boolean("0") is False


def test_negative_time_and_errors_fail() -> None:
    df = _valid_df()
    df.loc[0, "completion_time_sec"] = -1
    df.loc[1, "errors_count"] = -2

    result = validate_users_time_long(df)

    assert not result.is_valid
    assert any("completion_time_sec" in message for message in result.messages)
    assert any("errors_count" in message for message in result.messages)


def test_validation_file_absent_writes_report(tmp_path: Path) -> None:
    report = tmp_path / "report.md"

    result = validate_users_time_file(tmp_path / "missing.csv", report_path=report)

    assert not result.is_valid
    assert report.exists()
    assert "file non trovato" in report.read_text(encoding="utf-8")
