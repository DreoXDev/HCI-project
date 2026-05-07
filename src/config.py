from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path, base_dir: Path = PROJECT_ROOT) -> Path:
    value = Path(path)
    return value if value.is_absolute() else base_dir / value


def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    config_path = resolve_path(path)
    with config_path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    config["_root"] = str(config_path.parent)
    return config


def ensure_output_dirs(config: dict[str, Any]) -> None:
    paths = config.get("paths", {})
    base_dirs = [
        paths.get("output_figures", "outputs/figures"),
        paths.get("output_tables", "outputs/tables"),
        paths.get("output_tables_md", "outputs/tables_md"),
        paths.get("output_text", "outputs/text_snippets"),
        "outputs/report_assets",
        "data/processed",
        "data/templates",
    ]
    figure_root = resolve_path(paths.get("output_figures", "outputs/figures"))
    base_dirs.extend(
        [
            figure_root / "user_tests",
            figure_root / "heuristics",
            figure_root / "questionnaire",
        ]
    )
    for directory in base_dirs:
        resolve_path(directory).mkdir(parents=True, exist_ok=True)
