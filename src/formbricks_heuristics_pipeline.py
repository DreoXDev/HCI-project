from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yaml

from .adapters.formbricks.detection import find_by_alias
from .adapters.formbricks.normalization import comparable
from .adapters.formbricks.questionnaire_adapter import load_formbricks_export
from .config import resolve_path
from .visualization.theme import style_axis


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


@dataclass
class HeuristicsRawResult:
    raw_problems_long: pd.DataFrame
    raw_problems_table: pd.DataFrame
    expert_profiles: pd.DataFrame
    warnings: list[str] = field(default_factory=list)
    output_paths: list[Path] = field(default_factory=list)


@dataclass
class HeuristicsSeverityResult:
    ratings_long: pd.DataFrame
    final_problem_summary: pd.DataFrame
    warnings: list[str] = field(default_factory=list)
    output_paths: list[Path] = field(default_factory=list)


@dataclass
class CleanValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class FinalSeverityPipelineResult:
    clean_problems: pd.DataFrame
    ratings_long: pd.DataFrame
    final_dataset: pd.DataFrame
    problem_summary: pd.DataFrame
    warnings: list[str] = field(default_factory=list)
    output_paths: list[Path] = field(default_factory=list)


CLEAN_PROBLEM_REQUIRED_COLUMNS = ["problem_id", "app", "screen", "heuristic", "title", "description"]
CLEAN_PROBLEM_OPTIONAL_COLUMNS = ["source_count", "notes", "raw_problem_ids", "recommendation", "impact"]
FORMBRICKS_METADATA_COLUMNS = {
    "no.",
    "response id",
    "timestamp",
    "finished",
    "survey id",
    "formbricks id (internal)",
    "user id",
    "tags",
    "url",
    "country",
    "useragent - os",
    "useragent - device",
    "useragent - browser",
}
PROBLEM_ID_PATTERN = re.compile(r"\[(P\d{3,})\]", re.IGNORECASE)


def load_raw_heuristics_mapping(path: str | Path = "config/heuristics_raw_mapping.yml") -> dict[str, Any]:
    mapping_path = resolve_path(path)
    with mapping_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("heuristics_raw", data)


def _find_column(columns: list[str], aliases: list[str]) -> str:
    return find_by_alias(columns, aliases) or ""


def normalize_heuristic(value: Any) -> tuple[str | None, str | None]:
    text = str(value)
    if not text.strip() or text.strip().lower() == "nan":
        return None, None
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


def normalize_heuristic_codes(value: Any) -> list[str]:
    if pd.isna(value):
        return []
    text = str(value)
    if not text.strip():
        return []
    codes = re.findall(r"\bE(?:10|[1-9])\b", text.upper())
    if not codes:
        parts = re.split(r"[,;\n\[\]\(\)\"]+|\s+-\s+|\s+", text)
        for part in parts:
            code, _ = normalize_heuristic(part)
            if code:
                codes.append(code)
    return list(dict.fromkeys(codes))


def normalize_app(value: Any, systems: list[str] | None = None) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    for system in systems or ["Deliveroo", "Glovo"]:
        if comparable(system) in comparable(text):
            return system
    return text


def normalize_severity(value: Any) -> int | None:
    if pd.isna(value):
        return None
    match = re.search(r"\b[0-4]\b", str(value))
    return int(match.group(0)) if match else None


def completion_status(app: str, short_description: str, long_description: str, heuristics: str) -> str:
    missing = []
    if not app:
        missing.append("missing_app")
    if not short_description and not long_description:
        missing.append("missing_description")
    if not heuristics:
        missing.append("missing_heuristics")
    if not missing:
        return "complete"
    return missing[0] if len(missing) == 1 else "partial"


def import_heuristics_raw_survey(
    input_path: str | Path,
    *,
    config: dict | None = None,
    mapping_path: str | Path = "config/heuristics_raw_mapping.yml",
    output_dir: str | Path = "data/processed/heuristics",
    figures_dir: str | Path = "outputs/figures/heuristics",
    report_path: str | Path = "reports/heuristics_raw_report.md",
    template_path: str | Path = "data/templates/heuristics_consolidated_problems_template.csv",
) -> HeuristicsRawResult:
    df = load_formbricks_export(input_path)
    mapping = load_raw_heuristics_mapping(mapping_path)
    systems = [config["project"]["system_1"], config["project"]["system_2"]] if config else ["Deliveroo", "Glovo"]
    expert_profiles, profile_columns, warnings = extract_expert_profiles(df, mapping)
    raw_long, raw_warnings, ignored_empty = normalize_raw_heuristic_problems(df, mapping, profile_columns, systems)
    warnings.extend(raw_warnings)
    raw_table = build_raw_problems_table(raw_long)

    output_root = resolve_path(output_dir)
    figures_root = resolve_path(figures_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    figures_root.mkdir(parents=True, exist_ok=True)

    paths = [
        _write_csv_return(raw_long, output_root / "raw_problems_long.csv"),
        _write_csv_return(raw_table, output_root / "raw_problems_table.csv"),
        _write_csv_return(expert_profiles, output_root / "expert_profiles.csv"),
    ]
    problem_counts_by_app = _count(raw_table, "app")
    problem_counts_by_evaluator = _count(raw_table, "evaluator_id")
    heuristic_counts = _heuristic_counts(raw_table)
    evaluator_matrix = evaluator_problem_matrix_raw(raw_table)
    paths.extend(
        [
            _write_csv_return(problem_counts_by_app, output_root / "problem_counts_by_app.csv"),
            _write_csv_return(problem_counts_by_evaluator, output_root / "problem_counts_by_evaluator.csv"),
            _write_csv_return(heuristic_counts, output_root / "heuristic_counts.csv"),
            _write_csv_return(evaluator_matrix.reset_index(names="evaluator_id"), output_root / "evaluator_problem_matrix.csv"),
            _write_csv_return(build_evaluators_slide_table(expert_profiles, raw_table), resolve_path("outputs/tables/heuristics_evaluators_slide.csv")),
            _write_csv_return(raw_table, resolve_path("data/processed/heuristics_candidates.csv")),
            _write_csv_return(build_review_template(raw_table), resolve_path("data/processed/heuristics_review.csv")),
            write_consolidated_problems_template(template_path),
        ]
    )

    _plot_profile_charts(expert_profiles, figures_root / "demographics")
    _plot_count_bar(problem_counts_by_app, "app", "Problemi grezzi per app", figures_root / "problem_counts_by_app.png")
    _plot_count_bar(problem_counts_by_evaluator, "evaluator_id", "Problemi grezzi per valutatore", figures_root / "problem_counts_by_evaluator.png")
    _plot_count_bar(heuristic_counts, "heuristic", "Euristiche violate", figures_root / "heuristic_counts.png")
    _plot_matrix(evaluator_matrix, "Matrice grezza valutatore-problema", figures_root / "evaluator_problem_matrix.png")
    _write_raw_report(report_path, expert_profiles, raw_table, problem_counts_by_app, problem_counts_by_evaluator, heuristic_counts, warnings, ignored_empty, paths)
    return HeuristicsRawResult(raw_long, raw_table, expert_profiles, warnings, paths)


def extract_expert_profiles(df: pd.DataFrame, mapping: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, str], list[str]]:
    fields = mapping.get("evaluator_fields", {})
    detected: dict[str, str] = {}
    warnings: list[str] = []
    for field, aliases in fields.items():
        column = _find_column(list(df.columns), aliases if isinstance(aliases, list) else [str(aliases)])
        detected[field] = column
        if not column and field == "evaluator_id":
            warnings.append("Colonna evaluator_id non trovata: verranno generati ID automatici.")
        elif not column:
            warnings.append(f"Colonna profilo non trovata: {field}")
    rows = []
    for index, row in df.iterrows():
        profile = {field: _clean_text(row[column]) if column else "" for field, column in detected.items()}
        if not profile.get("evaluator_id"):
            profile["evaluator_id"] = f"EU{index + 1:02d}"
            warnings.append(f"Evaluator ID mancante alla riga {index + 2}: assegnato {profile['evaluator_id']}.")
        rows.append(profile)
    return pd.DataFrame(rows), detected, warnings


