from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import resolve_path


EXPECTED_PROBLEMS = 40
EXPECTED_EXPERTS = 8
EXPECTED_RATINGS = EXPECTED_PROBLEMS * EXPECTED_EXPERTS


@dataclass(frozen=True)
class DataIntegrityAuditResult:
    valid: bool
    report_path: Path
    mapping_path: Path
    problem_count: int
    expert_count: int
    rating_count: int
    failures: list[str]


def run_data_integrity_audit(
    *,
    problems_path: str | Path = "data/processed/heuristics/clean_problems.csv",
    ratings_path: str | Path = "data/processed/heuristics/problem_ratings_long.csv",
    report_path: str | Path = "outputs/reports/data_integrity_audit.md",
    mapping_path: str | Path = "data/processed/problem_id_mapping.csv",
) -> DataIntegrityAuditResult:
    problems_file = resolve_path(problems_path)
    ratings_file = resolve_path(ratings_path)
    report_file = resolve_path(report_path)
    mapping_file = resolve_path(mapping_path)

    failures: list[str] = []
    if not problems_file.exists():
        failures.append(f"File problemi mancante: {problems_file}")
        problems = pd.DataFrame()
    else:
        problems = pd.read_csv(problems_file)
    if not ratings_file.exists():
        failures.append(f"File rating mancante: {ratings_file}")
        ratings = pd.DataFrame()
    else:
        ratings = pd.read_csv(ratings_file)

    problem_count = int(problems["problem_id"].nunique()) if "problem_id" in problems else 0
    expert_count = int(ratings["expert_id"].nunique()) if "expert_id" in ratings else 0
    rating_count = int(len(ratings))

    if problem_count != EXPECTED_PROBLEMS:
        failures.append(f"Problemi consolidati: {problem_count}/{EXPECTED_PROBLEMS}")
    if expert_count != EXPECTED_EXPERTS:
        failures.append(f"Esperti valutatori: {expert_count}/{EXPECTED_EXPERTS}")
    if rating_count != EXPECTED_RATINGS:
        failures.append(f"Rating di severita: {rating_count}/{EXPECTED_RATINGS}")

    if {"expert_id", "problem_id"}.issubset(ratings.columns):
        duplicate_pairs = int(ratings.duplicated(["expert_id", "problem_id"]).sum())
        if duplicate_pairs:
            failures.append(f"Coppie esperto/problema duplicate: {duplicate_pairs}")
        per_problem = ratings.groupby("problem_id").size()
        if not per_problem.empty and (per_problem != EXPECTED_EXPERTS).any():
            bad = ", ".join(f"{idx}:{count}" for idx, count in per_problem[per_problem != EXPECTED_EXPERTS].items())
            failures.append(f"Problemi con numero rating diverso da {EXPECTED_EXPERTS}: {bad}")
        per_expert = ratings.groupby("expert_id").size()
        if not per_expert.empty and (per_expert != EXPECTED_PROBLEMS).any():
            bad = ", ".join(f"{idx}:{count}" for idx, count in per_expert[per_expert != EXPECTED_PROBLEMS].items())
            failures.append(f"Esperti con numero rating diverso da {EXPECTED_PROBLEMS}: {bad}")

    if "severity" in ratings:
        severity = pd.to_numeric(ratings["severity"], errors="coerce")
        if severity.isna().any():
            failures.append(f"Rating di severita non numerici o mancanti: {int(severity.isna().sum())}")
        out_of_range = severity.dropna()[~severity.dropna().between(0, 4)]
        if not out_of_range.empty:
            failures.append(f"Rating fuori scala 0-4: {len(out_of_range)}")
    else:
        severity = pd.Series(dtype=float)
        failures.append("Colonna severity mancante nei rating")

    if "problem_id" in problems and "problem_id" in ratings:
        problem_ids = set(problems["problem_id"].astype(str))
        rating_problem_ids = set(ratings["problem_id"].astype(str))
        missing = sorted(problem_ids - rating_problem_ids)
        unknown = sorted(rating_problem_ids - problem_ids)
        if missing:
            failures.append(f"Problemi senza rating: {', '.join(missing)}")
        if unknown:
            failures.append(f"Rating associati a problemi non presenti: {', '.join(unknown)}")

    mapping = _problem_mapping(problems)
    mapping_file.parent.mkdir(parents=True, exist_ok=True)
    mapping.to_csv(mapping_file, index=False, encoding="utf-8-sig")

    lines = [
        "# Data Integrity Audit",
        "",
        "| check | valore | atteso | esito |",
        "|---|---:|---:|---|",
        f"| Problemi consolidati unici | {problem_count} | {EXPECTED_PROBLEMS} | {_status(problem_count == EXPECTED_PROBLEMS)} |",
        f"| Esperti valutatori unici | {expert_count} | {EXPECTED_EXPERTS} | {_status(expert_count == EXPECTED_EXPERTS)} |",
        f"| Rating severita totali | {rating_count} | {EXPECTED_RATINGS} | {_status(rating_count == EXPECTED_RATINGS)} |",
        f"| Rating scala 0-4 inclusiva | {int(severity.dropna().between(0, 4).sum()) if 'severity' in ratings else 0} | {EXPECTED_RATINGS} | {_status('severity' in ratings and int(severity.dropna().between(0, 4).sum()) == EXPECTED_RATINGS)} |",
        "",
        "Nota: il valore 0 e una valutazione valida sulla scala Nielsen e viene conservato nei conteggi.",
        "",
        f"Mapping problemi esportato in `{mapping_file.relative_to(resolve_path('.'))}`.",
        "",
    ]
    if failures:
        lines.extend(["## Failure", "", *[f"- {failure}" for failure in failures], "", "STATUS: FAIL", ""])
    else:
        lines.extend(["## Esito", "", "- Dataset coerente: 40 problemi x 8 esperti = 320 rating.", "- Nessuna coppia esperto/problema duplicata.", "", "STATUS: PASS", ""])

    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text("\n".join(lines), encoding="utf-8")
    return DataIntegrityAuditResult(
        valid=not failures,
        report_path=report_file,
        mapping_path=mapping_file,
        problem_count=problem_count,
        expert_count=expert_count,
        rating_count=rating_count,
        failures=failures,
    )


def enforce_data_integrity_audit() -> DataIntegrityAuditResult:
    result = run_data_integrity_audit()
    if not result.valid:
        details = "\n".join(f"- {failure}" for failure in result.failures)
        raise SystemExit(f"Data integrity audit fallito.\n{details}\nReport: {result.report_path}")
    return result


def _problem_mapping(problems: pd.DataFrame) -> pd.DataFrame:
    columns = ["canonical_problem_id", "source_problem_id", "app", "title", "heuristic", "screen"]
    if problems.empty or "problem_id" not in problems:
        return pd.DataFrame(columns=columns)
    rows = []
    for index, row in problems.reset_index(drop=True).iterrows():
        rows.append(
            {
                "canonical_problem_id": f"P{index + 1:03d}",
                "source_problem_id": row.get("problem_id", ""),
                "app": row.get("app", ""),
                "title": row.get("title", ""),
                "heuristic": row.get("heuristic", ""),
                "screen": row.get("screen", ""),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def _status(ok: bool) -> str:
    return "OK" if ok else "FAIL"
