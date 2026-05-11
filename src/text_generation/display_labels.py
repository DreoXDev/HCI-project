from __future__ import annotations

from typing import Any

import pandas as pd

from .italian import italian_display_text


COLUMN_LABELS = {
    "expert_id": "Valutatore",
    "evaluator_id": "Valutatore",
    "evaluator": "Valutatore",
    "expert_role": "Ruolo",
    "expert_group": "Gruppo",
    "system": "App",
    "app": "App",
    "problem_id": "ID problema",
    "final_problem_id": "ID problema",
    "problem_group_id": "ID problema",
    "raw_problem_id": "ID grezzo",
    "problem_title": "Problema",
    "short_description": "Problema",
    "problem_description": "Descrizione",
    "long_description": "Descrizione",
    "heuristic": "Euristica",
    "heuristics": "Euristiche",
    "category": "Categoria",
    "severity": "Severità",
    "severity_score": "Severità media",
    "severity_mean": "Severità media",
    "severity_median": "Severità mediana",
    "impact": "Impatto",
    "frequency": "Frequenza",
    "persistence": "Persistenza",
    "detection_count": "Segnalazioni",
    "n_ratings": "Valutazioni",
    "priority": "Priorità",
    "priority_band": "Priorità",
    "priority_mean": "Priorità media",
    "problems": "Problemi",
    "evaluated_apps": "App valutata",
    "reported_problems": "Problemi segnalati",
    "recommendation": "Raccomandazione",
    "task_id": "Task",
    "task_name": "Task",
    "success_rate": "Tasso di successo",
    "avg_time": "Tempo medio",
    "mean_time": "Tempo medio",
    "mean_time_sec": "Tempo medio (s)",
    "median_time": "Tempo mediano",
    "error_count": "Errori",
    "errors_count": "Errori",
    "help_count": "Aiuti",
    "help_requests": "Aiuti",
    "sample_size": "Campione",
    "count": "Conteggio",
}

VALUE_LABELS = {
    "deliveroo": "Deliveroo",
    "glovo": "Glovo",
    "ed": "ED",
    "eu": "EU",
    "expert": "Esperto",
    "novice": "Utente",
    "high": "Alta",
    "medium": "Media",
    "low": "Bassa",
    "true": "Sì",
    "false": "No",
}


def prettify_identifier(value: str) -> str:
    text = italian_display_text(value).strip()
    if not text:
        return ""
    text = text.replace("_", " ").replace("-", " ")
    return text[:1].upper() + text[1:]


def display_column_name(column: str) -> str:
    key = str(column).strip()
    return COLUMN_LABELS.get(key, prettify_identifier(key))


def display_cell_value(value: Any, column: str | None = None) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    text = italian_display_text(value).strip()
    mapped = VALUE_LABELS.get(text.lower())
    if mapped:
        return mapped
    return text


def prepare_display_table(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()
    for column in display.columns:
        display[column] = display[column].map(lambda value, col=column: display_cell_value(value, str(col)))
    display = display.rename(columns={column: display_column_name(str(column)) for column in display.columns})
    return display