def normalize_raw_heuristic_problems(
    df: pd.DataFrame,
    mapping: dict[str, Any],
    profile_columns: dict[str, str],
    systems: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str], int]:
    slot_count = int(mapping.get("problem_slots", {}).get("count", 10))
    field_aliases = mapping.get("problem_slots", {}).get("fields", {})
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []
    ignored_empty = 0
    for source_index, source_row in df.iterrows():
        profile = {field: _clean_text(source_row[column]) if column else "" for field, column in profile_columns.items()}
        if not profile.get("evaluator_id"):
            profile["evaluator_id"] = f"EU{source_index + 1:02d}"
        for slot in range(1, slot_count + 1):
            slot_values = {}
            for field in ["app", "short_description", "long_description", "heuristics", "notes"]:
                column = find_problem_slot_column(list(df.columns), slot, field, field_aliases.get(field, []))
                slot_values[field] = _clean_text(source_row[column]) if column else ""
            if not any(slot_values.values()):
                ignored_empty += 1
                continue
            heuristics = normalize_heuristic_codes(slot_values["heuristics"])
            status = completion_status(normalize_app(slot_values["app"], systems), slot_values["short_description"], slot_values["long_description"], ";".join(heuristics))
            if status != "complete":
                warnings.append(f"Problema parziale riga {source_index + 2}, slot {slot}: {status}.")
            if slot_values["heuristics"] and not heuristics:
                warnings.append(f"Euristiche non riconosciute riga {source_index + 2}, slot {slot}: {slot_values['heuristics']}")
            rows.append(
                {
                    "raw_problem_id": f"RAW{len(rows) + 1:03d}",
                    **profile,
                    "problem_slot": slot,
                    "app": normalize_app(slot_values["app"], systems),
                    "short_description": slot_values["short_description"],
                    "long_description": slot_values["long_description"],
                    "heuristics": ";".join(heuristics),
                    "notes": slot_values["notes"],
                    "completion_status": status,
                }
            )
    columns = [
        "raw_problem_id",
        "evaluator_id",
        "expert_group",
        "gender",
        "age_group",
        "occupation",
        "familiarity",
        "usability_experience",
        "domain_experience",
        "problem_slot",
        "app",
        "short_description",
        "long_description",
        "heuristics",
        "notes",
        "completion_status",
    ]
    return pd.DataFrame(rows, columns=columns), warnings, ignored_empty


def find_problem_slot_column(columns: list[str], slot: int, field: str, aliases: list[str]) -> str:
    question_number = 7 + (slot - 1) * 4 + {"app": 0, "short_description": 1, "long_description": 2, "heuristics": 3, "notes": 4}.get(field, 0)
    normalized_aliases = [comparable(alias).replace("slot", str(slot)) for alias in aliases]
    for column in columns:
        raw_column = str(column).strip()
        comp = comparable(column)
        if re.match(rf"^{question_number}[\.\s:]", raw_column):
            if "option id" in comp:
                continue
            if field == "app" and any(token in comp for token in ["app", "quale app"]):
                return column
            if field == "short_description" and any(token in comp for token in ["descrizione breve", "titolo"]):
                return column
            if field == "long_description" and any(token in comp for token in ["dettagliata", "dettagliato", "descrizione più"]):
                return column
            if field == "heuristics" and any(token in comp for token in ["euristiche", "heuristic"]):
                return column
        if any(alias and alias in comp and str(slot) in comp for alias in normalized_aliases):
            return column
    return ""


def build_raw_problems_table(raw_long: pd.DataFrame) -> pd.DataFrame:
    columns = ["raw_problem_id", "evaluator_id", "problem_slot", "app", "short_description", "long_description", "heuristics", "notes", "completion_status"]
    return raw_long[columns].copy() if not raw_long.empty else pd.DataFrame(columns=columns)


def evaluator_problem_matrix_raw(raw_table: pd.DataFrame) -> pd.DataFrame:
    evaluators = sorted(raw_table["evaluator_id"].dropna().astype(str).unique()) if not raw_table.empty else []
    problems = raw_table["raw_problem_id"].dropna().astype(str).tolist() if not raw_table.empty else []
    matrix = pd.DataFrame(0, index=evaluators, columns=problems, dtype=int)
    for row in raw_table.itertuples():
        if row.evaluator_id in matrix.index and row.raw_problem_id in matrix.columns:
            matrix.loc[row.evaluator_id, row.raw_problem_id] = 1
    return matrix


