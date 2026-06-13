from __future__ import annotations

import pandas as pd

import src.real_inputs as real_inputs
from src.real_inputs import prepare_real_inputs
from src.users_time import UsersTimeValidationResult


def test_prepare_real_inputs_reports_partial_dataset(tmp_path, monkeypatch) -> None:
    source = tmp_path / "inbox"
    source.mkdir()
    pd.DataFrame(
        [
            {
                "problem_id": "P001",
                "app": "Deliveroo",
                "screen": "Home",
                "heuristic": "E1",
                "title": "Titolo",
                "description": "Descrizione",
            }
        ]
    ).to_csv(source / "clean_problems.csv", index=False)
    pd.DataFrame(
        [
            {
                "user_id": "U01",
                "app": "Deliveroo",
                "task_id": 1,
                "completion_time_sec": 10,
                "success": True,
                "errors_count": 0,
                "help_requests": 0,
            }
        ]
    ).to_csv(source / "users_time_clean.csv", index=False)

    monkeypatch.setattr(real_inputs, "resolve_path", lambda path: path if hasattr(path, "is_absolute") and path.is_absolute() else tmp_path / str(path))
    monkeypatch.setattr(
        real_inputs,
        "validate_users_time_file",
        lambda path, **_: UsersTimeValidationResult(True, ["WARNING: dataset parziale users_time: 1/24 utenti presenti"], pd.read_csv(path)),
    )
    config = {
        "users_time": {
            "required_columns": ["user_id", "app", "task_id", "task_name", "completion_time_sec", "success", "errors_count", "help_requests"],
            "tasks": [{"id": "T01", "name": "Task 1"}],
        },
        "formbricks": {"questionnaire": {"export_path": ""}},
        "project": {"system_1": "Deliveroo", "system_2": "Glovo"},
    }

    status = prepare_real_inputs(source, config, overwrite=True)

    assert status.data_status == "PARTIAL_DATA"
    assert status.users_time_present == 1
    assert (tmp_path / "data/raw/users_time.csv").exists()
    assert (tmp_path / "outputs/reports/real_input_status.md").exists()
