from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re

import pandas as pd

from .config import resolve_path
from .report_quality.final_deck_text_audit import audit_final_deck_text
from .users_time import load_users_time_long, validate_users_time_long


BANNED_OUTPUT_PATTERNS = [
    "Output generato dalla pipeline",
    "Verificare la lettura narrativa",
    "Spazio per",
    "TODO",
    "FIXME",
    "Lorem ipsum",
    "slides/assets",
    "outputs/",
    "[object Object]",
    "NaN",
    "None",
    "null",
    "undefined",
    "PARTIAL_DATA",
]


@dataclass
class FinalDataValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, condition: bool, ok: str, fail: str) -> None:
        if condition:
            self.warnings.append(f"OK: {ok}")
        else:
            self.errors.append(f"ERROR: {fail}")


def validate_final_data(config: dict, *, strict: bool = False) -> FinalDataValidationResult:
    result = FinalDataValidationResult()
    _validate_questionnaire(result)
    _validate_users_time(result, config)
    _validate_heuristics(result)
    _validate_processed_questionnaire(result)
    _validate_evaluator_outputs(result)
    _validate_static_texts(result)
    _validate_existing_outputs(result)
    _validate_existing_decks(result)
    if strict and result.errors:
        return result
    return result


def format_final_data_validation(result: FinalDataValidationResult) -> str:
    lines = ["# Final Data Validation", ""]
    lines.extend(result.warnings)
    lines.extend(result.errors)
    lines.extend(["", f"STATUS: {'FINAL_DATA' if result.ok else 'NEEDS_FIXES'}"])
    return "\n".join(lines) + "\n"


def _validate_questionnaire(result: FinalDataValidationResult) -> None:
    path = resolve_path("data/formbricks_raw/questionnaire/users_questionnaire_export.csv")
    if not path.exists():
        result.errors.append(f"ERROR: questionario mancante: {path}")
        return
    df = pd.read_csv(path, encoding="utf-8-sig")
    finished = df.get("Finished", pd.Series(dtype=str)).astype(str).str.casefold().isin({"yes", "true", "1", "si", "sì"})
    result.add(int(finished.sum()) == 24, "questionario utenti: 24 risposte finite", f"questionario utenti: {int(finished.sum())}/24 risposte finite")


def _validate_users_time(result: FinalDataValidationResult, config: dict) -> None:
    path = resolve_path("data/raw/users_time.csv")
    if not path.exists():
        result.errors.append(f"ERROR: users_time mancante: {path}")
        return
    raw = load_users_time_long(path)
    validation = validate_users_time_long(raw, config.get("users_time", {}).get("required_columns"), expected_users=24, tasks=config.get("users_time", {}).get("tasks", []))
    if not validation.is_valid:
        result.errors.extend(f"ERROR: {message}" for message in validation.messages)
        return
    df = validation.normalized
    result.add(len(df) == 144, "user testing: 144 righe tempo-task", f"user testing: {len(df)}/144 righe tempo-task")
    result.add(df["user_id"].nunique() == 24, "user testing: 24 utenti distinti", f"user testing: {df['user_id'].nunique()}/24 utenti distinti")
    expected_pairs = {("Deliveroo", "T01"), ("Deliveroo", "T02"), ("Deliveroo", "T03"), ("Glovo", "T01"), ("Glovo", "T02"), ("Glovo", "T03")}
    missing = []
    for user_id, group in df.groupby("user_id"):
        pairs = {(str(row.app), str(row.task_id)) for row in group.itertuples()}
        if pairs != expected_pairs:
            missing.append(str(user_id))
    result.add(not missing, "ogni utente ha le 6 combinazioni app x task", f"combinazioni app x task mancanti o extra per: {', '.join(missing[:8])}")


def _validate_heuristics(result: FinalDataValidationResult) -> None:
    path = resolve_path("data/processed/heuristics/clean_problems.csv")
    ratings = resolve_path("data/formbricks_raw/heuristics/severity_ratings_export.csv")
    if not path.exists():
        result.errors.append(f"ERROR: clean_problems mancante: {path}")
        return
    df = pd.read_csv(path, encoding="utf-8-sig")
    expected = [f"PD{idx:02d}" for idx in range(1, 21)] + [f"PG{idx:02d}" for idx in range(1, 21)]
    ids = df.get("problem_id", pd.Series(dtype=str)).astype(str).str.strip().tolist()
    result.add(ids == expected, "clean_problems contiene esattamente PD01-PD20 e PG01-PG20", "clean_problems non contiene esattamente PD01-PD20 e PG01-PG20 in ordine stabile")
    result.add(len(df) == 40, "problemi euristici: 40 problemi", f"problemi euristici: {len(df)}/40")
    descriptions = df.get("description", pd.Series(dtype=str)).fillna("").astype(str).str.strip()
    too_short = df.loc[descriptions.str.len() < 40, "problem_id"].astype(str).tolist() if "problem_id" in df else []
    ellipsis = df.loc[descriptions.str.contains(r"\.\.\.|…", regex=True), "problem_id"].astype(str).tolist() if "problem_id" in df else []
    result.add(not too_short and not ellipsis, "descrizioni problema complete", f"descrizioni problema vuote, brevi o troncate: {', '.join((too_short + ellipsis)[:8])}")
    if ratings.exists():
        ratings_df = pd.read_csv(ratings, encoding="utf-8-sig")
        evaluator_col = next((column for column in ratings_df.columns if "id esperto" in column.casefold() or "evaluator" in column.casefold()), "")
        experts = ratings_df[evaluator_col].dropna().astype(str).str.strip().nunique() if evaluator_col else len(ratings_df)
        result.add(experts == 8, "esperti severita: 8 esperti", f"esperti severita: {experts}/8")
    else:
        result.errors.append(f"ERROR: severity_ratings_export mancante: {ratings}")