def write_consolidated_problems_template(path: str | Path = "data/templates/heuristics_consolidated_problems_template.csv") -> Path:
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    columns = ["final_problem_id", "app", "short_description", "long_description", "heuristics", "source_raw_problem_ids", "notes"]
    if not target.exists():
        pd.DataFrame(
            [
                {"final_problem_id": "D-PB01", "app": "Deliveroo", "short_description": "", "long_description": "", "heuristics": "E1;E8", "source_raw_problem_ids": "RAW001;RAW007", "notes": ""},
                {"final_problem_id": "G-PB01", "app": "Glovo", "short_description": "", "long_description": "", "heuristics": "E3", "source_raw_problem_ids": "RAW002;RAW010", "notes": ""},
            ],
            columns=columns,
        ).to_csv(target, index=False)
    return target


def build_review_template(raw_table: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "problem_group_id",
        "raw_problem_id",
        "app",
        "problem_title",
        "problem_description",
        "heuristic",
        "evaluator_id",
        "review_notes",
    ]
    if raw_table.empty:
        return pd.DataFrame(columns=columns)
    review = pd.DataFrame(
        {
            "problem_group_id": "",
            "raw_problem_id": raw_table.get("raw_problem_id", ""),
            "app": raw_table.get("app", ""),
            "problem_title": raw_table.get("short_description", ""),
            "problem_description": raw_table.get("long_description", ""),
            "heuristic": raw_table.get("heuristics", ""),
            "evaluator_id": raw_table.get("evaluator_id", ""),
            "review_notes": "",
        }
    )
    return review[columns]


