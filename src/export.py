from __future__ import annotations

from pathlib import Path

from .config import resolve_path


USERS_TEMPLATE = "User;Task 1 Deliveroo;Task 2 Deliveroo;Task 3 Deliveroo;Task 1 Glovo;Task 2 Glovo;Task 3 Glovo;Sesso;Eta;Lavoro;Istruzione\nU1;0.00-C;0.00-A;0.00-F;0.00-C;0.00-A;0.00-F;F;22;Studente;Diploma\n"
HEURISTICS_TEMPLATE = ",Problema,Expert 1,Expert 2,Expert 3,Euristiche,Id valutatori\nPB1,Descrizione problema,2,3,1,E1-E5,EU1-ED1\n"
QUESTIONNAIRE_TEMPLATE = ",Utente 1,Utente 2\ngenere,Femmina,Maschio\neta,22,23\nsituazione lavorativa,Studente,Studente\nistruzione,Diploma,Laurea\nfastidioso-piacevole,4,5\nNPS,8,9\n"


def create_templates(directory: str | Path = "data/templates") -> None:
    target = resolve_path(directory)
    target.mkdir(parents=True, exist_ok=True)
    (target / "users-time-template.csv").write_text(USERS_TEMPLATE, encoding="utf-8")
    (target / "heuristics-template.csv").write_text(HEURISTICS_TEMPLATE, encoding="utf-8")
    (target / "questionnaire-template.csv").write_text(QUESTIONNAIRE_TEMPLATE, encoding="utf-8")
