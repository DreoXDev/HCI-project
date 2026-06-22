from __future__ import annotations

from pathlib import Path
import re
import zipfile

import pandas as pd

from .config import resolve_path
from .data_loading import load_all
from .data_integrity_audit import run_data_integrity_audit
from .formbricks_heuristics_pipeline import import_severity_formbricks, validate_clean_problems
from .questionnaire import numeric_items
from .report_quality.final_deck_text_audit import audit_final_deck_text
from .users_time import users_time_file, validate_users_time_file


DOC_WORD_RE = re.compile(r"\b(criticita|severita|priorita|qualita|accessibilita|usabilita|piu|perche|puo|cosi)\b", re.IGNORECASE)
LOCAL_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")


def _check(condition: bool, ok: str, fail: str, rows: list[dict]) -> None:
    rows.append({"status": "OK" if condition else "FAIL", "check": ok if condition else fail})


def _warn(condition: bool, ok: str, warn: str, rows: list[dict]) -> None:
    rows.append({"status": "OK" if condition else "WARNING", "check": ok if condition else warn})


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

    clean_problems = resolve_path("data/processed/heuristics/clean_problems.csv")
    severity_export = resolve_path("data/formbricks_raw/heuristics/severity_ratings_export.csv")
    if clean_problems.exists():
        clean_result = validate_clean_problems(clean_problems)
        _check(clean_result.valid, "clean_problems.csv valido", "clean_problems.csv non valido", rows)
        clean_df = pd.read_csv(clean_problems)
        _check(len(clean_df) == 40, "40 problemi consolidati presenti", f"Problemi consolidati presenti: {len(clean_df)}/40", rows)
    else:
        _check(False, "", "clean_problems.csv mancante", rows)
    if severity_export.exists():
        try:
            ratings, warnings = import_severity_formbricks(severity_export, problems_path=clean_problems if clean_problems.exists() else None)
            experts = ratings["expert_id"].nunique() if not ratings.empty else 0
            _check(experts == 8, "8 esperti nella survey severita", f"Esperti nella survey severita: {experts}/8", rows)
            _check(not any("Option ID" in str(value) for value in ratings.astype(str).stack()), "Nessuna colonna Option ID negli output severita", "Option ID trovato negli output severita", rows)
            for warning in warnings:
                if not warning.startswith("File generato"):
                    rows.append({"status": "WARNING", "check": warning})
        except Exception as exc:
            _check(False, "", f"Import severita reale non riuscito: {exc}", rows)
    else:
        _check(False, "", "severity_ratings_export.csv mancante", rows)
    try:
        integrity = run_data_integrity_audit()
        _check(integrity.valid, "Audit integrita dati 40x8=320 superato", f"Audit integrita dati fallito: {'; '.join(integrity.failures)}", rows)
        _check(integrity.mapping_path.exists(), "Mapping canonico problem_id esportato", "Mapping canonico problem_id mancante", rows)
    except Exception as exc:
        _check(False, "", f"Audit integrita dati non eseguibile: {exc}", rows)

    users_validation = validate_users_time_file(
        users_time_file(config),
        required_columns=config.get("users_time", {}).get("required_columns"),
        tasks=config.get("users_time", {}).get("tasks", []),
    )
    _check(users_validation.is_valid, "users_time.csv osservazionale valido", "users_time.csv osservazionale mancante o non valido", rows)
    observed_user_count = 0
    if users_validation.is_valid:
        observed = users_validation.normalized
        observed_user_count = observed["user_id"].nunique() if "user_id" in observed else 0
        _warn(observed_user_count >= 24, "24 utenti presenti: dataset finale", f"Dataset utenti parziale: {observed_user_count}/24 utenti", rows)
        _check(observed["task_id"].nunique() >= 3, "Almeno 3 task user test presenti", "Meno di 3 task user test presenti", rows)
        missing_tasks = [task.get("id") for task in config.get("users_time", {}).get("tasks", []) if not task.get("oet_seconds")]
        _check(not missing_tasks, "OET configurato per tutti i task in config.yaml", f"OET mancante per task: {', '.join(map(str, missing_tasks))}", rows)
        empty_tasks = observed.groupby("task_id").size()
        _check(bool((empty_tasks > 0).all()), "Nessun task senza dati", "Almeno un task e senza dati", rows)

    wide_times = resolve_path("outputs/tables/user_testing_times_wide.csv")
    if wide_times.exists():
        wide_df = pd.read_csv(wide_times, encoding="utf-8-sig")
        user_col = "Utente" if "Utente" in wide_df.columns else "user_id"
        users = wide_df[user_col].astype(str).tolist() if user_col in wide_df else []
        expected_users = [f"U{index}" for index in range(1, 25)]
        _check(len(users) == 24, "Tabella tempi wide contiene 24 utenti", f"Tabella tempi wide contiene {len(users)}/24 utenti", rows)
        _check(sorted(users, key=lambda value: int(value[1:]) if value.startswith("U") and value[1:].isdigit() else 999) == expected_users, "Utenti U1-U24 presenti una sola volta nella tabella tempi", "Utenti mancanti o duplicati nella tabella tempi", rows)
    else:
        _check(False, "", "Tabella tempi wide mancante", rows)

    profile_table = resolve_path("outputs/tables/user_profiles_slide.csv")
    if profile_table.exists():
        profiles_slide = pd.read_csv(profile_table, encoding="utf-8-sig")
        user_col = "Utente" if "Utente" in profiles_slide.columns else "user_id"
        profile_users = profiles_slide[user_col].astype(str).tolist() if user_col in profiles_slide else []
        _check(len(profile_users) == 24, "Profilo utenti contiene 24 utenti", f"Profilo utenti contiene {len(profile_users)}/24 utenti", rows)
        _check("digital_familiarity" not in profiles_slide.columns and "Familiarita digitale" not in profiles_slide.columns, "Profilo utenti non inventa familiarita digitale", "Profilo utenti contiene familiarita digitale non disponibile", rows)
        familiarity_cols = [column for column in profiles_slide.columns if "Familiarita" in column or "Frequenza" in column]
        raw_ordinal = profiles_slide[familiarity_cols].astype(str).isin(["1", "2", "3", "1.0", "2.0", "3.0"]).any().any() if familiarity_cols else False
        _check(not raw_ordinal, "Profilo utenti usa label Bassa/Media/Alta", "Profilo utenti mostra ancora valori 1/2/3", rows)
    else:
        _check(False, "", "Tabella profilo utenti mancante", rows)

    effectiveness_path = resolve_path("outputs/tables/user_test_effectiveness_by_task.csv")
    non_autonomous_path = resolve_path("outputs/tables/user_test_non_autonomous_tasks.csv")
    if effectiveness_path.exists() and non_autonomous_path.exists():
        effectiveness = pd.read_csv(effectiveness_path, encoding="utf-8-sig")
        excluded = pd.read_csv(non_autonomous_path, encoding="utf-8-sig")
        bad_outcomes = {"assisted_success", "success_with_issue", "partial_success"}
        _check(bool(bad_outcomes.issubset(set(excluded.get("outcome", pd.Series(dtype=str)).astype(str))) or bad_outcomes.intersection(set(excluded.get("outcome", pd.Series(dtype=str)).astype(str)))), "Task assistite/parziali escluse dalle metriche autonome", "Nessuna evidenza di esclusione task assistite/parziali", rows)
        deliveroo_t3 = effectiveness[(effectiveness["app"] == "Deliveroo") & (effectiveness["task"].astype(int) == 3)]
        _check(not deliveroo_t3.empty and int(deliveroo_t3["autonomous_success_count"].iloc[0]) == 16, "Deliveroo Task 3 conta solo successi autonomi", "Deliveroo Task 3 include successi assistiti nei successi", rows)
    else:
        _check(False, "", "Output efficacia autonoma/non autonoma mancanti", rows)

    for output in [
        "outputs/tables/user_test_effectiveness.csv",
        "outputs/tables/user_test_absolute_effectiveness.csv",
        "outputs/tables/user_test_effectiveness_mcnemar.csv",
        "outputs/tables/user_test_efficiency_by_task_autonomous.csv",
        "outputs/tables/user_test_efficiency_comparison_autonomous.csv",
        "outputs/reports/user_testing_autonomous_success_update.md",
    ]:
        _check(resolve_path(output).exists(), f"Output autonomo presente: {output}", f"Output autonomo mancante: {output}", rows)

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

    for app in ["deliveroo", "glovo"]:
        full_table = resolve_path(f"outputs/tables/final_problems_{app}.csv")
        slide_table = resolve_path(f"outputs/tables/final_problems_{app}_slide.csv")
        _check(full_table.exists(), f"Tabella problemi {app} presente", f"Tabella problemi {app} mancante", rows)
        _check(slide_table.exists(), f"Tabella problemi slide {app} presente", f"Tabella problemi slide {app} mancante", rows)
        if full_table.exists():
            df = pd.read_csv(full_table, encoding="utf-8-sig")
            _check("description" in df and df["description"].astype(str).str.len().gt(40).all(), f"Descrizioni complete presenti per {app}", f"Descrizioni mancanti o troppo brevi per {app}", rows)
            _check("description" in df and not df["description"].astype(str).str.contains(r"\.\.\.", regex=True).any(), f"Nessuna ellissi nelle descrizioni {app}", f"Ellissi trovata nelle descrizioni {app}", rows)
            if {"severity_mean", "problem_id"}.issubset(df.columns):
                sortable = df.copy()
                _check({"severity_median", "severity_std"}.issubset(sortable.columns), f"Statistiche complete presenti per {app}", f"Mediana/deviazione standard mancanti per {app}", rows)
                sortable["severity_mean"] = pd.to_numeric(sortable["severity_mean"], errors="coerce").fillna(-1)
                sortable["severity_median"] = pd.to_numeric(sortable.get("severity_median"), errors="coerce").fillna(-1)
                sortable["severity_std"] = pd.to_numeric(sortable.get("severity_std"), errors="coerce").fillna(-1)
                if "priority_rank" not in sortable.columns:
                    sortable["priority_rank"] = sortable.get("priority_band", "").map({"A": 0, "B": 1, "C": 2, "unrated": 9}).fillna(9).astype(int)
                sort_columns = ["priority_rank", "severity_mean", "severity_median", "severity_std", "problem_id"]
                ascending = [True, False, False, False, True]
                sorted_df = sortable.sort_values(sort_columns, ascending=ascending, kind="mergesort")
                _check(df["problem_id"].tolist() == sorted_df["problem_id"].tolist(), f"Problemi {app} ordinati per priorita e severita", f"Problemi {app} non ordinati per priorita e severita", rows)

    demographics_ok = run_demographics_quality_check(config)
    _check(demographics_ok, "Audit composizione campioni demografici superato", "Audit composizione campioni demografici fallito", rows)

    deck_findings = audit_final_deck_text()
    _check(not deck_findings, "Deck finale senza placeholder o path tecnici", f"Deck finale contiene {len(deck_findings)} testo/i vietato/i", rows)
    pptx_path = resolve_path("outputs/slides/final_report.pptx")
    if pptx_path.exists():
        try:
            with zipfile.ZipFile(pptx_path) as deck:
                slide_texts = []
                full_text = []
                for name in deck.namelist():
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                        xml = deck.read(name).decode("utf-8", errors="ignore")
                        plain = re.sub(r"<[^>]+>", " ", xml)
                        full_text.append(plain)
                        if "Tabella tempi user test" in plain:
                            slide_texts.append(plain)
                _check(len(slide_texts) == 4, "Deck contiene 4 slide tabella tempi user test", f"Deck contiene {len(slide_texts)}/4 slide tabella tempi user test", rows)
                combined = " ".join(slide_texts)
                _check(all(f"U{index}" in combined for index in range(1, 25)), "Deck tempi contiene U1-U24", "Deck tempi non contiene tutti gli utenti U1-U24", rows)
                all_deck_text = " ".join(full_text)
                _check("Matrice descrittiva del profilo utenti" not in all_deck_text and "user_expertise_matrix" not in all_deck_text, "Deck non contiene matrice expertise utenti", "Deck contiene ancora matrice expertise utenti", rows)
                _check("Apple Mappe" not in all_deck_text and "Google Maps" not in all_deck_text, "Deck senza label esempio Apple/Google", "Deck contiene label esempio Apple/Google", rows)
        except Exception as exc:
            _check(False, "", f"Audit slide tempi non eseguibile: {exc}", rows)

    item_desc = resolve_path("outputs/tables/questionnaire_item_descriptives.csv")
    item_interpretations = resolve_path("outputs/tables/questionnaire_item_interpretations.csv")
    if item_desc.exists():
        desc = pd.read_csv(item_desc, encoding="utf-8-sig")
        item_ids = set(desc.get("item_id", pd.Series(dtype=int)).dropna().astype(int))
        _check(set(range(1, 27)).issubset(item_ids), "Questionario copre le 26 domande", f"Questionario copre {len(item_ids)}/26 domande", rows)
        _check({"min", "q1", "mean", "median", "q3", "max"}.issubset(desc.columns), "Descrittive questionario complete", "Descrittive questionario min/q1/media/mediana/q3/max mancanti", rows)
    else:
        _check(False, "", "Descrittive questionario per item mancanti", rows)
    _check(item_interpretations.exists(), "Interpretazioni questionario presenti", "Interpretazioni questionario mancanti", rows)

    deck_config = resolve_path("slides/config/slide_deck.yml")
    if deck_config.exists():
        text = deck_config.read_text(encoding="utf-8")
        demo_refs = [line.strip() for line in text.splitlines() if "demo" in line.lower()]
        _check(not demo_refs, "Nessun riferimento demo nel deck finale", f"Riferimenti demo nel deck finale: {'; '.join(demo_refs[:3])}", rows)

    for doc in sorted(resolve_path("docs").glob("*.md")) + [resolve_path("README.md")]:
        try:
            text = doc.read_text(encoding="utf-8")
            _check(True, f"UTF-8 valido: {doc.relative_to(resolve_path('.'))}", "", rows)
        except UnicodeDecodeError:
            _check(False, "", f"Encoding non UTF-8: {doc}", rows)
            continue
        bad_words = [match.group(0) for match in DOC_WORD_RE.finditer(text)]
        _warn(not bad_words, f"Accenti OK: {doc.name}", f"Possibili accenti mancanti in {doc.name}: {', '.join(sorted(set(bad_words)))}", rows)
        for link in LOCAL_LINK_RE.findall(text):
            if "://" in link or link.startswith("#"):
                continue
            target = (doc.parent / link).resolve()
            _check(target.exists(), f"Link locale valido in {doc.name}: {link}", f"Link locale rotto in {doc.name}: {link}", rows)

    has_failures = any(row["status"] == "FAIL" for row in rows)
    if has_failures:
        status = "NEEDS_FIXES"
    elif observed_user_count >= 24:
        status = "READY_FOR_FINAL_SLIDES"
    else:
        status = "PARTIAL_READY_FOR_REVIEW"
    lines = ["# Final Quality Check", "", "| status | check |", "|---|---|"]
    lines.extend(f"| {row['status']} | {row['check']} |" for row in rows)
    lines.extend(["", f"STATUS: {status}", ""])
    target = resolve_path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    return status in {"READY_FOR_FINAL_SLIDES", "PARTIAL_READY_FOR_REVIEW"}


