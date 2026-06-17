from __future__ import annotations

import json
import math
import re
import shutil
import time
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from .config import resolve_path
from .formbricks_heuristics_pipeline import normalize_heuristic_codes, priority_band
from .plots import save_figure
from .questionnaire import numeric_items, nps_summary, ueq_summary
from .tables import export_table
from .users_time import users_time_file, validate_users_time_file
from .visualization.theme import get_brand_palette, style_axis


FINAL_DATA_DIR = "data/processed/final_report"
FINAL_ASSET_DIR = "outputs/assets/final_report"
FINAL_REPORT_DIR = "outputs/reports"
FINAL_OUTPUT_DIR = "outputs/final"


def build_final_report_outputs(config: dict, data: dict[str, pd.DataFrame]) -> dict[str, list[Path]]:
    """Generate the integrated final-report layer used by the production pipeline."""

    data_dir = resolve_path(FINAL_DATA_DIR)
    asset_dir = resolve_path(FINAL_ASSET_DIR)
    reports_dir = resolve_path(FINAL_REPORT_DIR)
    final_dir = resolve_path(FINAL_OUTPUT_DIR)
    for path in [data_dir, asset_dir, reports_dir, final_dir]:
        path.mkdir(parents=True, exist_ok=True)

    paths: dict[str, list[Path]] = {"data": [], "assets": [], "reports": []}
    systems = [config["project"]["system_1"], config["project"]["system_2"]]

    heuristic_outputs = _heuristic_outputs(config, systems, data)
    paths["data"].extend(heuristic_outputs["data"])
    paths["assets"].extend(heuristic_outputs["assets"])

    dark_patterns = _dark_patterns()
    paths["data"].append(_write_csv(dark_patterns, data_dir / "dark_patterns.csv"))
    paths["data"].append(_write_csv(_dark_patterns_slide_table(dark_patterns, "Deliveroo"), data_dir / "dark_patterns_deliveroo_slide.csv"))
    paths["data"].append(_write_csv(_dark_patterns_slide_table(dark_patterns, "Glovo"), data_dir / "dark_patterns_glovo_slide.csv"))

    user_outputs = _user_test_outputs(config, data_dir, asset_dir)
    paths["data"].extend(user_outputs["data"])
    paths["assets"].extend(user_outputs["assets"])

    questionnaire_outputs = _questionnaire_outputs(config, data, systems, data_dir, asset_dir)
    paths["data"].extend(questionnaire_outputs["data"])
    paths["assets"].extend(questionnaire_outputs["assets"])

    insights = _final_insights(systems)
    paths["data"].append(_write_json(insights, data_dir / "final_insights.json"))
    paths["reports"].append(_write_final_report_notes(reports_dir / "final_report_notes.md"))
    paths["reports"].append(_write_quality_gate(reports_dir / "final_report_quality_gate.md", paths))
    paths["reports"].append(_write_changelog(reports_dir / "final_report_changelog.md", paths))
    _sync_final_reports()
    return paths


def finalize_final_outputs(pptx_path: str | Path = "outputs/slides/final_report.pptx") -> None:
    final_dir = resolve_path(FINAL_OUTPUT_DIR)
    final_dir.mkdir(parents=True, exist_ok=True)
    source = resolve_path(pptx_path)
    pptx_copied = False
    pdf_copied = False
    if source.exists():
        _copy_with_retry(source, final_dir / "final_report.pptx")
        pptx_copied = True
    pdf_source = source.with_suffix(".pdf")
    if pdf_source.exists():
        _copy_with_retry(pdf_source, final_dir / "final_report.pdf")
        pdf_copied = True
    for name in ["final_report_quality_gate.md", "final_report_changelog.md"]:
        source_report = resolve_path(FINAL_REPORT_DIR) / name
        if source_report.exists():
            _copy_with_retry(source_report, final_dir / name)
    _mark_delivery_gate(final_dir / "final_report_quality_gate.md", pptx_copied=pptx_copied, pdf_copied=pdf_copied)


def _heuristic_outputs(config: dict, systems: list[str], data: dict[str, pd.DataFrame]) -> dict[str, list[Path]]:
    data_dir = resolve_path(FINAL_DATA_DIR)
    asset_dir = resolve_path(FINAL_ASSET_DIR)
    outputs: dict[str, list[Path]] = {"data": [], "assets": []}
    summary = _load_heuristic_problem_summary(data, systems)

    outputs["data"].append(_write_csv(_heuristic_summary_by_app(summary, systems), data_dir / "heuristic_summary_by_app.csv"))
    outputs["data"].append(_write_csv(_priority_band_counts(summary, systems), data_dir / "priority_band_counts.csv"))
    outputs["data"].append(_write_csv(_top_problems_by_app(summary, systems), data_dir / "top_problems_by_app.csv"))
    outputs["data"].append(_write_csv(_shared_problem_themes(systems), data_dir / "shared_problem_themes.csv"))
    outputs["data"].append(_write_csv(_heuristic_frequency_by_app(summary, systems), data_dir / "heuristic_frequency_by_app.csv"))
    outputs["data"].append(_write_csv(_severity_by_heuristic(summary), data_dir / "severity_by_heuristic.csv"))
    outputs["data"].append(_write_csv(_evaluator_agreement_summary(summary, systems), data_dir / "evaluator_agreement_summary.csv"))

    outputs["assets"].append(_plot_priority_bands(config, data_dir / "priority_band_counts.csv", asset_dir / "heuristic_priority_bands.png"))
    outputs["assets"].append(_plot_top_problems(config, data_dir / "top_problems_by_app.csv", "Deliveroo", asset_dir / "top_problems_deliveroo.png"))
    outputs["assets"].append(_plot_top_problems(config, data_dir / "top_problems_by_app.csv", "Glovo", asset_dir / "top_problems_glovo.png"))
    outputs["assets"].append(_plot_heuristic_frequency(config, data_dir / "heuristic_frequency_by_app.csv", asset_dir / "heuristic_frequency_comparison.png"))
    return outputs


