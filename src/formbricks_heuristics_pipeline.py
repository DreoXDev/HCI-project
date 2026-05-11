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
            if field == "long_description" and any(token in comp for token in ["dettagliata", "dettagliato", "descrizione piu"]):
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
        _write_csv_return(matrix.reset_index(names="evaluator_id"), output_root / "final_evaluator_problem_matrix.csv"),
        _write_csv_return(bands, output_root / "problem_priority_bands.csv"),
    ]
    _plot_count_bar(bands, "priority_band", "Fasce priorita problemi", figures_root / "final_priority_bands.png")
    _plot_matrix(matrix, "Matrice finale valutatore-problema", figures_root / "final_evaluator_problem_matrix.png")
    _write_final_report(report_path, summary, warnings, paths)
    return HeuristicsSeverityResult(ratings_long, summary, warnings, paths)


def normalize_severity_ratings(ratings: pd.DataFrame, problems: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    evaluator_col = _find_column(list(ratings.columns), ["evaluator_id", "id valutatore", "ID valutatore"])
    if "final_problem_id" not in problems.columns and "problem_group_id" in problems.columns:
        problems = problems.rename(columns={"problem_group_id": "final_problem_id"})
    problem_col = _find_column(list(ratings.columns), ["final_problem_id", "problem_group_id", "problem_id", "problema", "id problema"])
    severity_col = _find_column(list(ratings.columns), ["severity", "severita", "severità", "rating"])
    valid_problem_ids = set(problems.get("final_problem_id", pd.Series(dtype=str)).astype(str))
    rows: list[dict[str, Any]] = []
    if evaluator_col and problem_col and severity_col:
        for index, row in ratings.iterrows():
            severity = normalize_severity(row[severity_col])
            problem_id = _clean_text(row[problem_col])
            if severity is None:
                warnings.append(f"Severita fuori scala riga {index + 2}: {row[severity_col]}")
                continue
            if problem_id not in valid_problem_ids:
                warnings.append(f"Rating riferito a problem_id inesistente: {problem_id}")
            rows.append({"evaluator_id": _clean_text(row[evaluator_col]), "final_problem_id": problem_id, "severity": severity})
    else:
        if not evaluator_col:
            warnings.append("Colonna evaluator_id non trovata nel CSV severita.")
        for index, row in ratings.iterrows():
            evaluator = _clean_text(row[evaluator_col]) if evaluator_col else f"EU{index + 1:02d}"
            for problem_id in sorted(valid_problem_ids):
                column = _find_column(list(ratings.columns), [problem_id])
                if not column:
                    continue
                severity = normalize_severity(row[column])
                if severity is None and _clean_text(row[column]):
                    warnings.append(f"Severita fuori scala per {problem_id}, riga {index + 2}: {row[column]}")
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
    df.to_csv(target, index=False)
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
        f"- Euristiche piu violate: {counts_text(heuristic_counts.head(5), 'heuristic')}",
        "",
        "## Qualita dati",
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
        "# Report valutazione euristica - severita problemi consolidati",
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