def run_demographics_quality_check(config: dict) -> bool:
    experts_path = resolve_path("data/processed/heuristics/expert_profiles.csv")
    if not experts_path.exists():
        return False
    experts_df = pd.read_csv(experts_path)
    
    unique_experts = experts_df["evaluator_id"].nunique() if "evaluator_id" in experts_df.columns else 0
    gender_tot = experts_df["gender"].dropna().count() if "gender" in experts_df.columns else 0
    age_tot = experts_df["age_group"].dropna().count() if "age_group" in experts_df.columns else 0
    profile_tot = experts_df["occupation"].dropna().count() if "occupation" in experts_df.columns else 0
    fam_tot = experts_df["familiarity"].dropna().count() if "familiarity" in experts_df.columns else 0
    
    expert_split_no = "system" not in experts_df.columns and "app" not in experts_df.columns
    
    experts_ok = (unique_experts == 8 and gender_tot == 8 and age_tot == 8 and profile_tot == 8 and fam_tot == 8 and expert_split_no)
    
    users_path = resolve_path(config["paths"]["questionnaire_system_1"])
    if not users_path.exists():
        users_path = resolve_path(config["paths"]["questionnaire_system_2"])
    if not users_path.exists():
        return False
        
    users_df = pd.read_csv(users_path)
    if "item" in users_df.columns:
        users_df = users_df.set_index("item")
    elif "item" == users_df.index.name:
        pass
    else:
        users_df = users_df.set_index(users_df.columns[0])
        
    user_cols = [c for c in users_df.columns if c != "item"]
    unique_users = len(user_cols)
    
    gender_user_tot = users_df.loc["genere"].dropna().count() if "genere" in users_df.index else 0
    age_user_tot = users_df.loc["eta"].dropna().count() if "eta" in users_df.index else 0
    profession_user_tot = users_df.loc["situazione lavorativa"].dropna().count() if "situazione lavorativa" in users_df.index else 0
    fam_user_tot = users_df.loc["familiarita delivery"].dropna().count() if "familiarita delivery" in users_df.index else 0
    
    users_split_no = "system" not in users_df.index and "app" not in users_df.index
    
    users_ok = (unique_users == 24 and gender_user_tot == 24 and age_user_tot == 24 and profession_user_tot == 24 and fam_user_tot == 24 and users_split_no)
    
    status = "PASS" if (experts_ok and users_ok) else "FAIL"
    
    report_lines = [
        "# Demographics Quality Check",
        "",
        "## Experts",
        "",
        f"- Unique experts: {unique_experts}",
        f"- Gender total: {gender_tot}",
        f"- Age total: {age_tot}",
        f"- Profile total: {profile_tot}",
        f"- Familiarity total: {fam_tot}",
        f"- App/system split used: {'yes' if not expert_split_no else 'no'}",
        "",
        "## Users",
        "",
        f"- Unique users: {unique_users}",
        f"- Gender total: {gender_user_tot}",
        f"- Age total: {age_user_tot}",
        f"- Profession total: {profession_user_tot}",
        f"- Familiarity total: {fam_user_tot}",
        f"- App/system split used: {'yes' if not users_split_no else 'no'}",
        "",
        "## Status",
        "",
        status,
        ""
    ]
    
    report_path = resolve_path("outputs/reports/demographics_quality_check.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    
    return status == "PASS"
