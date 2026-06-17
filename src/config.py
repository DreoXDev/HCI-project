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
        "outputs/figures/dark",
        "outputs/figures/presentation",
        paths.get("output_tables", "outputs/tables"),
        paths.get("output_tables_md", "outputs/tables/markdown"),
        paths.get("output_text", "outputs/texts/snippets"),
        "outputs/texts/analysis",
        "outputs/reports",
        "outputs/slide_assets/pack",
        "outputs/figures/presentation/sample",
        "outputs/figures/presentation/questionnaire/items",
        "outputs/figures/presentation/questionnaire/subgroups",
        "outputs/figures/presentation/user_tests/tasks",
        "outputs/figures/presentation/heuristics",
        "outputs/figures/dark/sample",
        "outputs/figures/dark/questionnaire/items",
        "outputs/figures/dark/questionnaire/subgroups",
        "outputs/figures/dark/user_tests/tasks",
        "outputs/figures/dark/heuristics",
        "data/processed",
        "data/formbricks_raw/questionnaire",
        "data/formbricks_raw/heuristics",
        "data/formbricks_raw/user_tests",
    ]
    figure_root = resolve_path(paths.get("output_figures", "outputs/figures"))
    base_dirs.extend(
        [
            figure_root / "dark/user_tests",
            figure_root / "dark/heuristics",
            figure_root / "dark/questionnaire",
            figure_root / "dark/sample",
            figure_root / "dark/questionnaire/items",
            figure_root / "dark/questionnaire/subgroups",
            figure_root / "dark/user_tests/tasks",
        ]
    )
    for directory in base_dirs:
        resolve_path(directory).mkdir(parents=True, exist_ok=True)
