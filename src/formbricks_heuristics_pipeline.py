from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy.stats import binomtest

from .adapters.formbricks.detection import find_by_alias
from .adapters.formbricks.normalization import comparable
from .adapters.formbricks.questionnaire_adapter import load_formbricks_export
from .config import resolve_path


HEURISTICS = {
    "E1": "Visibility of system status",
    "E2": "Match between system and real world",
    "E3": "User control and freedom",
    "E4": "Consistency and standards",
    "E5": "Error prevention",
    "E6": "Recognition rather than recall",
    "E7": "Flexibility and efficiency of use",
    "E8": "Aesthetic and minimalist design",
    "E9": "Help users recognize and recover from errors",
    "E10": "Help and documentation",
}

REQUIRED_FIELDS = [
    "evaluator_id",
    "app",
    "task",
    "short_description",
    "long_description",
    "heuristic",
    "severity",
    "top5",
]

OUTPUT_COLUMNS = [
    "candidate_id",
    "app",
    "task",
    "evaluator_id",
    "short_description",
    "long_description",
    "heuristic_id",
    "heuristic_label",
    "severity",
    "top5",
    "problem_group_id",
    "include",
    "review_notes",
]


@dataclass
class HeuristicsImportResult:
    candidates: pd.DataFrame
    errors: pd.DataFrame
    source_rows: int
    column_mapping: dict[str, str]
    warnings: list[str] = field(default_factory=list)


def load_column_mapping(path: str | Path = "config/formbricks_heuristics_mapping.yml") -> dict[str, list[str]]:
    mapping_path = resolve_path(path)
    with mapping_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("columns", {})


def detect_columns(df: pd.DataFrame, mapping: dict[str, list[str]]) -> dict[str, str]:
    detected: dict[str, str] = {}
    available = list(df.columns)
    for field, aliases in mapping.items():
        candidates = [field, *aliases]
        detected[field] = _find_column(available, candidates)
    missing = [field for field in REQUIRED_FIELDS if not detected.get(field)]
    if missing:
        raise ValueError(f"Colonne obbligatorie mancanti nel CSV Formbricks: {', '.join(missing)}")
    return detected


def _find_column(columns: list[str], aliases: list[str]) -> str:
    return find_by_alias(columns, aliases) or ""


def normalize_heuristic(value: Any) -> tuple[str | None, str | None]:
    text = str(value)
    match = re.search(r"\bE(?:10|[1-9])\b", text.upper())
    if match:
        code = match.group(0)
        return code, HEURISTICS[code]
    normalized = comparable(text)
    for code, label in HEURISTICS.items():
        label_cmp = comparable(label)
        if normalized == label_cmp or normalized in label_cmp or label_cmp in normalized:
            return code, label
    return None, None


def normalize_severity(value: Any) -> int | None:
    if pd.isna(value):
        return None
    match = re.search(r"\b[0-4]\b", str(value))
    return int(match.group(0)) if match else None


TRUE_TOP5 = {"si", "sì", "yes", "true", "1", "top 5", "top5"}
FALSE_TOP5 = {"no", "false", "0"}


def normalize_top5(value: Any) -> bool | None:
    if pd.isna(value):
        return None
    normalized = comparable(value)
    if normalized in {comparable(v) for v in TRUE_TOP5}:
        return True
    if normalized in {comparable(v) for v in FALSE_TOP5}:
        return False
    return None