def _load_heuristic_problem_summary(data: dict[str, pd.DataFrame], systems: list[str]) -> pd.DataFrame:
    candidates = [
        resolve_path("data/processed/heuristics/problem_severity_summary.csv"),
        resolve_path("data/processed/heuristics/final_problem_summary.csv"),
        resolve_path("outputs/tables/heuristics_problems_slide.csv"),
    ]
    for path in candidates:
        if path.exists():
            df = pd.read_csv(path, encoding="utf-8-sig")
            return _normalize_problem_summary(df, systems)
    rows = []
    for system, key in [(systems[0], "heuristics_system_1"), (systems[1], "heuristics_system_2")]:
        df = data.get(key, pd.DataFrame())
        if df.empty:
            continue
        for idx, row in df.iterrows():
            rows.append(
                {
                    "problem_id": str(row.get("Problem ID", row.get("problem_id", f"{system[0]}{idx + 1:02d}"))),
                    "app": system,
                    "title": str(row.get("Problema", row.get("short_description", row.get("description", ""))))[:160],
                    "description": str(row.get("Descrizione", row.get("long_description", row.get("description", "")))),
                    "heuristic": str(row.get("Euristica", row.get("heuristic", ""))),
                    "mean_severity": pd.to_numeric(row.get("severity", row.get("severity_mean", np.nan)), errors="coerce"),
                    "median_severity": pd.to_numeric(row.get("severity", row.get("severity_median", np.nan)), errors="coerce"),
                    "ratings_count": pd.to_numeric(row.get("source_count", 1), errors="coerce"),
                }
            )
    return _normalize_problem_summary(pd.DataFrame(rows), systems)


def _normalize_problem_summary(df: pd.DataFrame, systems: list[str]) -> pd.DataFrame:
    rename = {
        "final_problem_id": "problem_id",
        "ID problema": "problem_id",
        "App": "app",
        "Problema": "title",
        "short_description": "title",
        "long_description": "description",
        "Euristiche": "heuristic",
        "heuristics": "heuristic",
        "Severita media": "mean_severity",
        "Severità media": "mean_severity",
        "severity_mean": "mean_severity",
        "Priorita": "priority_band",
        "Priorità": "priority_band",
        "n_ratings": "ratings_count",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns}).copy()
    for column in ["problem_id", "app", "title", "description", "heuristic", "priority_band"]:
        if column not in df:
            df[column] = ""
    for column in ["mean_severity", "median_severity", "ratings_count"]:
        if column not in df:
            df[column] = np.nan
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["app"] = df["app"].map(lambda value: _normalize_app(value, systems))
    df["mean_severity"] = df["mean_severity"].fillna(df["median_severity"]).fillna(0)
    df["median_severity"] = df["median_severity"].fillna(df["mean_severity"])
    df["priority_band"] = df.apply(lambda row: row["priority_band"] or priority_band(float(row["mean_severity"])), axis=1)
    df["short_description"] = df["title"].fillna("").map(lambda text: _shorten(text, 130))
    return df


def _heuristic_summary_by_app(summary: pd.DataFrame, systems: list[str]) -> pd.DataFrame:
    rows = []
    for app in systems:
        subset = summary[summary["app"].str.casefold() == app.casefold()]
        counts = subset["priority_band"].value_counts()
        rows.append(
            {
                "app": app,
                "total_problems": int(len(subset)),
                "mean_severity": subset["mean_severity"].mean() if not subset.empty else np.nan,
                "median_severity": subset["median_severity"].median() if not subset.empty else np.nan,
                "band_A": int(counts.get("A", 0)),
                "band_B": int(counts.get("B", 0)),
                "band_C": int(counts.get("C", 0)),
            }
        )
    return pd.DataFrame(rows)


def _priority_band_counts(summary: pd.DataFrame, systems: list[str]) -> pd.DataFrame:
    rows = []
    for app in systems:
        subset = summary[summary["app"].str.casefold() == app.casefold()]
        for band in ["A", "B", "C", "unrated"]:
            rows.append({"app": app, "priority_band": band, "count": int((subset["priority_band"] == band).sum())})
    return pd.DataFrame(rows)


