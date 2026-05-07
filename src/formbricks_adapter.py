from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .adapters.formbricks.heuristic_adapter import convert_heuristics_export
from .adapters.formbricks.mapping_engine import ImportReport, filter_finished
from .adapters.formbricks.normalization import comparable, normalize_item_name, strip_accents
from .adapters.formbricks.questionnaire_adapter import (
    convert_questionnaire_export,
    detect_questionnaire_columns,
    load_formbricks_export,
)
from .config import load_config
from .formbricks_heuristics_pipeline import import_formbricks_heuristics


def normalize_column_name(column: str) -> str:
    return normalize_item_name(column)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import CSV Formbricks nel formato del toolkit HCI")
    parser.add_argument("kind", choices=["questionnaire", "heuristics"])
    parser.add_argument("--input")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--include-unfinished", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    if args.kind == "questionnaire":
        convert_questionnaire_export(args.input, config, args.include_unfinished)
    else:
        source = args.input or config["formbricks"]["heuristics"]["export_path"]
        import_formbricks_heuristics(source)
    print("Import Formbricks completato. Controlla outputs/import_report.md o reports/ per le euristiche.")


__all__ = [
    "ImportReport",
    "comparable",
    "convert_heuristics_export",
    "convert_questionnaire_export",
    "detect_questionnaire_columns",
    "filter_finished",
    "load_formbricks_export",
    "normalize_column_name",
    "normalize_item_name",
    "pd",
    "Path",
    "strip_accents",
    "import_formbricks_heuristics",
]


if __name__ == "__main__":
    main()