def build_evaluators_slide_table(expert_profiles: pd.DataFrame, raw_table: pd.DataFrame) -> pd.DataFrame:
    columns = ["Valutatore", "Gruppo", "App valutata", "Problemi segnalati"]
    if expert_profiles.empty:
        return pd.DataFrame(columns=columns)
    rows = []
    for profile in expert_profiles.itertuples(index=False):
        evaluator_id = str(getattr(profile, "evaluator_id", ""))
        subset = raw_table[raw_table["evaluator_id"].astype(str) == evaluator_id] if not raw_table.empty else pd.DataFrame()
        apps = " e ".join(sorted(app for app in subset.get("app", pd.Series(dtype=str)).dropna().astype(str).unique() if app))
        rows.append(
            {
                "Valutatore": evaluator_id,
                "Gruppo": getattr(profile, "expert_group", ""),
                "App valutata": apps or "Deliveroo e Glovo",
                "Problemi segnalati": int(len(subset)),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def parse_severity_ratings(
    ratings_path: str | Path,
    problems_path: str | Path,
    *,
    output_dir: str | Path = "data/processed/heuristics",
    figures_dir: str | Path = "outputs/figures/heuristics",
    report_path: str | Path = "reports/heuristics_final_report.md",
) -> HeuristicsSeverityResult:
    ratings = load_formbricks_export(ratings_path)
    problems = pd.read_csv(resolve_path(problems_path))
    ratings_long, warnings = normalize_severity_ratings(ratings, problems)
    summary = summarize_severity_ratings(problems, ratings_long)
    matrix = final_evaluator_problem_matrix(ratings_long)
    bands = _count(summary, "priority_band")
    output_root = resolve_path(output_dir)
    figures_root = resolve_path(figures_dir)
    paths = [
        _write_csv_return(ratings_long, output_root / "severity_ratings_long.csv"),
        _write_csv_return(summary, output_root / "final_problem_summary.csv"),
        _write_csv_return(build_problems_slide_table(summary), resolve_path("outputs/tables/heuristics_problems_slide.csv")),
        _write_csv_return(matrix.reset_index(names="evaluator_id"), output_root / "final_evaluator_problem_matrix.csv"),
        _write_csv_return(bands, output_root / "problem_priority_bands.csv"),
    ]
    _plot_count_bar(bands, "priority_band", "Fasce priorità problemi", figures_root / "final_priority_bands.png")
    _plot_matrix(matrix, "Matrice finale valutatore-problema", figures_root / "final_evaluator_problem_matrix.png")
    _write_final_report(report_path, summary, warnings, paths)
    return HeuristicsSeverityResult(ratings_long, summary, warnings, paths)


def load_clean_problems(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(resolve_path(path))
    for column in CLEAN_PROBLEM_REQUIRED_COLUMNS + CLEAN_PROBLEM_OPTIONAL_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    df["problem_id"] = df["problem_id"].astype(str).str.strip().str.upper()
    for column in ["app", "screen", "heuristic", "title", "description"]:
        df[column] = df[column].map(_clean_text)
    return df


def validate_clean_problems(path_or_df: str | Path | pd.DataFrame) -> CleanValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        df = pd.read_csv(resolve_path(path_or_df)) if not isinstance(path_or_df, pd.DataFrame) else path_or_df.copy()
    except FileNotFoundError:
        return CleanValidationResult(False, [f"File clean_problems.csv non trovato: {resolve_path(path_or_df)}"], [])
    missing = [column for column in CLEAN_PROBLEM_REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        errors.append(f"Colonne obbligatorie mancanti: {', '.join(missing)}")
        return CleanValidationResult(False, errors, warnings)
    if df.empty:
        errors.append("Il file clean_problems.csv non contiene righe.")
    blank_rows = df[CLEAN_PROBLEM_REQUIRED_COLUMNS].isna().all(axis=1)
    if blank_rows.any():
        errors.append(f"Sono presenti righe completamente vuote: {', '.join(str(i + 2) for i in df.index[blank_rows])}")
    for column in CLEAN_PROBLEM_REQUIRED_COLUMNS:
        empty = df[column].isna() | (df[column].astype(str).str.strip() == "")
        if empty.any():
            errors.append(f"Valori vuoti nella colonna {column}: righe {', '.join(str(i + 2) for i in df.index[empty])}")
    ids = df["problem_id"].fillna("").astype(str).str.strip().str.upper()
    duplicated = sorted(ids[ids.duplicated() & (ids != "")].unique())
    if duplicated:
        errors.append(f"problem_id duplicati: {', '.join(duplicated)}")
    malformed = ids[(ids != "") & ~ids.str.match(r"^P\d{3,}$")]
    if not malformed.empty:
        errors.append(f"problem_id con formato non valido: {', '.join(malformed.unique())}. Usa P001, P002, ...")
    if "source_count" in df.columns:
        counts = pd.to_numeric(df["source_count"], errors="coerce")
        invalid = df["source_count"].notna() & (df["source_count"].astype(str).str.strip() != "") & counts.isna()
        if invalid.any():
            warnings.append(f"source_count non numerico alle righe: {', '.join(str(i + 2) for i in df.index[invalid])}")
    return CleanValidationResult(not errors, errors, warnings)


def import_severity_formbricks(
    input_path: str | Path,
    *,
    output_path: str | Path = "data/processed/heuristics/problem_ratings_long.csv",
    problems_path: str | Path | None = None,
    strict: bool = False,
) -> tuple[pd.DataFrame, list[str]]:
    export = load_formbricks_export(input_path)
    problems = load_clean_problems(problems_path) if problems_path else None
    ratings_long, warnings = normalize_formbricks_severity_export(export, problems=problems, strict=strict)
    target = _write_csv_return(ratings_long, output_path)
    warnings.append(f"File generato: {target}")
    return ratings_long, warnings


def normalize_formbricks_severity_export(
    export: pd.DataFrame,
    *,
    problems: pd.DataFrame | None = None,
    strict: bool = False,
    keep_missing: bool = False,
) -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    evaluator_col = detect_expert_id_column(export.columns)
    if not evaluator_col:
        raise ValueError("Colonna ID esperto non trovata. Inserisci una domanda tipo 'Qual e il tuo id esperto?'.")
    problem_columns = detect_problem_rating_columns(export.columns)
    if not problem_columns:
        raise ValueError("Nessuna colonna rating con pattern [P001] trovata nell'export Formbricks.")
    valid_ids = set()
    if problems is not None:
        valid_ids = set(problems["problem_id"].astype(str).str.strip().str.upper())
        form_ids = {problem_id for problem_id, _ in problem_columns}
        unknown = sorted(form_ids - valid_ids)
        missing = sorted(valid_ids - form_ids)
        if unknown:
            message = f"Problemi presenti nel form ma assenti da clean_problems.csv: {', '.join(unknown)}"
            if strict:
                raise ValueError(message)
            warnings.append(message)
        if missing:
            warnings.append(f"Problemi presenti in clean_problems.csv ma assenti dal form: {', '.join(missing)}")
    rows: list[dict[str, Any]] = []
    for row_index, row in export.iterrows():
        expert_id = _clean_text(row[evaluator_col])
        if not expert_id:
            warnings.append(f"ID esperto mancante alla riga {row_index + 2}: riga ignorata.")
            continue
        for problem_id, column in problem_columns:
            value = row[column]
            if pd.isna(value) or _clean_text(value) == "":
                if keep_missing:
                    rows.append({"expert_id": expert_id, "problem_id": problem_id, "severity": np.nan})
                continue
            severity = normalize_severity_strict(value)
            if severity is None:
                warnings.append(f"Severita non convertibile per {problem_id}, esperto {expert_id}, riga {row_index + 2}: {value}")
                continue
            rows.append({"expert_id": expert_id, "problem_id": problem_id, "severity": severity})
    ratings = pd.DataFrame(rows, columns=["expert_id", "problem_id", "severity"])
    if not ratings.empty:
        ratings["severity"] = pd.to_numeric(ratings["severity"], errors="coerce").astype("Int64")
    return ratings, warnings


def detect_expert_id_column(columns: pd.Index | list[str]) -> str:
    candidates = [column for column in columns if not _is_ignored_formbricks_column(column)]
    aliases = ["id esperto", "id expert", "expert id", "id valutatore", "evaluator id"]
    for column in candidates:
        comp = comparable(column)
        if any(alias in comp for alias in aliases):
            return str(column)
    return str(candidates[0]) if candidates else ""


def detect_problem_rating_columns(columns: pd.Index | list[str]) -> list[tuple[str, str]]:
    detected: list[tuple[str, str]] = []
    seen: set[str] = set()
    for column in columns:
        column_text = str(column)
        if _is_ignored_formbricks_column(column_text):
            continue
        match = PROBLEM_ID_PATTERN.search(column_text)
        if not match:
            continue
        problem_id = match.group(1).upper()
        if problem_id in seen:
            continue
        detected.append((problem_id, column_text))
        seen.add(problem_id)
    return detected


def normalize_severity_strict(value: Any) -> int | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        number = int(text)
        return number if 0 <= number <= 4 else None
    match = re.match(r"^\s*([0-4])\s*(?:[-–:]|$)", text)
    if match:
        return int(match.group(1))
    lower = comparable(text)
    labels = {
        "non e un problema": 0,
        "non è un problema": 0,
        "problema cosmetico": 1,
        "problema minore": 2,
        "problema maggiore": 3,
        "problema critico": 4,
    }
    for label, number in labels.items():
        if comparable(label) in lower:
            return number
    return None


def join_clean_problems_with_ratings(
    problems_path: str | Path,
    ratings_path: str | Path,
    *,
    output_path: str | Path = "data/processed/heuristics/heuristic_final_dataset.csv",
    strict: bool = False,
) -> tuple[pd.DataFrame, list[str]]:
    problems = load_clean_problems(problems_path)
    ratings = pd.read_csv(resolve_path(ratings_path))
    final, warnings = build_heuristic_final_dataset(problems, ratings, strict=strict)
    target = _write_csv_return(final, output_path)
    warnings.append(f"File generato: {target}")
    return final, warnings


def build_heuristic_final_dataset(problems: pd.DataFrame, ratings: pd.DataFrame, *, strict: bool = False) -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    required = {"expert_id", "problem_id", "severity"}
    missing = required - set(ratings.columns)
    if missing:
        raise ValueError(f"Colonne mancanti nel file rating long: {', '.join(sorted(missing))}")
    ratings = ratings.copy()
    ratings["problem_id"] = ratings["problem_id"].astype(str).str.strip().str.upper()
    ratings["severity"] = pd.to_numeric(ratings["severity"], errors="coerce")
    invalid = ratings[ratings["severity"].notna() & ~ratings["severity"].between(0, 4)]
    if not invalid.empty:
        raise ValueError("Il file rating contiene severita fuori scala 0-4.")
    valid_ids = set(problems["problem_id"].astype(str))
    unknown = sorted(set(ratings["problem_id"]) - valid_ids)
    if unknown:
        message = f"Rating riferiti a problem_id inesistenti: {', '.join(unknown)}"
        if strict:
            raise ValueError(message)
        warnings.append(message)
        ratings = ratings[ratings["problem_id"].isin(valid_ids)]
    unrated = sorted(valid_ids - set(ratings["problem_id"]))
    if unrated:
        warnings.append(f"Problemi senza valutazioni: {', '.join(unrated)}")
    final = problems.merge(ratings, on="problem_id", how="left")
    ordered = [
        "problem_id",
        "app",
        "screen",
        "heuristic",
        "title",
        "description",
        "expert_id",
        "severity",
        "source_count",
        "notes",
        "raw_problem_ids",
        "recommendation",
        "impact",
    ]
    return final[[column for column in ordered if column in final.columns]], warnings


def analyze_final_heuristics_dataset(
    dataset_path: str | Path,
    *,
    out_dir: str | Path = "outputs/heuristics",
    processed_dir: str | Path = "data/processed/heuristics",
) -> FinalSeverityPipelineResult:
    final = pd.read_csv(resolve_path(dataset_path))
    return write_final_heuristics_outputs(final, out_dir=out_dir, processed_dir=processed_dir)


def run_severity_pipeline(
    *,
    problems_path: str | Path = "data/processed/heuristics/clean_problems.csv",
    ratings_export_path: str | Path = "data/formbricks_raw/heuristics/severity_ratings_export.csv",
    out_dir: str | Path = "outputs/heuristics",
    processed_dir: str | Path = "data/processed/heuristics",
    strict: bool = False,
) -> FinalSeverityPipelineResult:
    validation = validate_clean_problems(problems_path)
    if validation.errors:
        raise ValueError("\n".join(validation.errors))
    problems = load_clean_problems(problems_path)
    ratings_export = load_formbricks_export(ratings_export_path)
    ratings_long, warnings = normalize_formbricks_severity_export(ratings_export, problems=problems, strict=strict)
    output_root = resolve_path(processed_dir)
    ratings_path = output_root / "problem_ratings_long.csv"
    final_path = output_root / "heuristic_final_dataset.csv"
    _write_csv_return(ratings_long, ratings_path)
    final, join_warnings = build_heuristic_final_dataset(problems, ratings_long, strict=strict)
    _write_csv_return(final, final_path)
    result = write_final_heuristics_outputs(final, out_dir=out_dir, processed_dir=processed_dir)
    result.warnings = validation.warnings + warnings + join_warnings + result.warnings
    result.output_paths = [ratings_path, final_path, *result.output_paths]
    result.clean_problems = problems
    result.ratings_long = ratings_long
    result.final_dataset = final
    return result


def write_final_heuristics_outputs(
    final: pd.DataFrame,
    *,
    out_dir: str | Path = "outputs/heuristics",
    processed_dir: str | Path = "data/processed/heuristics",
) -> FinalSeverityPipelineResult:
    warnings: list[str] = []
    processed_root = resolve_path(processed_dir)
    output_root = resolve_path(out_dir)
    charts_dir = output_root / "charts"
    tables_dir = output_root / "tables"
    texts_dir = output_root / "texts"
    for directory in [processed_root, charts_dir, tables_dir, texts_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    clean = _clean_from_final(final)
    ratings = final[["expert_id", "problem_id", "severity"]].dropna(subset=["expert_id", "severity"]).copy()
    problem_summary = build_problem_severity_summary(clean, ratings)
    matrix = build_expert_problem_matrix(clean, ratings)
    heuristic_summary = build_group_severity_summary(final, "heuristic", "heuristic_severity_summary")
    app_summary = build_group_severity_summary(final, "app", "app_severity_summary")
    paths = [
        _write_csv_return(problem_summary, processed_root / "problem_severity_summary.csv"),
        _write_csv_return(matrix, processed_root / "expert_problem_matrix.csv"),
        _write_csv_return(heuristic_summary, processed_root / "heuristic_severity_summary.csv"),
        _write_csv_return(app_summary, processed_root / "app_severity_summary.csv"),
    ]
    table_outputs = {
        "final_problems_table.csv": clean,
        "problem_ranking.csv": problem_summary.sort_values(["mean_severity", "ratings_count"], ascending=[False, False]),
        "expert_problem_matrix.csv": matrix,
        "heuristic_severity_summary.csv": heuristic_summary,
        "app_severity_summary.csv": app_summary,
        "critical_problems.csv": problem_summary[problem_summary["mean_severity"] >= 3].sort_values("mean_severity", ascending=False),
        "highest_disagreement.csv": problem_summary.sort_values("std_severity", ascending=False),
    }
    for filename, table in table_outputs.items():
        paths.append(_write_csv_return(table, tables_dir / filename))
    _plot_final_heuristics(problem_summary, matrix, heuristic_summary, app_summary, final, charts_dir)
    _write_final_texts(problem_summary, heuristic_summary, app_summary, clean, texts_dir)
    aliases = {
        "heuristics_top_problems.png": charts_dir / "top_problems.png",
        "heuristics_problem_expert_heatmap.png": charts_dir / "problem_expert_heatmap.png",
        "heuristics_by_app.png": charts_dir / "severity_by_app.png",
        "heuristics_by_heuristic.png": charts_dir / "severity_by_heuristic.png",
        "heuristics_summary.md": texts_dir / "summary.md",
        "heuristics_top_findings.md": texts_dir / "top_findings.md",
    }
    for alias, source in aliases.items():
        if source.exists():
            target = output_root / alias
            if source.suffix == ".png":
                import shutil

                shutil.copy2(source, target)
            else:
                target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            paths.append(target)
    critical_table = tables_dir / "critical_problems.csv"
    if critical_table.exists():
        paths.append(output_root / "heuristics_critical_problems_table.csv")
        (output_root / "heuristics_critical_problems_table.csv").write_text(critical_table.read_text(encoding="utf-8-sig"), encoding="utf-8")
    return FinalSeverityPipelineResult(clean, ratings, final, problem_summary, warnings, paths)


def build_problem_severity_summary(clean: pd.DataFrame, ratings: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for problem in clean.itertuples(index=False):
        problem_id = getattr(problem, "problem_id")
        subset = ratings[ratings["problem_id"].astype(str) == problem_id]
        values = pd.to_numeric(subset["severity"], errors="coerce").dropna()
        rows.append(
            {
                "problem_id": problem_id,
                "app": getattr(problem, "app", ""),
                "screen": getattr(problem, "screen", ""),
                "heuristic": getattr(problem, "heuristic", ""),
                "title": getattr(problem, "title", ""),
                "mean_severity": round(float(values.mean()), 2) if not values.empty else np.nan,
                "median_severity": round(float(values.median()), 2) if not values.empty else np.nan,
                "std_severity": round(float(values.std(ddof=1)), 2) if len(values) > 1 else 0.0,
                "min_severity": int(values.min()) if not values.empty else np.nan,
                "max_severity": int(values.max()) if not values.empty else np.nan,
                "ratings_count": int(values.count()),
            }
        )
    return pd.DataFrame(rows)


def build_expert_problem_matrix(clean: pd.DataFrame, ratings: pd.DataFrame) -> pd.DataFrame:
    if ratings.empty:
        return clean[["problem_id", "title"]].assign(mean_severity=np.nan)
    pivot = ratings.pivot_table(index="problem_id", columns="expert_id", values="severity", aggfunc="first")
    matrix = clean[["problem_id", "title"]].merge(pivot.reset_index(), on="problem_id", how="left")
    expert_columns = [column for column in matrix.columns if column not in {"problem_id", "title"}]
    matrix["mean_severity"] = matrix[expert_columns].apply(lambda col: pd.to_numeric(col, errors="coerce")).mean(axis=1).round(2) if expert_columns else np.nan
    return matrix


def build_group_severity_summary(final: pd.DataFrame, group_col: str, _: str = "") -> pd.DataFrame:
    if final.empty or group_col not in final:
        return pd.DataFrame(columns=[group_col, "problems_count", "ratings_count", "mean_severity", "median_severity"])
    base = final.copy()
    base["severity"] = pd.to_numeric(base["severity"], errors="coerce")
    rows = []
    for key, group in base.groupby(group_col, dropna=False):
        rows.append(
            {
                group_col: key,
                "problems_count": int(group["problem_id"].nunique()),
                "ratings_count": int(group["severity"].count()),
                "mean_severity": round(float(group["severity"].mean()), 2) if group["severity"].notna().any() else np.nan,
                "median_severity": round(float(group["severity"].median()), 2) if group["severity"].notna().any() else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values("mean_severity", ascending=False, na_position="last")


def _is_ignored_formbricks_column(column: Any) -> bool:
    text = str(column).strip()
    comp = comparable(text)
    return text.endswith("- Option ID") or comp in FORMBRICKS_METADATA_COLUMNS or comp.endswith(" option id")


def _clean_from_final(final: pd.DataFrame) -> pd.DataFrame:
    columns = CLEAN_PROBLEM_REQUIRED_COLUMNS + [column for column in CLEAN_PROBLEM_OPTIONAL_COLUMNS if column in final.columns]
    return final[[column for column in columns if column in final.columns]].drop_duplicates("problem_id").copy()


def _plot_final_heuristics(
    problem_summary: pd.DataFrame,
    matrix: pd.DataFrame,
    heuristic_summary: pd.DataFrame,
    app_summary: pd.DataFrame,
    final: pd.DataFrame,
    charts_dir: Path,
) -> None:
    _plot_metric_bar(problem_summary.sort_values("problem_id"), "problem_id", "mean_severity", "Severita media per problema", charts_dir / "mean_severity_by_problem.png")
    _plot_metric_bar(problem_summary.sort_values("mean_severity", ascending=False).head(10), "problem_id", "mean_severity", "Top problemi per severita", charts_dir / "top_problems.png")
    _plot_problem_expert_heatmap(matrix, charts_dir / "problem_expert_heatmap.png")
    _plot_metric_bar(heuristic_summary, "heuristic", "mean_severity", "Severita media per euristica", charts_dir / "severity_by_heuristic.png")
    _plot_metric_bar(app_summary, "app", "mean_severity", "Severita media per app", charts_dir / "severity_by_app.png")
    if "severity" in final:
        values = pd.to_numeric(final["severity"], errors="coerce").dropna()
        if not values.empty:
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.hist(values, bins=np.arange(-0.5, 5.5, 1), color="#3B82F6", edgecolor="white")
            ax.set_xticks(range(5))
            style_axis(ax, "Distribuzione severita", "Severita Nielsen 0-4", "Frequenza")
            fig.tight_layout()
            fig.savefig(charts_dir / "severity_distribution.png", dpi=180, bbox_inches="tight")
            plt.close(fig)
    _plot_count_from_summary(problem_summary, "heuristic", charts_dir / "problem_count_by_heuristic.png", "Conteggio problemi per euristica")
    _plot_count_from_summary(problem_summary, "screen", charts_dir / "problem_count_by_screen.png", "Conteggio problemi per schermata")


def _plot_metric_bar(df: pd.DataFrame, x: str, y: str, title: str, path: Path) -> None:
    if df.empty or x not in df or y not in df:
        return
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(max(7, len(df) * 0.55), 4.5))
    sns.barplot(data=df, x=x, y=y, hue=x, palette="viridis", legend=False, ax=ax)
    ax.set_ylim(0, 4)
    ax.tick_params(axis="x", rotation=30)
    style_axis(ax, title, "", "Severita media")
    fig.tight_layout()
    fig.savefig(target, dpi=180, bbox_inches="tight")
    plt.close(fig)


def _plot_problem_expert_heatmap(matrix: pd.DataFrame, path: Path) -> None:
    if matrix.empty:
        return
    heat = matrix.drop(columns=["title", "mean_severity"], errors="ignore").set_index("problem_id")
    if heat.empty:
        return
    heat = heat.apply(lambda col: pd.to_numeric(col, errors="coerce")).astype(float)
    fig, ax = plt.subplots(figsize=(max(7, heat.shape[1] * 0.65), max(4, heat.shape[0] * 0.35)))
    sns.heatmap(heat, vmin=0, vmax=4, cmap="YlOrRd", annot=True, fmt=".0f", linewidths=0.4, linecolor="#E5E7EB", ax=ax)
    style_axis(ax, "Matrice problemi-esperti", "Esperti", "Problemi")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def _plot_count_from_summary(summary: pd.DataFrame, column: str, path: Path, title: str) -> None:
    if summary.empty or column not in summary:
        return
    counts = summary.groupby(column, dropna=False).size().reset_index(name="count")
    _plot_count_bar(counts, column, title, path)


def _write_final_texts(problem_summary: pd.DataFrame, heuristic_summary: pd.DataFrame, app_summary: pd.DataFrame, clean: pd.DataFrame, texts_dir: Path) -> None:
    total = len(clean)
    rated = int(problem_summary["ratings_count"].gt(0).sum()) if "ratings_count" in problem_summary else 0
    mean = pd.to_numeric(problem_summary.get("mean_severity", pd.Series(dtype=float)), errors="coerce").mean()
    top = problem_summary.sort_values("mean_severity", ascending=False).head(3)
    top_text = ", ".join(f"{row.problem_id} ({row.title}, {row.mean_severity}/4)" for row in top.itertuples()) if not top.empty else "n.d."
    texts = {
        "summary.md": [
            "## Sintesi valutazione euristica",
            "",
            f"Dopo la deduplicazione sono stati identificati {total} problemi unici. {rated} problemi hanno almeno una valutazione di severita.",
            f"La severita media complessiva e pari a {mean:.2f}/4." if not np.isnan(mean) else "La severita media complessiva non e calcolabile per assenza di rating.",
        ],
        "top_findings.md": [
            "## Principali criticita",
            "",
            f"I problemi con severita media piu alta sono: {top_text}.",
        ],
        "app_comparison.md": [
            "## Confronto per app",
            "",
            _group_text(app_summary, "app"),
        ],
        "heuristic_summary.md": [
            "## Sintesi per euristica",
            "",
            _group_text(heuristic_summary, "heuristic"),
        ],
    }
    for filename, lines in texts.items():
        (texts_dir / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _group_text(summary: pd.DataFrame, label_col: str) -> str:
    if summary.empty:
        return "Non sono disponibili dati sufficienti per il confronto."
    parts = []
    for row in summary.itertuples(index=False):
        label = getattr(row, label_col)
        mean = getattr(row, "mean_severity")
        problems = getattr(row, "problems_count")
        parts.append(f"{label}: severita media {mean}/4 su {problems} problemi")
    return "; ".join(parts) + "."


def build_problems_slide_table(summary: pd.DataFrame) -> pd.DataFrame:
    source_columns = ["final_problem_id", "app", "short_description", "heuristics", "severity_mean", "priority_band"]
    display_columns = ["ID problema", "App", "Problema", "Euristiche", "Severità media", "Priorità"]
    if summary.empty:
        return pd.DataFrame(columns=display_columns)
    table = summary.copy()
    for column in source_columns:
        if column not in table.columns:
            table[column] = ""
    table = table[source_columns].copy()
    table["short_description"] = table["short_description"].astype(str).map(lambda text: text if len(text) <= 105 else text[:102].rstrip() + "...")
    table.columns = display_columns
    return table


def normalize_severity_ratings(ratings: pd.DataFrame, problems: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    evaluator_col = _find_column(list(ratings.columns), ["evaluator_id", "id valutatore", "ID valutatore"])
    if "final_problem_id" not in problems.columns and "problem_group_id" in problems.columns:
        problems = problems.rename(columns={"problem_group_id": "final_problem_id"})
    problem_col = _find_column(list(ratings.columns), ["final_problem_id", "problem_group_id", "problem_id", "problema", "id problema"])
    severity_col = _find_column(list(ratings.columns), ["severity", "severità", "severità", "rating"])
    valid_problem_ids = set(problems.get("final_problem_id", pd.Series(dtype=str)).astype(str))
    rows: list[dict[str, Any]] = []
    if evaluator_col and problem_col and severity_col:
        for index, row in ratings.iterrows():
            severity = normalize_severity(row[severity_col])
            problem_id = _clean_text(row[problem_col])
            if severity is None:
                warnings.append(f"severità fuori scala riga {index + 2}: {row[severity_col]}")
                continue
            if problem_id not in valid_problem_ids:
                warnings.append(f"Rating riferito a problem_id inesistente: {problem_id}")
            rows.append({"evaluator_id": _clean_text(row[evaluator_col]), "final_problem_id": problem_id, "severity": severity})
    else:
        if not evaluator_col:
            warnings.append("Colonna evaluator_id non trovata nel CSV severità.")
        for index, row in ratings.iterrows():
            evaluator = _clean_text(row[evaluator_col]) if evaluator_col else f"EU{index + 1:02d}"
            for problem_id in sorted(valid_problem_ids):
                column = _find_column(list(ratings.columns), [problem_id])
                if not column:
                    continue
                severity = normalize_severity(row[column])
                if severity is None and _clean_text(row[column]):
                    warnings.append(f"severità fuori scala per {problem_id}, riga {index + 2}: {row[column]}")
                    continue
                if severity is not None:
                    rows.append({"evaluator_id": evaluator, "final_problem_id": problem_id, "severity": severity})
    return pd.DataFrame(rows, columns=["evaluator_id", "final_problem_id", "severity"]), warnings


def summarize_severity_ratings(problems: pd.DataFrame, ratings_long: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for problem in problems.itertuples(index=False):
        problem_id = str(getattr(problem, "final_problem_id"))
        subset = ratings_long[ratings_long["final_problem_id"].astype(str) == problem_id]
        values = pd.to_numeric(subset["severity"], errors="coerce").dropna()
        evaluator_ids = sorted(subset["evaluator_id"].dropna().astype(str).unique())
        mean = float(values.mean()) if not values.empty else np.nan
        sd = float(values.std(ddof=1)) if len(values) > 1 else 0.0
        median = float(values.median()) if not values.empty else np.nan
        iqr = _iqr(values)
        rows.append(
            {
                "final_problem_id": problem_id,
                "app": getattr(problem, "app", ""),
                "short_description": getattr(problem, "short_description", ""),
                "long_description": getattr(problem, "long_description", ""),
                "heuristics": getattr(problem, "heuristics", ""),
                "evaluator_ids": ";".join(evaluator_ids),
                "n_ratings": int(len(values)),
                "severity_mean": round(mean, 2) if not np.isnan(mean) else np.nan,
                "severity_sd": round(sd, 2),
                "severity_median": round(median, 2) if not np.isnan(median) else np.nan,
                "severity_iqr": round(iqr, 2) if not np.isnan(iqr) else np.nan,
                "priority_band": priority_band(mean),
            }
        )
    return pd.DataFrame(rows)


def priority_band(severity_mean: float, thresholds: dict[str, float] | None = None) -> str:
    thresholds = thresholds or {"A": 3.25, "B": 2.0}
    if severity_mean is None or np.isnan(severity_mean):
        return "unrated"
    if severity_mean >= thresholds["A"]:
        return "A"
    if severity_mean >= thresholds["B"]:
        return "B"
    return "C"


def final_evaluator_problem_matrix(ratings_long: pd.DataFrame) -> pd.DataFrame:
    evaluators = sorted(ratings_long["evaluator_id"].dropna().astype(str).unique()) if not ratings_long.empty else []
    problems = sorted(ratings_long["final_problem_id"].dropna().astype(str).unique()) if not ratings_long.empty else []
    matrix = pd.DataFrame(0, index=evaluators, columns=problems, dtype=int)
    for row in ratings_long.itertuples():
        matrix.loc[str(row.evaluator_id), str(row.final_problem_id)] = 1
    return matrix


def _count(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if df.empty or column not in df:
        return pd.DataFrame(columns=[column, "count"])
    return df.groupby(column, dropna=False).size().reset_index(name="count")


def _heuristic_counts(raw_table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for value in raw_table.get("heuristics", pd.Series(dtype=str)).fillna(""):
        for code in [part.strip() for part in str(value).split(";") if part.strip()]:
            rows.append({"heuristic": code})
    if not rows:
        return pd.DataFrame(columns=["heuristic", "count"])
    return pd.DataFrame(rows).value_counts("heuristic").reset_index(name="count").sort_values("heuristic")


def _write_csv_return(df: pd.DataFrame, path: str | Path) -> Path:
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target, index=False, encoding="utf-8-sig")
    return target


def _plot_profile_charts(profiles: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for field in ["gender", "age_group", "occupation", "familiarity", "usability_experience", "domain_experience"]:
        if field not in profiles or profiles[field].replace("", pd.NA).dropna().empty:
            continue
        counts = profiles[field].replace("", "n.d.").value_counts().reset_index()
        counts.columns = [field, "count"]
        _plot_count_bar(counts, field, f"Distribuzione {field}", output_dir / f"{field}.png")


def _plot_count_bar(df: pd.DataFrame, x: str, title: str, path: str | Path) -> None:
    if df.empty or x not in df:
        return
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.barplot(data=df, x=x, y="count", hue=x, palette="viridis", legend=False, ax=ax)
    ax.tick_params(axis="x", rotation=25)
    style_axis(ax, title, "", "Conteggio")
    fig.tight_layout()
    fig.savefig(target, dpi=180, bbox_inches="tight")
    fig.savefig(target.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def _plot_matrix(matrix: pd.DataFrame, title: str, path: str | Path) -> None:
    if matrix.empty:
        return
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(max(8, matrix.shape[1] * 0.45), max(3.5, matrix.shape[0] * 0.4)))
    sns.heatmap(matrix, cmap="YlGnBu", cbar=False, linewidths=0.4, linecolor="#E5E7EB", ax=ax)
    style_axis(ax, title, "Problemi", "Valutatori")
    fig.tight_layout()
    fig.savefig(target, dpi=180, bbox_inches="tight")
    fig.savefig(target.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def _write_raw_report(
    report_path: str | Path,
    expert_profiles: pd.DataFrame,
    raw_table: pd.DataFrame,
    problem_counts_by_app: pd.DataFrame,
    problem_counts_by_evaluator: pd.DataFrame,
    heuristic_counts: pd.DataFrame,
    warnings: list[str],
    ignored_empty: int,
    output_paths: list[Path],
) -> None:
    def counts_text(df: pd.DataFrame, key: str) -> str:
        return ", ".join(f"{row[key]}={row['count']}" for _, row in df.iterrows()) if not df.empty else "n.d."

    lines = [
        "# Report valutazione euristica - raccolta problemi grezzi",
        "",
        "## Composizione esperti",
        f"- Numero esperti: {expert_profiles['evaluator_id'].nunique() if 'evaluator_id' in expert_profiles else 0}",
        f"- Distribuzione genere: {_profile_distribution(expert_profiles, 'gender')}",
        f"- Distribuzione eta: {_profile_distribution(expert_profiles, 'age_group')}",
        f"- Distribuzione occupazione: {_profile_distribution(expert_profiles, 'occupation')}",
        f"- Distribuzione familiarita: {_profile_distribution(expert_profiles, 'familiarity')}",
        "",
        "## Problemi raccolti",
        f"- Numero totale problemi grezzi: {len(raw_table)}",
        f"- Problemi per app: {counts_text(problem_counts_by_app, 'app')}",
        f"- Problemi per valutatore: {counts_text(problem_counts_by_evaluator, 'evaluator_id')}",
        f"- Euristiche più violate: {counts_text(heuristic_counts.head(5), 'heuristic')}",
        "",
        "## qualità dati",
        f"- Blocchi vuoti ignorati: {ignored_empty}",
        f"- Problemi senza app: {int((raw_table['completion_status'] == 'missing_app').sum()) if not raw_table.empty else 0}",
        f"- Problemi senza descrizione: {int((raw_table['completion_status'] == 'missing_description').sum()) if not raw_table.empty else 0}",
        f"- Problemi senza euristiche: {int((raw_table['completion_status'] == 'missing_heuristics').sum()) if not raw_table.empty else 0}",
        "",
        "## Warning",
        *(warnings if warnings else ["Nessun warning rilevante."]),
        "",
        "## File generati",
        *[f"- `{path}`" for path in output_paths],
        "",
    ]
    target = resolve_path(report_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")


def _write_final_report(report_path: str | Path, summary: pd.DataFrame, warnings: list[str], output_paths: list[Path]) -> None:
    lines = [
        "# Report valutazione euristica - severità problemi consolidati",
        "",
        f"- Problemi consolidati: {len(summary)}",
        f"- Problemi senza rating: {int((summary['priority_band'] == 'unrated').sum()) if not summary.empty else 0}",
        "",
        "## Warning",
        *(warnings if warnings else ["Nessun warning rilevante."]),
        "",
        "## File generati",
        *[f"- `{path}`" for path in output_paths],
        "",
    ]
    target = resolve_path(report_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")


def _profile_distribution(profiles: pd.DataFrame, field: str) -> str:
    if field not in profiles:
        return "n.d."
    counts = profiles[field].replace("", pd.NA).dropna().value_counts()
    return ", ".join(f"{key}={value}" for key, value in counts.items()) if not counts.empty else "n.d."


def _iqr(values: pd.Series) -> float:
    if values.empty:
        return np.nan
    return float(values.quantile(0.75) - values.quantile(0.25))


def _clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()
