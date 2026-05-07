from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from ...config import resolve_path
from .detection import first_index_containing, is_metadata_column, parse_column_tags, tagged_columns
from .mapping_engine import ImportReport, detect_demographic_columns, filter_finished, update_ignored_columns
from .models import QuestionnaireResponse
from .normalization import comparable, normalize_item_name


def load_schema(path: str | Path = "src/schemas/questionnaire_schema.yaml") -> dict[str, Any]:
    with resolve_path(path).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_formbricks_export(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(resolve_path(path), sep=",", encoding="utf-8-sig")


def _is_nps_column(column: str, configured: str, systems: list[str]) -> bool:
    parsed = parse_column_tags(column)
    if parsed.has("nps"):
        return True
    if configured and comparable(configured) in comparable(column):
        return True
    return ("nps" in comparable(column) or "consiglieresti" in comparable(column)) and any(
        comparable(system) in comparable(column) for system in systems
    )


def detect_questionnaire_columns(df: pd.DataFrame, system_name: str, next_system_name: str | None, config: dict[str, Any]) -> list[str]:
    qcfg = config["formbricks"]["questionnaire"]
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    tagged = [column for column in tagged_columns(list(df.columns), "ueq", [system_name])]
    metadata = qcfg.get("metadata_columns", [])
    if tagged:
        return [column for column in tagged if not is_metadata_column(column, metadata)]

    columns = list(df.columns)
    start = first_index_containing(columns, qcfg.get(f"system_{systems.index(system_name) + 1}_column_contains", system_name))
    if start is None:
        start = first_index_containing(columns, system_name)
    if start is None:
        return []
    end = len(columns)
    if next_system_name:
        next_start = first_index_containing(columns, next_system_name)
        if next_start is not None and next_start > start:
            end = next_start
    return [
        column
        for column in columns[start:end]
        if not is_metadata_column(column, metadata)
        and not _is_nps_column(column, qcfg.get("nps_system_1", ""), systems)
        and not _is_nps_column(column, qcfg.get("nps_system_2", ""), systems)
    ]


def _match_normalized(columns: list[str], expected: str) -> str | None:
    expected_cmp = comparable(expected)
    for column in columns:
        column_cmp = comparable(column)
        if column_cmp == expected_cmp or expected_cmp in column_cmp or column_cmp in expected_cmp:
            return column
    return None


def _ordered_ueq_rows(df: pd.DataFrame, columns: list[str], ueq_items: list[str], report: ImportReport) -> dict[str, list[Any]]:
    normalized_map = {normalize_item_name(column): column for column in columns}
    rows: dict[str, list[Any]] = {}
    for item in ueq_items:
        match = _match_normalized(list(normalized_map.keys()), item)
        if match:
            rows[item] = df[normalized_map[match]].tolist()
            report.recognized_columns.append(normalized_map[match])
    if not rows:
        for column in columns:
            item = normalize_item_name(parse_column_tags(column).label)
            rows[item] = df[column].tolist()
            report.recognized_columns.append(column)
    missing = [item for item in ueq_items if item not in rows]
    for item in missing:
        report.warnings.append(f"Item UEQ non trovato: {item}")
    return rows


def _nps_column(df: pd.DataFrame, system: str, configured_col: str) -> str | None:
    if configured_col:
        match = _match_normalized(list(df.columns), configured_col)
        if match:
            return match
    for column in df.columns:
        parsed = parse_column_tags(column)
        if parsed.has("nps") and parsed.system([system]) == system:
            return column
    candidates = [
        column
        for column in df.columns
        if ("nps" in comparable(column) or "consiglieresti" in comparable(column)) and comparable(system) in comparable(column)
    ]
    return candidates[0] if candidates else None


def normalize_questionnaire_responses(df: pd.DataFrame, config: dict, schema: dict | None = None) -> list[QuestionnaireResponse]:
    schema = schema or load_schema()
    qcfg = config["formbricks"]["questionnaire"]
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    demographics = detect_demographic_columns(df, schema, qcfg.get("metadata_columns", []))
    sys1_cols = detect_questionnaire_columns(df, systems[0], systems[1], config)
    sys2_cols = detect_questionnaire_columns(df, systems[1], None, config)
    system_columns = {systems[0]: sys1_cols, systems[1]: sys2_cols}
    responses = []
    for index, (_, row) in enumerate(df.iterrows(), start=1):
        scales = {
            system: {normalize_item_name(parse_column_tags(column).label): row[column] for column in columns}
            for system, columns in system_columns.items()
        }
        nps = {}
        for system, configured in [(systems[0], qcfg.get("nps_system_1", "")), (systems[1], qcfg.get("nps_system_2", ""))]:
            column = _nps_column(df, system, configured)
            if column:
                nps[system] = row[column]
        responses.append(
            QuestionnaireResponse(
                respondent_id=f"Utente {index}",
                demographics={field_id: row[column] for field_id, column in demographics.items()},
                scales=scales,
                nps=nps,
                metadata={column: row[column] for column in qcfg.get("metadata_columns", []) if column in df.columns},
            )
        )
    return responses


def convert_questionnaire_export(
    input_path: str | Path | None,
    config: dict,
    include_unfinished: bool = False,
) -> ImportReport:
    schema = load_schema()
    qcfg = config["formbricks"]["questionnaire"]
    source = input_path or qcfg["export_path"]
    raw = load_formbricks_export(source)
    use_finished = config["formbricks"].get("use_only_finished", True) and not include_unfinished
    df = filter_finished(raw, use_finished)
    report = ImportReport("questionnaire", str(resolve_path(source)), len(raw), len(df))

    demographics = detect_demographic_columns(df, schema, qcfg.get("metadata_columns", []))
    common_rows: dict[str, list[Any]] = {}
    for field_id, column in demographics.items():
        common_rows[field_id] = df[column].tolist()
        report.recognized_columns.append(column)

    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    user_cols = [f"Utente {index + 1}" for index in range(len(df))]
    ueq_items = qcfg.get("ueq_items") or schema["questionnaire"].get("ueq_items", [])
    output_rows = {}
    for index, system in enumerate(systems):
        next_system = systems[index + 1] if index + 1 < len(systems) else None
        columns = detect_questionnaire_columns(df, system, next_system, config)
        rows = dict(common_rows)
        rows.update(_ordered_ueq_rows(df, columns, ueq_items, report))
        nps_col = _nps_column(df, system, qcfg.get(f"nps_system_{index + 1}", ""))
        if nps_col:
            rows["NPS"] = df[nps_col].tolist()
            report.recognized_columns.append(nps_col)
        else:
            report.warnings.append(f"NPS non trovato per {system}: la pipeline saltera il grafico NPS.")
        output_rows[system] = rows

    output_paths = [resolve_path(qcfg["output_system_1"]), resolve_path(qcfg["output_system_2"])]
    for output_path, system in zip(output_paths, systems):
        out = pd.DataFrame(output_rows[system], index=user_cols).T
        out.index.name = "item"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(output_path)
        report.output_paths.append(str(output_path))

    clean_target = resolve_path("data/processed/questionnaire_formbricks_clean.csv")
    clean_target.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(clean_target, index=False)
    long_target = resolve_path("data/processed/questionnaire_long.csv")
    _write_long_questionnaire(output_rows, user_cols, systems, long_target)
    report.output_paths.extend([str(clean_target), str(long_target)])
    update_ignored_columns(report, list(raw.columns))
    _write_import_report(report)
    return report


def _write_long_questionnaire(output_rows: dict[str, dict[str, list[Any]]], user_cols: list[str], systems: list[str], target: Path) -> None:
    rows = []
    for system, items in output_rows.items():
        for item, values in items.items():
            if item == "NPS":
                item_type = "nps"
            elif system in systems and item not in {"genere", "eta", "situazione lavorativa", "istruzione", "familiarita delivery", "preferred_app", "frequency_usage"}:
                item_type = "ueq"
            else:
                item_type = "demographic"
            normalized_system = system if item_type != "demographic" else "profile"
            for respondent, value in zip(user_cols, values):
                rows.append(
                    {
                        "respondent_id": respondent,
                        "system": normalized_system,
                        "item_type": item_type,
                        "item": item,
                        "value": value,
                    }
                )
    target.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).drop_duplicates().to_csv(target, index=False)


def _write_import_report(report: ImportReport) -> None:
    target = resolve_path("outputs/import_report.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report.to_markdown(), encoding="utf-8")
