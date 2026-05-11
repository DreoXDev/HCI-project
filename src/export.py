from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import resolve_path
from .users_time import TEMPLATE_COLUMNS


USERS_TEMPLATE = "User;Task 1 Deliveroo;Task 2 Deliveroo;Task 3 Deliveroo;Task 1 Glovo;Task 2 Glovo;Task 3 Glovo;Sesso;Eta;Lavoro;Istruzione\nU1;0.00-C;0.00-A;0.00-F;0.00-C;0.00-A;0.00-F;F;22;Studente;Diploma\n"
HEURISTICS_TEMPLATE = ",Problema,Expert 1,Expert 2,Expert 3,Euristiche,Id valutatori\nPB1,Descrizione problema,2,3,1,E1-E5,EU1-ED1\n"
QUESTIONNAIRE_TEMPLATE = ",Utente 1,Utente 2\ngenere,Femmina,Maschio\neta,22,23\nsituazione lavorativa,Studente,Studente\nistruzione,Diploma,Laurea\nfastidioso-piacevole,4,5\nNPS,8,9\n"
USERS_TIME_EXAMPLE = [
    {
        "user_id": "U01",
        "app": "Deliveroo",
        "task_id": "T01",
        "task_name": "Ricerca ristorante",
        "completion_time_sec": 34,
        "success": True,
        "errors_count": 0,
        "help_requests": 0,
        "notes": "Ricerca completata senza difficolta",
        "start_time": "14:00:00",
        "end_time": "14:00:34",
        "device": "Android",
        "observer_id": "OBS1",
        "order": 1,
    },
    {
        "user_id": "U01",
        "app": "Glovo",
        "task_id": "T01",
        "task_name": "Ricerca ristorante",
        "completion_time_sec": 47,
        "success": True,
        "errors_count": 1,
        "help_requests": 0,
        "notes": "L'utente ha esitato nella scelta della categoria",
        "start_time": "14:05:00",
        "end_time": "14:05:47",
        "device": "Android",
        "observer_id": "OBS1",
        "order": 2,
    },
    {
        "user_id": "U02",
        "app": "Deliveroo",
        "task_id": "T02",
        "task_name": "Aggiunta prodotto al carrello",
        "completion_time_sec": 29,
        "success": True,
        "errors_count": 0,
        "help_requests": 0,
        "notes": "Nessun problema rilevante",
        "start_time": "14:12:00",
        "end_time": "14:12:29",
        "device": "iOS",
        "observer_id": "OBS1",
        "order": 1,
    },
    {
        "user_id": "U02",
        "app": "Glovo",
        "task_id": "T02",
        "task_name": "Aggiunta prodotto al carrello",
        "completion_time_sec": 41,
        "success": True,
        "errors_count": 1,
        "help_requests": 1,
        "notes": "L'utente ha chiesto conferma sul pulsante corretto",
        "start_time": "14:18:00",
        "end_time": "14:18:41",
        "device": "iOS",
        "observer_id": "OBS1",
        "order": 2,
    },
]


def _write_text_if_needed(path: Path, content: str, overwrite: bool) -> bool:
    if path.exists() and not overwrite:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def _write_dataframe_if_needed(path: Path, df: pd.DataFrame, overwrite: bool) -> bool:
    if path.exists() and not overwrite:
        return False
    if path.suffix == ".xlsx":
        df.to_excel(path, index=False)
    else:
        df.to_csv(path, index=False, encoding="utf-8-sig")
    return True


def create_templates(directory: str | Path = "data/templates", overwrite: bool = False) -> list[Path]:
    target = resolve_path(directory)
    target.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for path, content in [
        (target / "users-time-template.csv", USERS_TEMPLATE),
        (target / "heuristics-template.csv", HEURISTICS_TEMPLATE),
        (target / "questionnaire-template.csv", QUESTIONNAIRE_TEMPLATE),
    ]:
        if _write_text_if_needed(path, content, overwrite):
            created.append(path)

    examples = resolve_path("data/examples")
    examples.mkdir(parents=True, exist_ok=True)
    users_time_template = pd.DataFrame(columns=TEMPLATE_COLUMNS)
    users_time_example = pd.DataFrame(USERS_TIME_EXAMPLE, columns=TEMPLATE_COLUMNS)
    for path, df in [
        (examples / "users_time_template.csv", users_time_template),
        (examples / "users_time_template.xlsx", users_time_template),
        (examples / "users_time_example.csv", users_time_example),
        (examples / "users_time_example.xlsx", users_time_example),
    ]:
        if _write_dataframe_if_needed(path, df, overwrite):
            created.append(path)
    return created