def import_formbricks_heuristics(
    input_path: str | Path,
    output_path: str | Path = "data/processed/heuristics_candidates.csv",
    review_path: str | Path = "data/processed/heuristics_review.csv",
    mapping_path: str | Path = "config/formbricks_heuristics_mapping.yml",
    report_path: str | Path = "reports/heuristics_import_report.md",
    errors_path: str | Path = "reports/heuristics_import_errors.csv",
) -> HeuristicsImportResult:
    source = resolve_path(input_path)
    df = load_formbricks_export(source)
    mapping = load_column_mapping(mapping_path)
    detected = detect_columns(df, mapping)
    normalized = df.rename(columns={source_col: field for field, source_col in detected.items()})

    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index, row in normalized.iterrows():
        candidate_id = f"C{len(rows) + 1:03d}"
        heuristic_id, heuristic_label = normalize_heuristic(row["heuristic"])
        severity = normalize_severity(row["severity"])
        top5 = normalize_top5(row["top5"])
        include = True
        if heuristic_id is None:
            include = False
            errors.append(_error(index, candidate_id, "heuristic", row["heuristic"], "Euristica non riconosciuta"))
        if severity is None:
            include = False
            errors.append(_error(index, candidate_id, "severity", row["severity"], "Severita non valida"))
        if top5 is None:
            include = False
            errors.append(_error(index, candidate_id, "top5", row["top5"], "Top5 non riconosciuto"))
        rows.append(
            {
                "candidate_id": candidate_id,
                "app": _clean_text(row["app"]),
                "task": _clean_text(row["task"]),
                "evaluator_id": _clean_text(row["evaluator_id"]),
                "short_description": _clean_text(row["short_description"]),
                "long_description": _clean_text(row["long_description"]),
                "heuristic_id": heuristic_id or "",
                "heuristic_label": heuristic_label or "",
                "severity": severity if severity is not None else "",
                "top5": bool(top5) if top5 is not None else "",
                "problem_group_id": f"PG{len(rows) + 1:03d}",
                "include": include,
                "review_notes": "",
            }
        )

    candidates = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    error_df = pd.DataFrame(errors, columns=["row_number", "candidate_id", "field", "value", "message"])
    _write_csv(candidates, output_path)
    _write_csv(candidates, review_path)
    _write_csv(error_df, errors_path)
    _write_import_report(candidates, error_df, len(df), detected, report_path, review_path)
    return HeuristicsImportResult(candidates, error_df, len(df), detected)


def _error(index: int, candidate_id: str, field: str, value: Any, message: str) -> dict[str, Any]:
    return {
        "row_number": index + 2,
        "candidate_id": candidate_id,
        "field": field,
        "value": value,
        "message": message,
    }


def _clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def build_heuristics_from_review(
    input_path: str | Path = "data/processed/heuristics_review.csv",
    output_dir: str | Path = "data/raw",
    report_path: str | Path = "reports/heuristics_build_report.md",
    prefixes: dict[str, str] | None = None,
) -> dict[str, pd.DataFrame]:
    review = pd.read_csv(resolve_path(input_path))
    required = set(OUTPUT_COLUMNS) - {"review_notes"}
    missing = [column for column in required if column not in review.columns]
    if missing:
        raise ValueError(f"File review incompleto, colonne mancanti: {', '.join(missing)}")

    include_mask = review["include"].apply(_truthy_include)
    usable = review[include_mask & review["problem_group_id"].notna() & (review["problem_group_id"].astype(str).str.strip() != "")].copy()
    usable["severity"] = pd.to_numeric(usable["severity"], errors="coerce")
    usable["top5"] = usable["top5"].apply(_truthy_include)

    outputs: dict[str, pd.DataFrame] = {}
    for app, app_df in usable.groupby("app", sort=True):
        prefix = _app_prefix(app, prefixes)
        rows = []
        for index, (_, group) in enumerate(app_df.groupby("problem_group_id", sort=True), start=1):
            rows.append(_aggregate_group(group, f"{prefix}{index}"))
        final = pd.DataFrame(rows)
        outputs[app] = final
        filename = f"heuristics_{_slug(app)}.csv"
        _write_csv(final, Path(output_dir) / filename)

    _write_build_report(outputs, len(review), len(usable), report_path)
    return outputs


