from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .adapters.formbricks.questionnaire_adapter import convert_questionnaire_export
from .config import resolve_path
from .formbricks_heuristics_pipeline import import_severity_formbricks, validate_clean_problems
from .users_time import validate_users_time_file


EXPECTED_EXPERTS = 8
EXPECTED_USERS_FINAL = 24


CANONICAL_INPUTS = {
    "clean_problems": Path("data/processed/heuristics/clean_problems.csv"),
    "severity_export": Path("data/formbricks_raw/heuristics/severity_ratings_export.csv"),
    "problem_ratings_long": Path("data/processed/heuristics/problem_ratings_long.csv"),
    "users_time": Path("data/raw/users_time.csv"),
    "user_testing_observations": Path("data/raw/user_testing_observations.csv"),
    "questionnaire_export": Path("data/formbricks_raw/questionnaire/users_questionnaire_export.csv"),
}


@dataclass
class PreparedInput:
    key: str
    source: Path
    target: Path


@dataclass
class RealInputStatus:
    prepared: list[PreparedInput] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    experts_present: int = 0
    users_time_present: int = 0
    questionnaire_responses_present: int = 0

    @property
    def data_status(self) -> str:
        if self.users_time_present >= EXPECTED_USERS_FINAL and self.questionnaire_responses_present >= EXPECTED_USERS_FINAL:
            return "FINAL_DATA"
        return "PARTIAL_DATA"


def prepare_real_inputs(source_dir: str | Path, config: dict, *, overwrite: bool = False) -> RealInputStatus:
    source_root = resolve_path(source_dir)
    status = RealInputStatus()
    if not source_root.exists():
        status.errors.append(f"Cartella sorgente non trovata: {source_root}")
        write_real_input_status(status)
        return status

    matches = _discover_inputs(source_root)
    for key, target_rel in CANONICAL_INPUTS.items():
        source = matches.get(key)
        if not source:
            if key not in {"problem_ratings_long"}:
                status.warnings.append(f"Input non trovato per {key}")
            continue
        target = resolve_path(target_rel)
        if target.exists() and not overwrite:
            status.warnings.append(f"File gia presente, non sovrascritto: {target}")
            continue
        _read_csv_or_error(source, status)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        status.prepared.append(PreparedInput(key, source, target))

    _validate_prepared_inputs(config, status)
    write_real_input_status(status)
    return status


def _discover_inputs(source_root: Path) -> dict[str, Path]:
    files = [path for path in source_root.rglob("*.csv") if path.is_file()]
    by_name = {path.name.lower(): path for path in files}
    return {
        "clean_problems": _first(by_name, "clean_problems.csv"),
        "severity_export": _first(by_name, "severity_ratings_export_remapped_p001_p040.csv", "severity_ratings_export.csv"),
        "problem_ratings_long": _first(by_name, "problem_ratings_long_clean.csv", "problem_ratings_long.csv"),
        "users_time": _first(by_name, "users_time_clean.csv", "users_time.csv"),
        "user_testing_observations": _first(by_name, "user_testing_observations_clean.csv", "user_testing_observations.csv"),
        "questionnaire_export": _first(by_name, "questionnaire_formbricks_raw_current_18_responses.csv", "users_questionnaire_export.csv"),
    }


def _first(files: dict[str, Path], *names: str) -> Path | None:
    for name in names:
        found = files.get(name.lower())
        if found:
            return found
    return None


def _read_csv_or_error(path: Path, status: RealInputStatus) -> None:
    try:
        pd.read_csv(path, nrows=2, encoding="utf-8-sig")
    except UnicodeDecodeError:
        status.errors.append(f"Encoding non UTF-8 leggibile: {path}")
    except Exception as exc:
        status.errors.append(f"CSV non leggibile {path}: {exc}")


def _validate_prepared_inputs(config: dict, status: RealInputStatus) -> None:
    clean_path = resolve_path(CANONICAL_INPUTS["clean_problems"])
    severity_path = resolve_path(CANONICAL_INPUTS["severity_export"])
    users_time_path = resolve_path(CANONICAL_INPUTS["users_time"])
    questionnaire_path = resolve_path(CANONICAL_INPUTS["questionnaire_export"])

    if clean_path.exists():
        result = validate_clean_problems(clean_path)
        status.warnings.extend(result.warnings)
        status.errors.extend(result.errors)
    if severity_path.exists():
        try:
            ratings, warnings = import_severity_formbricks(severity_path, problems_path=clean_path if clean_path.exists() else None, strict=False)
            status.experts_present = ratings["expert_id"].nunique() if not ratings.empty else 0
            status.warnings.extend(w for w in warnings if not w.startswith("File generato"))
        except Exception as exc:
            status.errors.append(f"Import severita Formbricks non riuscito: {exc}")
    if users_time_path.exists():
        validation = validate_users_time_file(
            users_time_path,
            required_columns=config.get("users_time", {}).get("required_columns"),
            expected_users=EXPECTED_USERS_FINAL,
            tasks=config.get("users_time", {}).get("tasks", []),
        )
        status.users_time_present = validation.normalized["user_id"].nunique() if not validation.normalized.empty and "user_id" in validation.normalized else 0
        status.warnings.extend(message for message in validation.messages if message.startswith("WARNING"))
        status.errors.extend(message for message in validation.messages if message.startswith("ERROR"))
    if questionnaire_path.exists():
        try:
            raw = pd.read_csv(questionnaire_path, encoding="utf-8-sig")
            status.questionnaire_responses_present = len(raw)
            convert_questionnaire_export(questionnaire_path, config)
        except Exception as exc:
            status.errors.append(f"Import questionario Formbricks non riuscito: {exc}")

    if status.experts_present and status.experts_present < EXPECTED_EXPERTS:
        status.warnings.append(f"Esperti severita presenti: {status.experts_present}/{EXPECTED_EXPERTS}")
    if status.questionnaire_responses_present and status.questionnaire_responses_present < EXPECTED_USERS_FINAL:
        status.warnings.append(f"Questionari utenti presenti: {status.questionnaire_responses_present}/{EXPECTED_USERS_FINAL}")


def write_real_input_status(status: RealInputStatus, output_path: str | Path = "outputs/reports/real_input_status.md") -> Path:
    lines = [
        "# Real Input Status",
        "",
        f"- DATA_STATUS: {status.data_status}",
        f"- Esperti severita: {status.experts_present}/{EXPECTED_EXPERTS}",
        f"- Utenti users_time: {status.users_time_present}/{EXPECTED_USERS_FINAL}",
        f"- Risposte questionario utenti: {status.questionnaire_responses_present}/{EXPECTED_USERS_FINAL}",
        "",
        "## File preparati",
        "",
    ]
    if status.prepared:
        lines.extend(f"- `{item.source}` -> `{item.target}`" for item in status.prepared)
    else:
        lines.append("- Nessun file copiato.")
    lines.extend(["", "## Warning", ""])
    lines.extend(f"- {warning}" for warning in status.warnings) if status.warnings else lines.append("- Nessun warning.")
    lines.extend(["", "## Errori", ""])
    lines.extend(f"- {error}" for error in status.errors) if status.errors else lines.append("- Nessun errore.")
    target = resolve_path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target
