from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from ...config import resolve_path
from .detection import find_by_alias, parse_column_tags
from .mapping_engine import ImportReport, filter_finished, update_ignored_columns
from .models import HeuristicProblem
from .normalization import comparable, normalize_heuristic_codes
from .questionnaire_adapter import load_formbricks_export


def load_schema(path: str | Path = "src/schemas/heuristic_schema.yaml") -> dict[str, Any]:
    with resolve_path(path).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _field_column(df: pd.DataFrame, field_id: str, field: dict[str, Any]) -> str | None:
    for column in df.columns:
        parsed = parse_column_tags(column)
        if parsed.has("heuristic") and comparable(field_id) in comparable(parsed.label):
            return column
    return find_by_alias(list(df.columns), [field_id, *field.get("aliases", [])])


def detect_heuristic_columns(df: pd.DataFrame, schema: dict[str, Any], config: dict) -> dict[str, str | None]:
    hcfg = config["formbricks"]["heuristics"]
    fields = schema["heuristics"]["fields"]
    configured = {
        "evaluator_id": hcfg.get("evaluator_id_column", ""),
        "system": hcfg.get("system_column", ""),
        "problem_id": hcfg.get("problem_id_column", ""),
        "title": hcfg.get("problem_column", ""),
        "heuristics": hcfg.get("heuristics_column", ""),
        "severity": hcfg.get("severity_column", ""),
    }
    result = {}
    for field_id, field in fields.items():
        aliases = [configured.get(field_id, ""), field_id, *field.get("aliases", [])]
        result[field_id] = find_by_alias(list(df.columns), aliases) or _field_column(df, field_id, field)
    return result


def normalize_heuristic_problems(df: pd.DataFrame, config: dict, schema: dict | None = None) -> list[HeuristicProblem]:
    schema = schema or load_schema()
    columns = detect_heuristic_columns(df, schema, config)
    required = [field_id for field_id, field in schema["heuristics"]["fields"].items() if field.get("required")]
    missing = [field_id for field_id in required if not columns.get(field_id)]
    if missing:
        raise ValueError(f"Import euristiche incompleto, colonne mancanti: {', '.join(missing)}")
    problems = []
    for _, row in df.iterrows():
        heuristics = normalize_heuristic_codes(row[columns["heuristics"]])
        severity = pd.to_numeric(pd.Series([row[columns["severity"]]]), errors="coerce").fillna(0).iloc[0]
        problems.append(
            HeuristicProblem(
                evaluator_id=str(row[columns["evaluator_id"]]),
                evaluator_type=str(row[columns["evaluator_type"]]) if columns.get("evaluator_type") else None,
                system_name=str(row[columns["system"]]),
                title=str(row[columns["title"]]),
                description=str(row[columns["description"]]) if columns.get("description") else str(row[columns["title"]]),
                heuristics=heuristics,
                severity=float(severity),
                notes=str(row[columns["notes"]]) if columns.get("notes") else None,
                problem_id=str(row[columns["problem_id"]]) if columns.get("problem_id") else None,
                metadata={},
            )
        )
    return problems