def _truthy_include(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = comparable(value)
    return normalized in {"true", "1", "yes", "si", "sì"}


def _app_prefix(app: str, prefixes: dict[str, str] | None) -> str:
    if prefixes:
        for key, prefix in prefixes.items():
            if comparable(key) == comparable(app):
                return prefix
    if comparable(app) == "deliveroo":
        return "PD"
    if comparable(app) == "glovo":
        return "PG"
    return "P"


def _aggregate_group(group: pd.DataFrame, problem_id: str) -> dict[str, Any]:
    sorted_group = group.sort_values("severity", ascending=False, na_position="last")
    first = sorted_group.iloc[0]
    severities = pd.to_numeric(group["severity"], errors="coerce").dropna()
    evaluator_ids = sorted(dict.fromkeys(group["evaluator_id"].astype(str)))
    heuristic_ids = _unique_join(group["heuristic_id"], separator=", ")
    top5_count = int(group["top5"].sum())
    not_top5_count = int((~group["top5"]).sum())
    priority = calculate_priority(top5_count, not_top5_count)
    mean = float(severities.mean()) if not severities.empty else np.nan
    sd = float(severities.std(ddof=1)) if len(severities) > 1 else 0.0
    median = float(severities.median()) if not severities.empty else np.nan
    iqr = _iqr(severities)
    expert_values = {f"Expert {idx}": 0 for idx in range(1, len(evaluator_ids) + 1)}
    for idx, evaluator_id in enumerate(evaluator_ids, start=1):
        expert_values[f"Expert {idx}"] = group[group["evaluator_id"].astype(str) == evaluator_id]["severity"].max()
    return {
        "ID": problem_id,
        "Problem ID": problem_id,
        "Descrizione breve": first["short_description"],
        "Problema": first["short_description"],
        "Descrizione lunga": first["long_description"],
        "Euristiche violate (ID)": heuristic_ids,
        "Euristiche": heuristic_ids.replace(", ", "-"),
        "Popolarita": len(evaluator_ids),
        "Popolarità": len(evaluator_ids),
        "Valutatori (ID)": ", ".join(evaluator_ids),
        "Id valutatori": "-".join(evaluator_ids),
        "Priorita": priority,
        "Priorità": priority,
        "Severita media (SD)": f"{mean:.2f} [{sd:.2f}]",
        "Severità media (SD)": f"{mean:.2f} [{sd:.2f}]",
        "Severita mediana (IQR)": f"{median:.2f} [{iqr:.2f}]",
        "Severità mediana (IQR)": f"{median:.2f} [{iqr:.2f}]",
        "severity_mean": round(mean, 2),
        "severity_sd": round(sd, 2),
        "severity_median": round(median, 2),
        "severity_iqr": round(iqr, 2),
        "top5_count": top5_count,
        "not_top5_count": not_top5_count,
        **expert_values,
    }


def calculate_priority(top5_count: int, not_top5_count: int) -> str:
    total = top5_count + not_top5_count
    if total == 0 or top5_count == not_top5_count:
        return "B"
    p_value = binomtest(top5_count, total, p=0.5).pvalue
    if top5_count > not_top5_count and p_value < 0.05:
        return "A"
    if not_top5_count > top5_count and p_value < 0.05:
        return "C"
    return "B"


def _unique_join(values: pd.Series, separator: str) -> str:
    items: list[str] = []
    for value in values.dropna().astype(str):
        for part in re.split(r"[,;\-]+", value):
            part = part.strip()
            if part and part not in items:
                items.append(part)
    return separator.join(items)


def _iqr(values: pd.Series) -> float:
    if values.empty:
        return np.nan
    return float(values.quantile(0.75) - values.quantile(0.25))


def _slug(value: str) -> str:
    return comparable(value).replace(" ", "_")


def _write_csv(df: pd.DataFrame, path: str | Path) -> None:
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target, index=False)


def _write_import_report(
    candidates: pd.DataFrame,
    errors: pd.DataFrame,
    source_rows: int,
    column_mapping: dict[str, str],
    report_path: str | Path,
    review_path: str | Path,
) -> None:
    apps = ", ".join(sorted(candidates["app"].dropna().unique()))
    evaluators = candidates["evaluator_id"].dropna().nunique()
    lines = [
        "# Heuristics Import Report",
        "",
        f"- Righe importate: {source_rows}",
        f"- Problemi candidati: {len(candidates)}",
        f"- App trovate: {apps}",
        f"- Valutatori distinti: {evaluators}",
        f"- Righe con errori: {errors['candidate_id'].nunique() if not errors.empty else 0}",
        f"- Righe escluse di default: {(~candidates['include'].astype(bool)).sum()}",
        "",
        "## Colonne riconosciute",
        "",
        *[f"- `{field}` <- `{column}`" for field, column in column_mapping.items()],
        "",
        "## Errori da verificare",
        "",
    ]
    if errors.empty:
        lines.append("Nessun errore di normalizzazione rilevato.")
    else:
        for _, row in errors.iterrows():
            lines.append(f"- Riga {row['row_number']} `{row['candidate_id']}`: {row['message']} (`{row['value']}`)")
    lines.extend(
        [
            "",
            "## Azione richiesta",
            "",
            f"Aprire `{resolve_path(review_path)}` e compilare manualmente `problem_group_id` per unire problemi simili.",
            "",
            "Poi lanciare `python -m src.cli build-heuristics-from-review --input data/processed/heuristics_review.csv`.",
            "",
        ]
    )
    target = resolve_path(report_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")


def _write_build_report(outputs: dict[str, pd.DataFrame], review_rows: int, used_rows: int, report_path: str | Path) -> None:
    lines = [
        "# Heuristics Build Report",
        "",
        f"- Righe review lette: {review_rows}",
        f"- Righe incluse: {used_rows}",
        f"- App generate: {', '.join(sorted(outputs))}",
        "",
        "## Output",
        "",
    ]
    for app, df in outputs.items():
        lines.append(f"- {app}: {len(df)} problemi finali")
    target = resolve_path(report_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
