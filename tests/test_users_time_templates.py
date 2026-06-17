from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.export import create_templates
from src.users_time import TEMPLATE_COLUMNS


def test_create_templates_generates_users_time_files(tmp_path: Path) -> None:
    created = create_templates(directory=tmp_path / "templates", overwrite=True)

    assert tmp_path / "templates" / "users-time-template.csv" in created
    example_root = tmp_path / "templates" / "examples"
    assert example_root / "users_time_template.csv" in created
    assert example_root / "users_time_template.xlsx" in created
    assert (example_root / "users_time_template.csv").exists()
    assert (example_root / "users_time_template.xlsx").exists()
    columns = pd.read_csv(example_root / "users_time_template.csv").columns.tolist()
    assert columns == TEMPLATE_COLUMNS


def test_create_templates_does_not_overwrite_without_flag(tmp_path: Path) -> None:
    template = tmp_path / "templates" / "users-time-template.csv"
    template.parent.mkdir(parents=True)
    template.write_text("custom\n", encoding="utf-8")

    create_templates(directory=tmp_path / "templates", overwrite=False)

    assert template.read_text(encoding="utf-8") == "custom\n"