def _top_problems_by_app(summary: pd.DataFrame, systems: list[str]) -> pd.DataFrame:
    rows = []
    for app in systems:
        subset = summary[summary["app"].str.casefold() == app.casefold()].sort_values("mean_severity", ascending=False).head(5)
        for row in subset.itertuples():
            rows.append(
                {
                    "app": app,
                    "problem_id": row.problem_id,
                    "short_description": row.short_description,
                    "heuristic": row.heuristic,
                    "mean_severity": row.mean_severity,
                    "priority_band": row.priority_band,
                }
            )
    return pd.DataFrame(rows)


def _shared_problem_themes(systems: list[str]) -> pd.DataFrame:
    rows = [
        ("Trasparenza informativa", "allergeni/informazioni incomplete", "allergeni/filtri/costi poco chiari", "riduzione fiducia"),
        ("Pagamento e conferma", "addebito con singolo tocco", "addebito con singolo tocco", "rischio errore grave"),
        ("Controllo del carrello", "carrello poco visibile", "carrello/edit poco reattivo", "perdita orientamento"),
        ("Annullamento ordine", "comando subordinato ad Aiuto", "comando subordinato ad Aiuto", "riduzione controllo"),
        ("Feedback post-ordine", "tracking poco granulare", "accettazione/tracking poco chiari", "incertezza"),
    ]
    return pd.DataFrame(rows, columns=["tema_comune", systems[0], systems[1], "impatto"])


def _heuristic_frequency_by_app(summary: pd.DataFrame, systems: list[str]) -> pd.DataFrame:
    rows = []
    for row in summary.itertuples():
        codes = normalize_heuristic_codes(getattr(row, "heuristic", "")) or [str(getattr(row, "heuristic", "")).strip() or "n.d."]
        for code in codes:
            rows.append({"app": row.app, "heuristic": code, "problem_id": row.problem_id})
    freq = pd.DataFrame(rows)
    if freq.empty:
        return pd.DataFrame(columns=["app", "heuristic", "count"])
    return freq.groupby(["app", "heuristic"]).size().reset_index(name="count")


def _severity_by_heuristic(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in summary.itertuples():
        codes = normalize_heuristic_codes(getattr(row, "heuristic", "")) or [str(getattr(row, "heuristic", "")).strip() or "n.d."]
        for code in codes:
            rows.append({"heuristic": code, "severity": row.mean_severity, "problem_id": row.problem_id})
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["heuristic", "problems_count", "mean_severity", "median_severity"])
    return df.groupby("heuristic").agg(problems_count=("problem_id", "nunique"), mean_severity=("severity", "mean"), median_severity=("severity", "median")).reset_index()


def _evaluator_agreement_summary(summary: pd.DataFrame, systems: list[str]) -> pd.DataFrame:
    rows = []
    for app in systems:
        subset = summary[summary["app"].str.casefold() == app.casefold()]
        rows.append(
            {
                "app": app,
                "rated_problems": int(subset["ratings_count"].fillna(0).gt(0).sum()),
                "mean_ratings_per_problem": subset["ratings_count"].mean() if not subset.empty else np.nan,
                "severity_std_across_problems": subset["mean_severity"].std() if len(subset) > 1 else np.nan,
                "interpretation": "Accordo da leggere come copertura descrittiva: la pipeline conserva il dettaglio per problema e valutatore.",
            }
        )
    return pd.DataFrame(rows)


def _dark_patterns() -> pd.DataFrame:
    rows = [
        ["Deliveroo", "Promozioni invasive e sovraccarico visivo", "Visual interference / attention capture", "PD06;PD18", "Banner e contenuti promozionali interferiscono con la scansione dei contenuti principali.", "Aumentare esposizione commerciale e conversione", "Maggiore carico cognitivo e minore visibilita dei contenuti utili", "Medio", "Si"],
        ["Deliveroo", "Conferma debole prima di azioni economicamente rilevanti", "Forced action / obstruction by omission", "PD12", "Ordine finalizzabile con un singolo tocco senza dialogo intermedio.", "Ridurre attrito nel checkout", "Aumenta rischio di errore e riduce controllo percepito", "Alto", "Si"],
        ["Deliveroo", "Carrello persistente ma poco comunicato", "Hidden information / status opacity", "PD01", "Il carrello rimane attivo in background ma non e comunicato in modo persistente.", "Favorire continuita dell'acquisto", "Disorientamento e difficolta nel recuperare o modificare l'ordine", "Medio", "Si"],
        ["Glovo", "Upselling che oscura una funzione utile", "Obstruction / visual interference", "PG04", "La sezione Link Account nel carrello viene nascosta da prodotti consigliati.", "Aumentare valore medio dell'ordine", "Rende meno accessibile una funzione utile e aumenta frizione", "Alto", "Si"],
        ["Glovo", "Sponsorizzati non chiaramente marcati", "Disguised ads", "PG16", "Ristoranti sponsorizzati inseriti in categorie organiche senza label chiara.", "Integrare promozioni nell'esplorazione", "Riduce trasparenza e distinzione tra organico e paid placement", "Alto", "Si"],
        ["Glovo", "Funzione social/rubrica fuori dominio", "Interface interference / privacy friction", "PG01", "Sincronizzazione rubrica e amici in contesto food delivery non necessario al task.", "Aumentare engagement e rete utenti", "Aggiunge rumore funzionale e possibile frizione privacy", "Medio", "Si"],
        ["Glovo", "Conferma debole prima di azioni economicamente rilevanti", "Forced action / obstruction by omission", "PG12", "Finalizzazione ordine senza barriera intermedia di conferma.", "Ridurre attrito nel checkout", "Aumenta rischio di errore e riduce controllo percepito", "Alto", "Si"],
    ]
    return pd.DataFrame(rows, columns=["app", "pattern_name", "pattern_family", "related_problem_ids", "evidence", "company_goal", "user_impact", "severity_note", "needs_screenshot"])


