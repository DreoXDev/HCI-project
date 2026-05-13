from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd


TASK_RE = re.compile(r"^\d+\.\d{1,2}-[CAF]$")
HEURISTIC_RE = re.compile(r"^E([1-9]|10)(-E([1-9]|10))*$")


@dataclass
class ValidationMessage:
    level: str
    message: str


def _empty_cells(df: pd.DataFrame) -> list[ValidationMessage]:
    messages: list[ValidationMessage] = []
    for column, count in df.isna().sum().items():
        if count:
            messages.append(ValidationMessage("WARNING", f"{count} celle vuote nella colonna {column}"))
    return messages


def validate_users_time_csv(df: pd.DataFrame, config: dict) -> list[ValidationMessage]:
    messages = _empty_cells(df)
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    task_columns = [column for column in df.columns if str(column).startswith("Task ")]
    expected = [f"Task {task} {system}" for system in systems for task in range(1, 4)]
    missing = [column for column in expected if column not in df.columns]
    if missing:
        messages.append(ValidationMessage("ERROR", f"Colonne task mancanti: {', '.join(missing)}"))
    for column in task_columns:
        invalid = df[column].dropna().astype(str).loc[lambda s: ~s.str.match(TASK_RE)]
        if not invalid.empty:
            messages.append(ValidationMessage("ERROR", f"Formato tempo/esito non valido in {column}: {invalid.iloc[0]}"))
    if not messages:
        messages.append(ValidationMessage("OK", "users_time.csv valido"))
    return messages


def validate_heuristics_csv(df: pd.DataFrame) -> list[ValidationMessage]:
    messages = _empty_cells(df)
    required = ["Problema", "Euristiche", "Id valutatori"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        messages.append(ValidationMessage("ERROR", f"Colonne euristiche mancanti: {', '.join(missing)}"))
    expert_columns = [column for column in df.columns if str(column).startswith("Expert")]
    for column in expert_columns:
        values = pd.to_numeric(df[column], errors="coerce")
        if values.isna().any() or ~values.between(0, 4).all():
            messages.append(ValidationMessage("ERROR", f"Valori severità fuori range 0-4 in {column}"))
    if "Euristiche" in df:
        invalid = df["Euristiche"].dropna().astype(str).loc[lambda s: ~s.str.match(HEURISTIC_RE)]
        if not invalid.empty:
            messages.append(ValidationMessage("ERROR", f"Euristiche scritte male: {invalid.iloc[0]}"))
    if not messages:
        messages.append(ValidationMessage("OK", "file euristiche valido"))
    return messages


def validate_questionnaire_csv(df: pd.DataFrame, config: dict) -> list[ValidationMessage]:
    messages = _empty_cells(df)
    ueq_min = config["analysis"]["ueq_scale_min"]
    ueq_max = config["analysis"]["ueq_scale_max"]
    nps_min = config["analysis"]["nps_min"]
    nps_max = config["analysis"]["nps_max"]
    configured = config.get("questionnaire", {}).get("demographic_rows", [])
    demographic = {
        "genere",
        "eta",
        "situazione lavorativa",
        "istruzione",
        "familiarita delivery",
        "familiarita con app di delivery",
        "familiarita",
        *[str(row).strip().lower() for row in configured],
    }
    numeric_rows = []
    if "NPS" not in df.index:
        messages.append(ValidationMessage("WARNING", "Riga NPS mancante: analisi NPS saltata"))
    for idx in df.index:
        if str(idx).strip().lower() in demographic:
            continue
        if str(idx).upper() == "NPS":
            numeric_rows.append(idx)
            continue
        values = pd.to_numeric(df.loc[idx], errors="coerce")
        if values.isna().any():
            messages.append(ValidationMessage("WARNING", f"Riga non numerica trattata come demografica: {idx}"))
            continue
        numeric_rows.append(idx)
    for idx in numeric_rows:
        values = pd.to_numeric(df.loc[idx], errors="coerce")
        if values.isna().any():
            messages.append(ValidationMessage("ERROR", f"Valori non numerici nella riga {idx}"))
            continue
        low, high = (nps_min, nps_max) if str(idx).upper() == "NPS" else (ueq_min, ueq_max)
        if not values.between(low, high).all():
            messages.append(ValidationMessage("ERROR", f"Valore fuori range {low}-{high} nella riga {idx}"))
    if not messages:
        messages.append(ValidationMessage("OK", "questionario valido"))
    return messages


def format_validation(messages: list[ValidationMessage]) -> str:
    return "\n".join(f"{msg.level}: {msg.message}" for msg in messages)