def _validate_processed_questionnaire(result: FinalDataValidationResult) -> None:
    root = resolve_path("data/processed/questionnaire")
    required = [
        "questionnaire_demographics.csv",
        "questionnaire_ueq_long.csv",
        "questionnaire_ueq_summary.csv",
        "questionnaire_nps_long.csv",
        "questionnaire_nps_summary.csv",
    ]
    missing = [name for name in required if not (root / name).exists()]
    result.add(not missing, "derivati questionario ufficiali presenti", f"derivati questionario mancanti: {', '.join(missing)}")
    long_path = root / "questionnaire_ueq_long.csv"
    if long_path.exists():
        df = pd.read_csv(long_path)
        scores = pd.to_numeric(df.get("score_minus3_plus3"), errors="coerce")
        result.add(scores.between(-3, 3).all(), "UEQ normalizzato nel range -3..+3", "UEQ normalizzato fuori range -3..+3")


def _validate_static_texts(result: FinalDataValidationResult) -> None:
    text = resolve_path("slides/content/reference_static_texts.md").read_text(encoding="utf-8")
    result.add("FINAL_DATA" in text and "Dati finali" in text, "testi statici marcati FINAL_DATA", "testi statici ancora non marcati FINAL_DATA")
    result.add("Menù Cheeseburger Singolo" in text, "Task 2 usa Menù Cheeseburger Singolo", "Task 2 non usa Menù Cheeseburger Singolo")
    result.add("Cheeseburger Doppio" in text and re.search(r"\b2\b", text), "Task 3 richiede Cheeseburger Doppio e quantita 2", "Task 3 non contiene Cheeseburger Doppio e quantita 2")


def _validate_evaluator_outputs(result: FinalDataValidationResult) -> None:
    path = resolve_path("outputs/tables/heuristics_evaluators_slide.csv")
    if not path.exists():
        result.warnings.append("WARNING: tabella valutatori slide non ancora generata")
    else:
        df = pd.read_csv(path, encoding="utf-8-sig")
        column = "Valutatore" if "Valutatore" in df.columns else df.columns[0]
        count = df[column].dropna().astype(str).str.strip().nunique()
        result.add(count == 8, "tabella valutatori slide: 8 esperti", f"tabella valutatori slide: {count}/8 esperti")

    profiles_path = resolve_path("outputs/tables/heuristics_expert_profiles.csv")
    expertise_path = resolve_path("outputs/figures/dark/heuristics/expertise_matrix.png")
    if profiles_path.exists():
        profiles = pd.read_csv(profiles_path, encoding="utf-8-sig")
        profile_count = profiles["evaluator_id"].dropna().astype(str).str.strip().nunique() if "evaluator_id" in profiles.columns else 0
        result.add(profile_count == 8, "matrice expertise: 8 profili valutatore", f"matrice expertise: {profile_count}/8 profili valutatore")
    else:
        result.errors.append(f"ERROR: profili expertise mancanti: {profiles_path}")
    result.add(expertise_path.exists(), "grafico matrice expertise presente", f"grafico matrice expertise mancante: {expertise_path}")

    expected = {
        "deliveroo": [f"PD{idx:02d}" for idx in range(1, 21)],
        "glovo": [f"PG{idx:02d}" for idx in range(1, 21)],
    }
    for slug, expected_ids in expected.items():
        matrix_path = resolve_path(f"outputs/tables/problem_evaluator_matrix_{slug}.csv")
        if not matrix_path.exists():
            result.warnings.append(f"WARNING: matrice problemi-valutatori {slug} non ancora generata")
            continue
        matrix = pd.read_csv(matrix_path, encoding="utf-8-sig")
        problem_cols = [column for column in matrix.columns if re.fullmatch(r"P[DG]\d{2}", str(column))]
        evaluator_count = matrix["evaluator"].dropna().astype(str).str.strip().nunique() if "evaluator" in matrix.columns else 0
        result.add(problem_cols == expected_ids, f"matrice {slug}: 20 problemi finali", f"matrice {slug}: colonne problema errate ({len(problem_cols)}): {', '.join(problem_cols[:25])}")
        result.add(evaluator_count == 8, f"matrice {slug}: 8 valutatori", f"matrice {slug}: {evaluator_count}/8 valutatori")


def _validate_existing_outputs(result: FinalDataValidationResult) -> None:
    roots = [resolve_path("outputs/texts"), resolve_path("outputs/tables/markdown")]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".md", ".txt", ".csv"}:
                text = path.read_text(encoding="utf-8", errors="ignore")
                bad = [pattern for pattern in BANNED_OUTPUT_PATTERNS if _contains_banned(text, pattern)]
                if bad:
                    result.errors.append(f"ERROR: pattern vietati in {path}: {', '.join(bad)}")


def _validate_existing_decks(result: FinalDataValidationResult) -> None:
    pptx = resolve_path("outputs/slides/final_report.pptx")
    if not pptx.exists():
        result.warnings.append("WARNING: final_report.pptx non ancora generato; audit deck saltato")
        return
    findings = audit_final_deck_text(pptx)
    result.add(not findings, "final_report.pptx senza placeholder o path tecnici", f"final_report.pptx contiene {len(findings)} testi vietati")


def _contains_banned(text: str, pattern: str) -> bool:
    if pattern in {"TODO", "FIXME", "NaN", "None", "null", "undefined"}:
        return re.search(rf"(?<![A-Za-z0-9_]){re.escape(pattern)}(?![A-Za-z0-9_])", text, flags=re.IGNORECASE) is not None
    return pattern.casefold() in text.casefold()