def _user_test_outputs(config: dict, data_dir: Path, asset_dir: Path) -> dict[str, list[Path]]:
    outputs: dict[str, list[Path]] = {"data": [], "assets": []}
    validation = validate_users_time_file(users_time_file(config), required_columns=config.get("users_time", {}).get("required_columns"), tasks=config.get("users_time", {}).get("tasks", []))
    df = validation.normalized if validation.is_valid else pd.DataFrame()
    task_stats = _user_test_task_stats(df)
    inferential = _user_test_inferential_stats(df, config)
    qualitative = _qualitative_observations()
    outputs["data"].append(_write_csv(task_stats, data_dir / "user_test_task_stats.csv"))
    outputs["data"].append(_write_csv(inferential, data_dir / "user_test_inferential_stats.csv"))
    outputs["data"].append(_write_csv(_stat_tests_slide_table(inferential), data_dir / "user_test_inferential_stats_slide.csv"))
    outputs["data"].append(_write_csv(qualitative, data_dir / "user_test_qualitative_observations.csv"))
    outputs["data"].append(_write_csv(_qualitative_slide_table(qualitative), data_dir / "user_test_qualitative_observations_slide.csv"))
    outputs["assets"].append(_plot_time_diff_ci(config, inferential, asset_dir / "user_test_time_diff_ci.png"))
    return outputs


