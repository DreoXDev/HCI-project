from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from .config import resolve_path
from .data_loading import load_all
from .questionnaire import numeric_items
from .users_time import users_time_file, validate_users_time_file


DOC_WORD_RE = re.compile(r"\b(criticita|severita|priorita|qualita|accessibilita|usabilita|piu|perche|puo|cosi)\b", re.IGNORECASE)
LOCAL_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")


def _check(condition: bool, ok: str, fail: str, rows: list[dict]) -> None:
    rows.append({"status": "OK" if condition else "FAIL", "check": ok if condition else fail})


def run_quality_check(config: dict, output_path: str | Path = "outputs/reports/final_quality_check.md") -> bool:
    rows: list[dict] = []
    try:
        data = load_all(config)
    except Exception as exc:
        data = {}
        rows.append({"status": "FAIL", "check": f"Caricamento dati legacy non riuscito: {exc}"})

    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    for key, system in [("questionnaire_system_1", systems[0]), ("questionnaire_system_2", systems[1])]:
        df = data.get(key, pd.DataFrame())
        _check(not df.empty and df.shape[1] >= 12, f"Questionario {system}: almeno 12 rispondenti", f"Questionario {system}: meno di 12 rispondenti o file mancante", rows)
        _check("NPS" in df.index, f"NPS presente per {system}", f"NPS mancante per {system}", rows)
        if not df.empty:
            items = numeric_items(df, config)
            valid_items = items.apply(pd.to_numeric, errors="coerce").stack().between(1, 7).all() if not items.empty else False
            _check(bool(valid_items), f"Item UEQ nel range 1-7 per {system}", f"Item UEQ fuori range o assenti per {system}", rows)
            if "NPS" in df.index:
                nps = pd.to_numeric(df.loc["NPS"], errors="coerce").dropna()
                _check(bool(nps.between(0, 10).all()), f"NPS nel range 0-10 per {system}", f"NPS fuori range per {system}", rows)

    users_validation = validate_users_time_file(users_time_file(config), required_columns=config.get("users_time", {}).get("required_columns"))
    _check(users_validation.is_valid, "users_time.csv osservazionale valido", "users_time.csv osservazionale mancante o non valido", rows)
    if users_validation.is_valid:
        observed = users_validation.normalized
        _check(observed["task_id"].nunique() >= 3, "Almeno 3 task user test presenti", "Meno di 3 task user test presenti", rows)
        missing_tasks = [task.get("id") for task in config.get("users_time", {}).get("tasks", []) if not task.get("oet_seconds")]
        _check(not missing_tasks, "OET configurato per tutti i task in config.yaml", f"OET mancante per task: {', '.join(map(str, missing_tasks))}", rows)
        empty_tasks = observed.groupby("task_id").size()
        _check(bool((empty_tasks > 0).all()), "Nessun task senza dati", "Almeno un task e senza dati", rows)

    for key, system in [("heuristics_system_1", systems[0]), ("heuristics_system_2", systems[1])]:
        df = data.get(key, pd.DataFrame())
        expert_cols = [c for c in df.columns if str(c).startswith("Expert")]
        _check(len(expert_cols) >= 5, f"Almeno 5 valutatori euristici per {system}", f"Meno di 5 valutatori euristici per {system}", rows)
        if expert_cols:
            sev = df[expert_cols].apply(pd.to_numeric, errors="coerce").stack()
            _check(bool(sev.between(0, 4).all()), f"Severità euristiche 0-4 per {system}", f"Severità euristiche fuori range per {system}", rows)

    required_outputs = [
        "outputs/tables/user_test_effectiveness.csv",
        "outputs/tables/heuristics_summary.csv",
        "outputs/tables/ueq_summary.csv",
        "outputs/slide_assets/pack/00_index.md",
        "outputs/slide_assets/pack/assets_manifest.csv",
    ]
    for output in required_outputs:
        _check(resolve_path(output).exists(), f"Output principale presente: {output}", f"Output principale mancante: {output}", rows)

    for doc in sorted(resolve_path("docs").glob("*.md")) + [resolve_path("README.md")]:
        try:
            text = doc.read_text(encoding="utf-8")
            _check(True, f"UTF-8 valido: {doc.relative_to(resolve_path('.'))}", "", rows)
        except UnicodeDecodeError:
            _check(False, "", f"Encoding non UTF-8: {doc}", rows)
            continue
        bad_words = [match.group(0) for match in DOC_WORD_RE.finditer(text)]
        _check(not bad_words, f"Accenti OK: {doc.name}", f"Possibili accenti mancanti in {doc.name}: {', '.join(sorted(set(bad_words)))}", rows)
        for link in LOCAL_LINK_RE.findall(text):
            if "://" in link or link.startswith("#"):
                continue
            target = (doc.parent / link).resolve()
            _check(target.exists(), f"Link locale valido in {doc.name}: {link}", f"Link locale rotto in {doc.name}: {link}", rows)

    status = "READY_FOR_SLIDES" if all(row["status"] == "OK" for row in rows) else "NEEDS_FIXES"
    lines = ["# Final Quality Check", "", "| status | check |", "|---|---|"]
    lines.extend(f"| {row['status']} | {row['check']} |" for row in rows)
    lines.extend(["", f"STATUS: {status}", ""])
    target = resolve_path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    return status == "READY_FOR_SLIDES"

