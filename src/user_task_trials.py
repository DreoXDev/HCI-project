from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .config import resolve_path
from .user_tests import parse_task_value
from .users_time import load_users_time_long, users_time_file, validate_users_time_file


TRIAL_COLUMNS = [
    "participant_id",
    "app",
    "task_id",
    "task_label",
    "time_seconds",
    "outcome",
    "completed",
    "correct",
    "assisted",
    "error_count",
    "critical_error_count",
    "help_count",
    "notes",
]

OUTCOMES = {"success", "assisted_success", "partial_success", "failure", "timeout", "invalid"}


@dataclass
class TrialAuditResult:
    ok: bool
    report_path: Path
    template_path: Path | None
    normalized_path: Path | None
    messages: list[str]


def audit_and_normalize_user_task_trials(config: dict, *, fail_on_missing: bool = False) -> TrialAuditResult:
    paths = _candidate_sources(config)
    report_path = resolve_path("outputs/audit/data_availability_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    messages: list[str] = []
    normalized = pd.DataFrame(columns=TRIAL_COLUMNS)
    source_used: Path | None = None
    for source in paths:
        if not source.exists() or not source.is_file():
            continue
        source_used = source
        normalized = normalize_user_task_trials(source, config)
        break

    template_path: Path | None = None
    if normalized.empty:
        messages.append("ERROR: nessun sorgente user test con trial, tempi e outcome trovato.")
        template_path = write_user_task_trials_template(config)
    else:
        messages.extend(_validate_trials(normalized, config))
        if any(message.startswith("ERROR") for message in messages) and source_used and source_used.name == "user_task_trials_template.csv":
            template_path = source_used

    ok = not any(message.startswith("ERROR") for message in messages)
    normalized_path: Path | None = None
    if not normalized.empty and ok:
        normalized_path = _export_trials(normalized)
    elif not ok:
        stale = resolve_path("data/processed/user_task_trials_normalized.csv")
        stale.unlink(missing_ok=True)
        stale_table = resolve_path("outputs/tables/user_task_trials_full.csv")
        stale_table.unlink(missing_ok=True)
        stale_xlsx = resolve_path("outputs/tables/user_task_trials_full.xlsx")
        stale_xlsx.unlink(missing_ok=True)

    _write_audit_report(report_path, config, paths, source_used, normalized, messages, template_path, normalized_path)
    if fail_on_missing and not ok:
        raise RuntimeError(
            "Dati user test insufficienti per il final report. "
            f"Vedi {report_path} e compila {template_path or 'il template trial-level'}."
        )
    return TrialAuditResult(ok, report_path, template_path, normalized_path, messages)


def normalize_user_task_trials(source: str | Path, config: dict) -> pd.DataFrame:
    path = resolve_path(source)
    df = load_users_time_long(path)
    real_columns = {"user_id", "collector", "app", "task", "time_raw", "time_seconds", "outcome", "assistance", "error_flag", "issue_note"}
    if real_columns.issubset(df.columns):
        return _normalize_real_user_testing_times(df, config)
    if set(TRIAL_COLUMNS).issubset(df.columns):
        return df[TRIAL_COLUMNS].copy()
    long_required = {"user_id", "app", "task_id", "completion_time_sec", "success"}
    if long_required.issubset(df.columns):
        return _normalize_long_trials(df, config)
    return _normalize_legacy_wide_trials(df, config)


def write_user_task_trials_template(config: dict) -> Path:
    target = resolve_path("data/processed/user_task_trials_template.csv")
    target.parent.mkdir(parents=True, exist_ok=True)
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    tasks = _report_tasks(config)
    rows = []
    for participant_idx in range(1, 25):
        for app in systems:
            for task in tasks:
                rows.append(
                    {
                        "participant_id": f"U{participant_idx:02d}",
                        "app": app,
                        "task_id": task["id"],
                        "task_label": task["name"],
                        "time_seconds": "",
                        "outcome": "",
                        "completed": "",
                        "correct": "",
                        "assisted": "",
                        "error_count": "",
                        "critical_error_count": "",
                        "help_count": "",
                        "notes": "",
                    }
                )
    pd.DataFrame(rows, columns=TRIAL_COLUMNS).to_csv(target, index=False, encoding="utf-8-sig")
    return target


def _candidate_sources(config: dict) -> list[Path]:
    candidates = [
        resolve_path("data/user_testing_times.csv"),
        users_time_file(config),
        resolve_path("data/formbricks_raw/user_tests/user_tests.csv"),
        resolve_path("data/processed/user_task_trials_template.csv"),
        resolve_path("data/processed/user_task_trials_normalized.csv"),
    ]
    unique: list[Path] = []
    for path in candidates:
        if path not in unique:
            unique.append(path)
    return unique


def _normalize_real_user_testing_times(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    task_names = {str(index + 1): task["name"] for index, task in enumerate(_report_tasks(config))}
    rows = []
    for row in df.itertuples(index=False):
        task_number = int(getattr(row, "task"))
        outcome_raw = str(getattr(row, "outcome", "")).strip()
        assistance = str(getattr(row, "assistance", "")).strip()
        error_flag = _boolish(getattr(row, "error_flag", False))
        normalized_outcome = _normalize_outcome(outcome_raw)
        rows.append(
            {
                "participant_id": getattr(row, "user_id", ""),
                "app": getattr(row, "app", ""),
                "task_id": f"T{task_number:02d}",
                "task_label": task_names.get(str(task_number), f"Task {task_number}"),
                "time_seconds": pd.to_numeric(getattr(row, "time_seconds", pd.NA), errors="coerce"),
                "outcome": normalized_outcome,
                "completed": normalized_outcome in {"success", "assisted_success", "partial_success"},
                "correct": normalized_outcome in {"success", "assisted_success", "partial_success"},
                "assisted": assistance in {"verbal_help", "workaround"} or normalized_outcome == "assisted_success",
                "error_count": 1 if error_flag else 0,
                "critical_error_count": 0,
                "help_count": 1 if assistance == "verbal_help" or normalized_outcome == "assisted_success" else 0,
                "notes": getattr(row, "issue_note", ""),
            }
        )
    return pd.DataFrame(rows, columns=TRIAL_COLUMNS)


def _normalize_outcome(value: str) -> str:
    if value == "success_with_issue":
        return "partial_success"
    if value == "unknown":
        return "invalid"
    return value if value in OUTCOMES else "invalid"


def _boolish(value: Any) -> bool:
    return str(value).strip().casefold() in {"true", "1", "yes", "si", "sì"}


def _normalize_long_trials(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    validation = validate_users_time_file(users_time_file(config), required_columns=config.get("users_time", {}).get("required_columns"), tasks=config.get("users_time", {}).get("tasks", []))
    source = validation.normalized if validation.is_valid and not validation.normalized.empty else df.copy()
    rows = []
    for row in source.itertuples(index=False):
        success = bool(getattr(row, "success", False))
        help_count = int(pd.to_numeric(getattr(row, "help_requests", 0), errors="coerce") or 0)
        error_count = int(pd.to_numeric(getattr(row, "errors_count", 0), errors="coerce") or 0)
        outcome = "assisted_success" if success and help_count else "success" if success else "failure"
        rows.append(
            {
                "participant_id": getattr(row, "user_id", ""),
                "app": getattr(row, "app", ""),
                "task_id": getattr(row, "task_id", ""),
                "task_label": getattr(row, "task_name", getattr(row, "task_id", "")),
                "time_seconds": getattr(row, "completion_time_sec", ""),
                "outcome": outcome,
                "completed": success,
                "correct": success,
                "assisted": help_count > 0,
                "error_count": error_count,
                "critical_error_count": int(pd.to_numeric(getattr(row, "critical_error_count", 0), errors="coerce") or 0),
                "help_count": help_count,
                "notes": getattr(row, "notes", ""),
            }
        )
    return pd.DataFrame(rows, columns=TRIAL_COLUMNS)


def _normalize_legacy_wide_trials(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    tasks = _report_tasks(config)
    rows = []
    if df.empty or "User" not in df.columns:
        return pd.DataFrame(columns=TRIAL_COLUMNS)
    for _, row in df.iterrows():
        participant_id = row.get("User", "")
        for task_index, task in enumerate(tasks, start=1):
            for app in systems:
                column = f"Task {task_index} {app}"
                if column not in df.columns:
                    continue
                raw_value = row.get(column, "")
                try:
                    seconds, status = parse_task_value(str(raw_value))
                except ValueError:
                    seconds, status = pd.NA, "I"
                outcome = {"C": "success", "A": "assisted_success", "F": "failure"}.get(status, "invalid")
                rows.append(
                    {
                        "participant_id": participant_id,
                        "app": app,
                        "task_id": task["id"],
                        "task_label": task["name"],
                        "time_seconds": seconds,
                        "outcome": outcome,
                        "completed": outcome in {"success", "assisted_success", "partial_success"},
                        "correct": outcome in {"success", "assisted_success"},
                        "assisted": outcome in {"assisted_success", "partial_success"},
                        "error_count": 0 if outcome in {"success", "assisted_success"} else 1,
                        "critical_error_count": 1 if outcome == "failure" else 0,
                        "help_count": 1 if outcome == "assisted_success" else 0,
                        "notes": "",
                    }
                )
    return pd.DataFrame(rows, columns=TRIAL_COLUMNS)


def _validate_trials(df: pd.DataFrame, config: dict) -> list[str]:
    messages: list[str] = []
    missing = [column for column in TRIAL_COLUMNS if column not in df.columns]
    if missing:
        messages.append(f"ERROR: colonne trial mancanti: {', '.join(missing)}")
        return messages
    valid = df[~df["outcome"].isin(["invalid", ""])]
    systems = set(df["app"].dropna().astype(str))
    tasks = set(df["task_id"].dropna().astype(str))
    participants = set(df["participant_id"].dropna().astype(str))
    expected = 24 * 2 * len(_report_tasks(config))
    if len(df) < expected:
        messages.append(f"ERROR: trial user test insufficienti: {len(df)}/{expected}.")
    if len(participants) < 24:
        messages.append(f"ERROR: partecipanti insufficienti: {len(participants)}/24.")
    if not {"Deliveroo", "Glovo"}.issubset(systems):
        messages.append("ERROR: app user test non complete: servono Deliveroo e Glovo.")
    if len(tasks) < len(_report_tasks(config)):
        messages.append(f"ERROR: task coperti insufficienti: {len(tasks)}/{len(_report_tasks(config))}.")
    if valid.empty:
        messages.append("ERROR: nessun trial valido con outcome utilizzabile.")
    for column in ["time_seconds", "error_count", "critical_error_count", "help_count"]:
        numeric = pd.to_numeric(df[column], errors="coerce")
        if numeric.isna().all():
            messages.append(f"ERROR: `{column}` non contiene valori numerici.")
    if not messages:
        messages.append("OK: trial user test completi e normalizzati.")
    return messages


def _export_trials(df: pd.DataFrame) -> Path:
    processed = resolve_path("data/processed/user_task_trials_normalized.csv")
    tables = resolve_path("outputs/tables/user_task_trials_full.csv")
    xlsx = resolve_path("outputs/tables/user_task_trials_full.xlsx")
    for path in [processed, tables, xlsx]:
        path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(processed, index=False, encoding="utf-8-sig")
    df.to_csv(tables, index=False, encoding="utf-8-sig")
    df.to_excel(xlsx, index=False)
    return processed


def _write_audit_report(
    path: Path,
    config: dict,
    candidates: list[Path],
    source_used: Path | None,
    normalized: pd.DataFrame,
    messages: list[str],
    template_path: Path | None,
    normalized_path: Path | None,
) -> None:
    lines = ["# Data availability report", ""]
    lines.append("## Sorgenti user test")
    for candidate in candidates:
        exists = candidate.exists()
        lines.append(f"- `{candidate}`: {'trovato' if exists else 'mancante'}")
        if exists:
            try:
                df = pd.read_csv(candidate, sep=None, engine="python", encoding="utf-8-sig")
                lines.append(f"  - righe: {len(df)}")
                lines.append(f"  - colonne: {', '.join(map(str, df.columns))}")
            except Exception as exc:
                lines.append(f"  - lettura fallita: {exc}")
    lines.extend(["", "## Normalizzazione", f"- Sorgente usato: `{source_used}`" if source_used else "- Sorgente usato: nessuno"])
    if not normalized.empty:
        lines.append(f"- Trial normalizzati: {len(normalized)}")
        lines.append(f"- App coperte: {', '.join(sorted(normalized['app'].dropna().astype(str).unique()))}")
        lines.append(f"- Task coperti: {', '.join(sorted(normalized['task_id'].dropna().astype(str).unique()))}")
        lines.append(f"- File normalizzato: `{normalized_path}`")
    if template_path:
        lines.append(f"- Template da compilare: `{template_path}`")
    lines.extend(["", "## Esito", *[f"- {message}" for message in messages], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _report_tasks(config: dict) -> list[dict[str, str]]:
    tasks = config.get("users_time", {}).get("tasks", [])[:3]
    return [{"id": str(task.get("id", f"T{idx:02d}")), "name": str(task.get("name", f"Task {idx}"))} for idx, task in enumerate(tasks, start=1)]