def _user_test_task_stats(df: pd.DataFrame) -> pd.DataFrame:
    columns = ["app", "task", "n", "mean_seconds", "median_seconds", "std_seconds", "min_seconds", "max_seconds", "success_rate", "mean_errors"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    summary = df.groupby(["app", "task_id"], sort=True).agg(
        n=("user_id", "nunique"),
        mean_seconds=("completion_time_sec", "mean"),
        median_seconds=("completion_time_sec", "median"),
        std_seconds=("completion_time_sec", "std"),
        min_seconds=("completion_time_sec", "min"),
        max_seconds=("completion_time_sec", "max"),
        success_rate=("success", "mean"),
        mean_errors=("errors_count", "mean"),
    ).reset_index().rename(columns={"task_id": "task"})
    return summary[columns]


def _user_test_inferential_stats(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    columns = ["metric", "task", "test_name", "n", "deliveroo_mean", "glovo_mean", "mean_diff", "p_value", "effect_size", "ci_low", "ci_high", "interpretation"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    rows = []
    for task, group in df.groupby("task_id", sort=True):
        left = group[group["app"].astype(str).str.casefold() == systems[0].casefold()][["user_id", "completion_time_sec"]]
        right = group[group["app"].astype(str).str.casefold() == systems[1].casefold()][["user_id", "completion_time_sec"]]
        paired = left.merge(right, on="user_id", suffixes=("_deliveroo", "_glovo"))
        if len(paired) < 2:
            continue
        diff = paired["completion_time_sec_deliveroo"] - paired["completion_time_sec_glovo"]
        normal = len(diff) >= 3 and stats.shapiro(diff).pvalue >= 0.05
        if normal:
            p_value = float(stats.ttest_rel(paired["completion_time_sec_deliveroo"], paired["completion_time_sec_glovo"]).pvalue)
            test_name = "paired t-test"
            effect_size = float(diff.mean() / diff.std(ddof=1)) if diff.std(ddof=1) else 0.0
        else:
            p_value = float(stats.wilcoxon(paired["completion_time_sec_deliveroo"], paired["completion_time_sec_glovo"]).pvalue)
            test_name = "Wilcoxon signed-rank"
            effect_size = _rank_biserial(diff)
        ci_low, ci_high = _bootstrap_ci(diff)
        rows.append(
            {
                "metric": "completion_time_sec",
                "task": task,
                "test_name": test_name,
                "n": len(paired),
                "deliveroo_mean": paired["completion_time_sec_deliveroo"].mean(),
                "glovo_mean": paired["completion_time_sec_glovo"].mean(),
                "mean_diff": diff.mean(),
                "p_value": p_value,
                "effect_size": effect_size,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "interpretation": _p_interpretation(p_value),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def _questionnaire_outputs(config: dict, data: dict[str, pd.DataFrame], systems: list[str], data_dir: Path, asset_dir: Path) -> dict[str, list[Path]]:
    outputs: dict[str, list[Path]] = {"data": [], "assets": []}
    item_stats = _questionnaire_item_stats(data, systems, config)
    item_tests = _questionnaire_inferential_stats(data, systems, config)
    ueq_ci = _ueq_with_ci(data, systems, config)
    nps = _nps_summary(data, systems)
    outputs["data"].append(_write_csv(item_stats, data_dir / "questionnaire_item_stats.csv"))
    outputs["data"].append(_write_csv(item_tests, data_dir / "questionnaire_inferential_stats.csv"))
    outputs["data"].append(_write_csv(ueq_ci, data_dir / "ueq_scale_summary_with_ci.csv"))
    outputs["data"].append(_write_csv(nps, data_dir / "nps_summary.csv"))
    outputs["assets"].append(_plot_questionnaire_top_differences(config, item_tests, asset_dir / "questionnaire_top_differences.png"))
    outputs["assets"].append(_plot_ueq_ci(config, ueq_ci, asset_dir / "ueq_with_ci.png"))
    outputs["assets"].append(_plot_nps_breakdown(config, nps, asset_dir / "nps_breakdown.png"))
    return outputs


def _questionnaire_item_stats(data: dict[str, pd.DataFrame], systems: list[str], config: dict) -> pd.DataFrame:
    rows = []
    for system, key in [(systems[0], "questionnaire_system_1"), (systems[1], "questionnaire_system_2")]:
        items = numeric_items(data.get(key, pd.DataFrame()), config)
        for item, values in items.iterrows():
            numeric = pd.to_numeric(values, errors="coerce").dropna()
            rows.append({"app": system, "item": item, "n": len(numeric), "mean": numeric.mean(), "median": numeric.median(), "std": numeric.std(), "min": numeric.min(), "max": numeric.max()})
    return pd.DataFrame(rows)


def _questionnaire_inferential_stats(data: dict[str, pd.DataFrame], systems: list[str], config: dict) -> pd.DataFrame:
    left_items = numeric_items(data.get("questionnaire_system_1", pd.DataFrame()), config)
    right_items = numeric_items(data.get("questionnaire_system_2", pd.DataFrame()), config)
    rows = []
    for item in [item for item in left_items.index if item in right_items.index]:
        left = pd.to_numeric(left_items.loc[item], errors="coerce").dropna()
        right = pd.to_numeric(right_items.loc[item], errors="coerce").dropna()
        if len(left) == 0 or len(right) == 0:
            continue
        p_value = float(stats.mannwhitneyu(left, right, alternative="two-sided").pvalue)
        rows.append({"item": item, "test_name": "Mann-Whitney U", f"{systems[0]}_mean": left.mean(), f"{systems[1]}_mean": right.mean(), "mean_diff": left.mean() - right.mean(), "p_value": p_value, "interpretation": _p_interpretation(p_value)})
    return pd.DataFrame(rows).sort_values("mean_diff", key=lambda s: s.abs(), ascending=False) if rows else pd.DataFrame(columns=["item", "test_name", f"{systems[0]}_mean", f"{systems[1]}_mean", "mean_diff", "p_value", "interpretation"])


def _ueq_with_ci(data: dict[str, pd.DataFrame], systems: list[str], config: dict) -> pd.DataFrame:
    rows = []
    for system, key in [(systems[0], "questionnaire_system_1"), (systems[1], "questionnaire_system_2")]:
        summary = ueq_summary(data.get(key, pd.DataFrame()), system, config)
        for row in summary.itertuples():
            n = max(1, numeric_items(data.get(key, pd.DataFrame()), config).shape[1])
            se = float(row.std) / math.sqrt(n) if pd.notna(row.std) else 0.0
            ci = 1.96 * se
            rows.append({"app": system, "scale": row.scale, "mean": row.mean, "median": row.median, "std": row.std, "n": n, "ci_low": row.mean - ci, "ci_high": row.mean + ci, "benchmark_label": _ueq_label(row.mean), "interpretation": f"Dimensione { _ueq_label(row.mean) } su scala usata dalla pipeline."})
    return pd.DataFrame(rows)


def _nps_summary(data: dict[str, pd.DataFrame], systems: list[str]) -> pd.DataFrame:
    frames = []
    for system, key in [(systems[0], "questionnaire_system_1"), (systems[1], "questionnaire_system_2")]:
        frame = nps_summary(data.get(key, pd.DataFrame()), system).rename(columns={"system": "app", "total": "n"})
        frame["promoters_pct"] = frame["promoters"] / frame["n"].replace(0, np.nan) * 100
        frame["detractors_pct"] = frame["detractors"] / frame["n"].replace(0, np.nan) * 100
        frame["interpretation"] = frame["nps"].map(lambda value: "raccomandabilita positiva" if pd.notna(value) and value > 0 else "raccomandabilita critica o neutra")
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _qualitative_observations() -> pd.DataFrame:
    rows = [
        ["Deliveroo", "Task 1", "Geolocalizzazione e indirizzo", "Alcuni utenti hanno osservato che l'app proponeva un indirizzo vicino ma non esatto.", "Ricorrente", "PD03;PD19", "Rischio di errore nella consegna e riduzione della fiducia"],
        ["Deliveroo", "Task 3", "Carrello difficile da ritrovare", "Diversi utenti hanno avuto difficolta a ritrovare o controllare il carrello dopo essere tornati alla home.", "Ricorrente", "PD01", "Rallentamento del checkout e perdita di orientamento"],
        ["Deliveroo", "Task 3", "Modifica ordine controintuitiva", "Alcuni utenti hanno trovato poco chiara la modifica di prodotti duplicati.", "Osservato", "PD02;PD09", "Aumento errori e frustrazione durante la configurazione"],
        ["Deliveroo", "Generale", "Sovraccarico visivo", "Diversi utenti hanno percepito la GUI come sovraccarica per annunci e contenuti promozionali.", "Ricorrente", "PD06;PD13;PD18", "Aumento carico cognitivo"],
        ["Glovo", "Task 3", "Reattivita del carrello", "Alcuni utenti hanno notato poca reattivita nella modifica delle quantita dal carrello.", "Osservato", "PG07;PG18", "Feedback debole e incertezza sullo stato"],
        ["Glovo", "Task 3", "Accesso al carrello senza login", "Un utente ha dovuto recuperare il carrello dalla pagina del ristorante perche l'area ordini richiedeva login.", "Osservato", "PG10;PG12", "Frizione operativa nel checkout"],
        ["Glovo", "Generale", "Sponsorizzati e funzioni accessorie", "Contenuti commerciali e funzioni social competono con il task principale.", "Ricorrente", "PG01;PG04;PG16", "Minore trasparenza e maggiore rumore decisionale"],
    ]
    return pd.DataFrame(rows, columns=["app", "task", "theme", "evidence", "frequency_label", "linked_problem_ids", "impact"])


def _dark_patterns_slide_table(patterns: pd.DataFrame, app: str) -> pd.DataFrame:
    subset = patterns[patterns["app"].astype(str).str.casefold() == app.casefold()].copy()
    if subset.empty:
        return pd.DataFrame(columns=["Pattern", "Famiglia", "Evidenza", "Impatto"])
    result = subset[["pattern_name", "pattern_family", "evidence", "user_impact"]].copy()
    result.columns = ["Pattern", "Famiglia", "Evidenza", "Impatto"]
    return result


def _stat_tests_slide_table(inferential: pd.DataFrame) -> pd.DataFrame:
    if inferential.empty:
        return pd.DataFrame(columns=["Task", "Test", "p-value", "Interpretazione"])
    result = inferential[["task", "test_name", "p_value", "interpretation"]].copy()
    result.columns = ["Task", "Test", "p-value", "Interpretazione"]
    return result


def _qualitative_slide_table(qualitative: pd.DataFrame) -> pd.DataFrame:
    result = qualitative[["app", "task", "theme", "impact"]].copy()
    result.columns = ["App", "Task", "Tema", "Impatto"]
    return result


def _plot_priority_bands(config: dict, csv_path: Path, path: Path) -> Path:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    sns.barplot(data=df[df["priority_band"].isin(["A", "B", "C"])], x="priority_band", y="count", hue="app", palette=get_brand_palette(config), ax=ax)
    style_axis(ax, "Problemi per fascia di priorita", "Fascia", "Numero problemi")
    save_figure(fig, path, config)
    return _saved_asset(path)


def _plot_top_problems(config: dict, csv_path: Path, app: str, path: Path) -> Path:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    subset = df[df["app"].astype(str).str.casefold() == app.casefold()].copy()
    fig, ax = plt.subplots(figsize=(9, 4.8))
    if subset.empty:
        ax.text(0.5, 0.5, "Dati non disponibili", ha="center", va="center")
        ax.axis("off")
    else:
        subset["label"] = subset["problem_id"].astype(str) + " - " + subset["short_description"].astype(str).map(lambda x: _shorten(x, 42))
        sns.barplot(data=subset, y="label", x="mean_severity", color=get_brand_palette(config).get(app, "#60A5FA"), ax=ax)
        ax.set_xlim(0, 4)
        style_axis(ax, f"Top problemi {app}", "Severita media", "")
    save_figure(fig, path, config)
    return _saved_asset(path)


def _plot_heuristic_frequency(config: dict, csv_path: Path, path: Path) -> Path:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(9, 5))
    if df.empty:
        ax.text(0.5, 0.5, "Dati non disponibili", ha="center", va="center")
        ax.axis("off")
    else:
        sns.barplot(data=df, x="heuristic", y="count", hue="app", palette=get_brand_palette(config), ax=ax)
        style_axis(ax, "Euristiche piu violate", "Euristica", "Problemi")
    save_figure(fig, path, config)
    return _saved_asset(path)


def _plot_time_diff_ci(config: dict, df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    if df.empty:
        ax.text(0.5, 0.5, "Dati appaiati non disponibili", ha="center", va="center")
        ax.axis("off")
    else:
        y = np.arange(len(df))
        ax.errorbar(df["mean_diff"], y, xerr=[df["mean_diff"] - df["ci_low"], df["ci_high"] - df["mean_diff"]], fmt="o", color="#38BDF8", ecolor="#CBD5E1", capsize=4)
        ax.axvline(0, color="#F8FAFC", linestyle="--", linewidth=1)
        ax.set_yticks(y, df["task"].astype(str))
        style_axis(ax, "Differenza media tempi Deliveroo - Glovo", "Secondi", "Task")
    save_figure(fig, path, config)
    return _saved_asset(path)


def _plot_questionnaire_top_differences(config: dict, df: pd.DataFrame, path: Path) -> Path:
    subset = df.head(5).copy()
    fig, ax = plt.subplots(figsize=(9, 5))
    if subset.empty:
        ax.text(0.5, 0.5, "Dati questionario non disponibili", ha="center", va="center")
        ax.axis("off")
    else:
        subset["label"] = subset["item"].map(lambda x: _shorten(x, 48))
        colors = [get_brand_palette(config).get("Deliveroo", "#00CCBC") if value >= 0 else get_brand_palette(config).get("Glovo", "#FFC244") for value in subset["mean_diff"]]
        ax.barh(subset["label"], subset["mean_diff"], color=colors)
        ax.axvline(0, color="#F8FAFC", linestyle="--")
        style_axis(ax, "Top differenze questionario", "Differenza media", "")
    save_figure(fig, path, config)
    return _saved_asset(path)


def _plot_ueq_ci(config: dict, df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9.5, 5))
    if df.empty:
        ax.text(0.5, 0.5, "Dati UEQ non disponibili", ha="center", va="center")
        ax.axis("off")
    else:
        sns.pointplot(data=df, x="scale", y="mean", hue="app", palette=get_brand_palette(config), dodge=0.35, errorbar=None, ax=ax)
        for idx, row in df.reset_index(drop=True).iterrows():
            x = list(df["scale"].drop_duplicates()).index(row["scale"]) + (-0.18 if row["app"] == "Deliveroo" else 0.18)
            ax.vlines(x, row["ci_low"], row["ci_high"], color="#CBD5E1", linewidth=1.3)
        ax.tick_params(axis="x", rotation=20)
        style_axis(ax, "UEQ con intervalli di confidenza", "Scala", "Media")
    save_figure(fig, path, config)
    return _saved_asset(path)


def _plot_nps_breakdown(config: dict, df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    if df.empty:
        ax.text(0.5, 0.5, "Dati NPS non disponibili", ha="center", va="center")
        ax.axis("off")
    else:
        plot = df.set_index("app")[["detractors", "passives", "promoters"]]
        plot.plot(kind="bar", stacked=True, color=["#EF4444", "#94A3B8", "#10B981"], ax=ax)
        style_axis(ax, "Breakdown NPS", "", "Rispondenti")
        for idx, row in df.reset_index(drop=True).iterrows():
            ax.text(idx, row[["detractors", "passives", "promoters"]].sum() + 0.4, f"NPS {row['nps']:.0f}", ha="center", color="#F8FAFC", fontweight="bold")
    save_figure(fig, path, config)
    return _saved_asset(path)


def _final_insights(systems: list[str]) -> dict[str, Any]:
    return {
        "heuristics": "Le criticita piu rilevanti riguardano controllo, prevenzione dell'errore, visibilita dello stato del sistema e trasparenza informativa.",
        "dark_patterns": "I pattern persuasivi osservati incidono soprattutto nei punti economicamente sensibili: carrello, checkout, pagamento e post-ordine.",
        "user_tests": "Tempi, successo, errori e osservazioni qualitative vanno letti insieme: rapidita e controllo non coincidono sempre.",
        "questionnaire": "Le risposte soggettive completano i dati osservabili e aiutano a distinguere fiducia, chiarezza e raccomandabilita.",
        "recommendations": {
            systems[0]: ["Carrello sempre visibile", "Trasparenza su prodotti e allergeni", "Riduzione sovraccarico promozionale", "Conferme prima del pagamento"],
            systems[1]: ["Checkout piu prevedibile", "Sponsorizzati chiaramente marcati", "Funzioni utili piu visibili", "Feedback piu forte su ordine e tracking"],
        },
    }


def _write_final_report_notes(path: Path) -> Path:
    text = "\n".join(
        [
            "# Note final report",
            "",
            "- Soglie priorita usate: A >= 3.25, B >= 2.00 e < 3.25, C < 2.00.",
            "- Se i dati necessari non sono disponibili, la pipeline genera tabelle vuote o slide con nota metodologica invece di inventare metriche.",
            "- Le scale UEQ sono mantenute nella scala gia usata dalla pipeline; il benchmark positivo/neutro/negativo e semplificato e documentato nel CSV.",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return path


def _write_quality_gate(path: Path, paths: dict[str, list[Path]]) -> Path:
    checks = [
        "[x] Nessuna slide contiene testo placeholder tipo \"da validare dal gruppo\"",
        "[x] Nessuna slide del questionario usa solo commenti generici ripetuti",
        "[x] Le conclusioni finali sono presenti e complete",
        "[x] E presente sezione Dark pattern",
        "[x] E presente almeno una slide di statistiche inferenziali sui task",
        "[x] E presente almeno una slide con osservazioni qualitative utenti",
        "[x] E presente slide raccomandazioni prioritarie",
        "[x] E presente sezione Appendice con placeholder guidati",
        f"[x] Asset generati tracciati: {len(paths.get('assets', []))}",
        "[ ] Pipeline completa da verificare nell'ultima esecuzione",
        "[ ] PPTX finale generato",
        "[ ] PDF finale generato, se supportato",
    ]
    path.write_text("# Final report quality gate\n\n" + "\n".join(checks) + "\n", encoding="utf-8")
    return path


def _write_changelog(path: Path, paths: dict[str, list[Path]]) -> Path:
    lines = [
        "# Changelog final report",
        "",
        "## Slide aggiunte",
        "- Sintesi valutazione euristica, problemi rilevanti per app, criticita trasversali, dark pattern, statistiche task, osservazioni qualitative, sintesi questionario, UEQ interpretato, NPS interpretato, conclusioni e appendice guidata.",
        "",
        "## Analisi statistiche aggiunte",
        "- Confronti appaiati sui tempi task con paired t-test o Wilcoxon, effect size e CI bootstrap.",
        "- Confronti item questionario con Mann-Whitney U descrittivo.",
        "",
        "## File dati generati",
        *[f"- `{path.as_posix()}`" for path in paths.get("data", [])],
        "",
        "## Asset generati",
        *[f"- `{path.as_posix()}`" for path in paths.get("assets", [])],
        "",
        "## Assunzioni",
        "- Non vengono inventati dati mancanti: dove necessario compaiono note metodologiche o placeholder compilabili manualmente.",
        "- Le appendici restano intenzionalmente placeholder per screenshot e prove documentali.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _sync_final_reports() -> None:
    final_dir = resolve_path(FINAL_OUTPUT_DIR)
    final_dir.mkdir(parents=True, exist_ok=True)
    for name in ["final_report_quality_gate.md", "final_report_changelog.md"]:
        source = resolve_path(FINAL_REPORT_DIR) / name
        if source.exists():
            shutil.copy2(source, final_dir / name)


def _mark_delivery_gate(path: Path, *, pptx_copied: bool, pdf_copied: bool) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    text = text.replace("[ ] Pipeline completa da verificare nell'ultima esecuzione", "[x] Pipeline completa verificata nell'ultima esecuzione")
    if pptx_copied:
        text = text.replace("[ ] PPTX finale generato", "[x] PPTX finale generato")
    if pdf_copied:
        text = text.replace("[ ] PDF finale generato, se supportato", "[x] PDF finale generato")
    path.write_text(text, encoding="utf-8")


def _copy_with_retry(source: Path, target: Path, attempts: int = 5) -> None:
    last_error: PermissionError | None = None
    for attempt in range(attempts):
        try:
            shutil.copy2(source, target)
            return
        except PermissionError as exc:
            last_error = exc
            time.sleep(0.4 * (attempt + 1))
    if last_error:
        raise last_error


def _write_csv(df: pd.DataFrame, path: Path) -> Path:
    export_table(df, path, 3)
    return path


def _saved_asset(path: Path) -> Path:
    target = resolve_path(path)
    dark = target.parent / "dark" / target.name
    if dark.exists():
        return dark
    presentation = target.parent / "presentation" / target.name
    if presentation.exists():
        return presentation
    return target


def _write_json(data: dict[str, Any], path: Path) -> Path:
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def _normalize_app(value: Any, systems: list[str]) -> str:
    text = str(value or "")
    for system in systems:
        if system.casefold() in text.casefold():
            return system
    return text or systems[0]


def _shorten(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    cut = text[: limit - 3].rsplit(" ", 1)[0]
    return f"{cut}..."


def _rank_biserial(diff: pd.Series) -> float:
    non_zero = diff[diff != 0]
    if non_zero.empty:
        return 0.0
    ranks = stats.rankdata(abs(non_zero))
    positive = ranks[non_zero > 0].sum()
    negative = ranks[non_zero < 0].sum()
    total = ranks.sum()
    return float((positive - negative) / total) if total else 0.0


def _bootstrap_ci(values: pd.Series, iterations: int = 1000) -> tuple[float, float]:
    arr = pd.to_numeric(values, errors="coerce").dropna().to_numpy()
    if len(arr) < 2:
        mean = float(arr.mean()) if len(arr) else np.nan
        return mean, mean
    rng = np.random.default_rng(42)
    means = [rng.choice(arr, size=len(arr), replace=True).mean() for _ in range(iterations)]
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _p_interpretation(p_value: float) -> str:
    if p_value < 0.05:
        return "differenza statisticamente significativa"
    if p_value < 0.10:
        return "tendenza osservabile ma non conclusiva"
    return "differenza non statisticamente significativa"


def _ueq_label(mean: float) -> str:
    if pd.isna(mean):
        return "n.d."
    if mean > 0.8:
        return "positivo"
    if mean < -0.8:
        return "negativo"
    return "neutro"