def convert_heuristics_export(
    input_path: str | Path | None,
    config: dict,
    include_unfinished: bool = False,
) -> ImportReport:
    schema = load_schema()
    hcfg = config["formbricks"]["heuristics"]
    source = input_path or hcfg["export_path"]
    raw = load_formbricks_export(source)
    use_finished = config["formbricks"].get("use_only_finished", True) and not include_unfinished
    df = filter_finished(raw, use_finished)
    report = ImportReport("heuristics", str(resolve_path(source)), len(raw), len(df))
    columns = detect_heuristic_columns(df, schema, config)
    required = [field_id for field_id, field in schema["heuristics"]["fields"].items() if field.get("required")]
    missing = [field_id for field_id in required if not columns.get(field_id)]
    if missing:
        report.warnings.append(f"Import euristiche incompleto, colonne mancanti: {', '.join(missing)}")
        _write_import_report(report)
        raise ValueError(report.warnings[-1])
    report.recognized_columns.extend([column for column in columns.values() if column])
    problems = normalize_heuristic_problems(df, config, schema)
    _write_review_outputs(problems)

    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    output_paths = [resolve_path(hcfg["output_system_1"]), resolve_path(hcfg["output_system_2"])]
    for output_path, system in zip(output_paths, systems):
        subset = [problem for problem in problems if comparable(system) in comparable(problem.system_name)]
        evaluators = sorted({problem.evaluator_id for problem in subset})
        rows = []
        by_id: dict[str, list[HeuristicProblem]] = {}
        for problem in subset:
            key = problem.problem_id or problem.title
            by_id.setdefault(key, []).append(problem)
        for problem_id, group in by_id.items():
            first = group[0]
            row = {
                "Problem ID": problem_id,
                "Problema": first.title,
                "Euristiche": "-".join(dict.fromkeys(code for problem in group for code in problem.heuristics)),
                "Id valutatori": "-".join(dict.fromkeys(problem.evaluator_id for problem in group)),
            }
            severity_by_evaluator = {problem.evaluator_id: problem.severity for problem in group}
            for index, evaluator in enumerate(evaluators, start=1):
                row[f"Expert {index}"] = severity_by_evaluator.get(evaluator, 0)
            rows.append(row)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(output_path, index=False)
        report.output_paths.append(str(output_path))

    clean_target = resolve_path("data/processed/heuristics_formbricks_clean.csv")
    clean_target.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(clean_target, index=False)
    submissions_target = resolve_path("data/processed/heuristics_submissions_clean.csv")
    _write_submissions_clean(problems, submissions_target)
    consolidation_target = resolve_path("data/processed/heuristics_consolidation_template.csv")
    _write_consolidation_template(problems, consolidation_target)
    report.output_paths.extend([str(clean_target), str(submissions_target), str(consolidation_target)])
    update_ignored_columns(report, list(raw.columns))
    _write_import_report(report)
    return report


def _write_review_outputs(problems: list[HeuristicProblem]) -> None:
    target_dir = resolve_path("outputs/heuristic_review")
    target_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# Problemi euristici normalizzati", ""]
    for index, problem in enumerate(problems, start=1):
        lines.extend(
            [
                f"## Problema {index}",
                "",
                f"- Sistema: {problem.system_name}",
                f"- Valutatore: {problem.evaluator_id}",
                f"- Severita: {problem.severity}",
                f"- Euristiche: {', '.join(problem.heuristics)}",
                f"- Titolo: {problem.title}",
                "",
                problem.description,
                "",
            ]
        )
    (target_dir / "all_problems.md").write_text("\n".join(lines), encoding="utf-8")
    (target_dir / "grouped_problems.md").write_text(
        "# Problemi raggruppati\n\nDa compilare dopo consolidamento manuale dei duplicati.\n", encoding="utf-8"
    )
    (target_dir / "possible_duplicates.md").write_text(
        "# Possibili duplicati\n\nNessun suggerimento automatico configurato. Verificare manualmente `all_problems.md`.\n",
        encoding="utf-8",
    )


def _write_submissions_clean(problems: list[HeuristicProblem], target: Path) -> None:
    rows = []
    for index, problem in enumerate(problems, start=1):
        rows.append(
            {
                "submission_id": f"H{index:03d}",
                "evaluator_id": problem.evaluator_id,
                "evaluator_type": problem.evaluator_type,
                "system": problem.system_name,
                "title": problem.title,
                "description": problem.description,
                "heuristics": "-".join(problem.heuristics),
                "severity": problem.severity,
                "notes": problem.notes,
            }
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(target, index=False)


def _write_consolidation_template(problems: list[HeuristicProblem], target: Path) -> None:
    evaluators = sorted({problem.evaluator_id for problem in problems})
    rows = []
    for index, problem in enumerate(problems, start=1):
        row = {
            "canonical_problem_id": problem.problem_id or f"P{index:03d}",
            "system": problem.system_name,
            "canonical_title": problem.title,
            "canonical_description": problem.description,
            "heuristics": "-".join(problem.heuristics),
            "linked_submission_ids": f"H{index:03d}",
            "notes": problem.notes or "",
        }
        for evaluator in evaluators:
            row[evaluator] = problem.severity if evaluator == problem.evaluator_id else 0
        rows.append(row)
    target.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(target, index=False)


def _write_import_report(report: ImportReport) -> None:
    target = resolve_path("outputs/import_report.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report.to_markdown(), encoding="utf-8")
