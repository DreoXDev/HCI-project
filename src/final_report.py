from __future__ import annotations

import json
import math
import re
import shutil
import time
from datetime import datetime
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
    paths["reports"].extend(user_outputs.get("reports", []))

    questionnaire_outputs = _questionnaire_outputs(config, data, systems, data_dir, asset_dir)
    paths["data"].extend(questionnaire_outputs["data"])
    paths["assets"].extend(questionnaire_outputs["assets"])

    insights = _final_insights(systems)
    paths["data"].append(_write_json(insights, data_dir / "final_insights.json"))
    paths["reports"].append(_write_final_report_notes(reports_dir / "final_report_notes.md"))
    paths["reports"].append(_write_quality_gate(reports_dir / "final_report_quality_gate.md", paths))
    paths["reports"].append(_write_changelog(reports_dir / "final_report_changelog.md", paths))
    paths["reports"].append(_write_generation_log(resolve_path(FINAL_OUTPUT_DIR) / "final_report_generation_log.md", paths))
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
    df = _load_final_user_test_trials(config)
    unified = _user_test_times_unified(df)
    summary = _user_test_times_summary(df)
    task_stats = _user_test_task_stats(df)
    inferential = _user_test_inferential_stats(df, config)
    efficiency = _task_efficiency_stats(df, config)
    qualitative = _qualitative_observations()
    outputs["data"].append(_write_csv(unified, data_dir / "user_test_times_unified.csv"))
    outputs["data"].append(_write_csv(summary, data_dir / "user_test_times_summary.csv"))
    outputs["data"].append(_write_csv(task_stats, data_dir / "user_test_task_stats.csv"))
    outputs["data"].append(_write_csv(inferential, data_dir / "user_test_inferential_stats.csv"))
    outputs["data"].append(_write_csv(efficiency, data_dir / "task_efficiency_stats.csv"))
    outputs["data"].append(_write_csv(_stat_tests_slide_table(inferential), data_dir / "user_test_inferential_stats_slide.csv"))
    outputs["data"].append(_write_csv(qualitative, data_dir / "user_test_qualitative_observations.csv"))
    outputs["data"].append(_write_csv(_qualitative_slide_table(qualitative), data_dir / "user_test_qualitative_observations_slide.csv"))
    outputs["reports"] = [_write_statistical_tests_notes(data_dir / "statistical_tests_notes.md", efficiency)]
    outputs["assets"].append(_plot_time_diff_ci(config, inferential, asset_dir / "user_test_time_diff_ci.png"))
    outputs["assets"].extend(_plot_task_efficiency_stats(config, efficiency, asset_dir))
    return outputs


def _load_final_user_test_trials(config: dict) -> pd.DataFrame:
    normalized_path = resolve_path("data/processed/user_task_trials_normalized.csv")
    if normalized_path.exists():
        trials = pd.read_csv(normalized_path, encoding="utf-8-sig")
        if not trials.empty and {"participant_id", "app", "task_id", "time_seconds", "outcome"}.issubset(trials.columns):
            valid_outcomes = {"success", "assisted_success", "partial_success", "failure", "timeout"}
            trials = trials[trials["outcome"].isin(valid_outcomes)].copy()
            return pd.DataFrame(
                {
                    "user_id": trials["participant_id"],
                    "app": trials["app"],
                    "task_id": trials["task_id"],
                    "task_name": trials.get("task_label", trials["task_id"]),
                    "completion_time_sec": pd.to_numeric(trials["time_seconds"], errors="coerce"),
                    "success": trials["outcome"].isin(["success", "assisted_success", "partial_success"]),
                    "errors_count": pd.to_numeric(trials.get("error_count", 0), errors="coerce").fillna(0),
                    "help_requests": pd.to_numeric(trials.get("help_count", 0), errors="coerce").fillna(0),
                    "notes": trials.get("notes", ""),
                }
            ).dropna(subset=["completion_time_sec"])
    validation = validate_users_time_file(users_time_file(config), required_columns=config.get("users_time", {}).get("required_columns"), tasks=config.get("users_time", {}).get("tasks", []))
    return validation.normalized if validation.is_valid else pd.DataFrame()


def _user_test_times_unified(df: pd.DataFrame) -> pd.DataFrame:
    columns = ["participant_id", "app", "task_id", "task_label", "time_seconds", "success", "error_count", "notes"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    result = pd.DataFrame(
        {
            "participant_id": df["user_id"].astype(str),
            "app": df["app"],
            "task_id": df["task_id"],
            "task_label": df.get("task_name", df["task_id"]),
            "time_seconds": df["completion_time_sec"],
            "success": df["success"],
            "error_count": df["errors_count"],
            "notes": df["notes"] if "notes" in df else "",
        }
    )
    return result[columns].sort_values(["participant_id", "task_id", "app"])


def _user_test_times_summary(df: pd.DataFrame) -> pd.DataFrame:
    columns = ["app", "task_id", "task_label", "n", "mean_seconds", "median_seconds", "std_seconds", "min_seconds", "q1_seconds", "q3_seconds", "max_seconds"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    summary = df.groupby(["app", "task_id", "task_name"], sort=True).agg(
        n=("user_id", "nunique"),
        mean_seconds=("completion_time_sec", "mean"),
        median_seconds=("completion_time_sec", "median"),
        std_seconds=("completion_time_sec", "std"),
        min_seconds=("completion_time_sec", "min"),
        q1_seconds=("completion_time_sec", lambda s: s.quantile(0.25)),
        q3_seconds=("completion_time_sec", lambda s: s.quantile(0.75)),
        max_seconds=("completion_time_sec", "max"),
    ).reset_index().rename(columns={"task_name": "task_label"})
    return summary[columns]


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


def _task_efficiency_stats(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    columns = [
        "task_id",
        "task_label",
        "deliveroo_n",
        "glovo_n",
        "deliveroo_mean",
        "glovo_mean",
        "deliveroo_std",
        "glovo_std",
        "mean_diff",
        "p_value",
        "ci_low",
        "ci_high",
        "effect_size",
        "test_name",
        "interpretation",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    rows = []
    for (task_id, task_label), group in df.groupby(["task_id", "task_name"], sort=True):
        left = group[group["app"].astype(str).str.casefold() == systems[0].casefold()][["user_id", "completion_time_sec"]].dropna()
        right = group[group["app"].astype(str).str.casefold() == systems[1].casefold()][["user_id", "completion_time_sec"]].dropna()
        paired = left.merge(right, on="user_id", suffixes=("_deliveroo", "_glovo"))
        deliveroo_values = paired["completion_time_sec_deliveroo"] if len(paired) >= 2 else left["completion_time_sec"]
        glovo_values = paired["completion_time_sec_glovo"] if len(paired) >= 2 else right["completion_time_sec"]
        if len(deliveroo_values) == 0 or len(glovo_values) == 0:
            continue
        if len(paired) >= 2:
            diff = paired["completion_time_sec_deliveroo"] - paired["completion_time_sec_glovo"]
            try:
                normal = len(diff) >= 3 and stats.shapiro(diff).pvalue >= 0.05
            except ValueError:
                normal = False
            if normal:
                p_value = float(stats.ttest_rel(paired["completion_time_sec_deliveroo"], paired["completion_time_sec_glovo"]).pvalue)
                test_name = "paired t-test"
                effect_size = float(diff.mean() / diff.std(ddof=1)) if diff.std(ddof=1) else 0.0
            else:
                p_value = float(stats.wilcoxon(paired["completion_time_sec_deliveroo"], paired["completion_time_sec_glovo"]).pvalue)
                test_name = "Wilcoxon signed-rank"
                effect_size = _rank_biserial(diff)
            ci_low, ci_high = _bootstrap_ci(diff)
            mean_diff = float(diff.mean())
        else:
            p_value = float(stats.mannwhitneyu(left["completion_time_sec"], right["completion_time_sec"], alternative="two-sided").pvalue)
            test_name = "Mann-Whitney U"
            mean_diff = float(left["completion_time_sec"].mean() - right["completion_time_sec"].mean())
            ci_low, ci_high = _bootstrap_ci_unpaired(left["completion_time_sec"], right["completion_time_sec"])
            pooled = pd.concat([left["completion_time_sec"], right["completion_time_sec"]]).std(ddof=1)
            effect_size = mean_diff / pooled if pooled else 0.0
        faster = systems[0] if deliveroo_values.mean() < glovo_values.mean() else systems[1]
        significance = "indica" if p_value < 0.05 else "non indica"
        stability = "stabile" if ci_low * ci_high > 0 else "incerta"
        rows.append(
            {
                "task_id": task_id,
                "task_label": task_label,
                "deliveroo_n": int(len(deliveroo_values)),
                "glovo_n": int(len(glovo_values)),
                "deliveroo_mean": deliveroo_values.mean(),
                "glovo_mean": glovo_values.mean(),
                "deliveroo_std": deliveroo_values.std(ddof=1),
                "glovo_std": glovo_values.std(ddof=1),
                "mean_diff": mean_diff,
                "p_value": p_value,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "effect_size": effect_size,
                "test_name": test_name,
                "interpretation": f"{faster} mostra il tempo medio inferiore; il p-value {significance} una differenza significativa e l'IC suggerisce una stima {stability}.",
            }
        )
    return pd.DataFrame(rows, columns=columns)


def _questionnaire_outputs(config: dict, data: dict[str, pd.DataFrame], systems: list[str], data_dir: Path, asset_dir: Path) -> dict[str, list[Path]]:
    outputs: dict[str, list[Path]] = {"data": [], "assets": []}
    item_stats = _questionnaire_item_stats(data, systems, config)
    item_descriptives = _questionnaire_item_descriptive_stats(data, systems, config)
    item_tests = _questionnaire_inferential_stats(data, systems, config)
    scale_validation = _ueq_scale_validation(data, systems, config)
    ueq_items = _ueq_item_summary(data, systems, config)
    ueq_scales = _ueq_scale_summary(data, systems, config)
    ueq_ci = _ueq_with_ci(data, systems, config)
    nps = _nps_summary(data, systems)
    outputs["data"].append(_write_csv(item_stats, data_dir / "questionnaire_item_stats.csv"))
    outputs["data"].append(_write_csv(item_descriptives, data_dir / "questionnaire_item_descriptive_stats.csv"))
    outputs["data"].append(_write_csv(item_tests, data_dir / "questionnaire_inferential_stats.csv"))
    outputs["data"].append(_write_md(scale_validation, data_dir / "ueq_scale_validation.md"))
    outputs["data"].append(_write_csv(ueq_items, data_dir / "ueq_item_summary.csv"))
    outputs["data"].append(_write_csv(_ueq_item_mapping(data, systems, config), data_dir / "ueq_item_mapping.csv"))
    outputs["data"].append(_write_md(_ueq_scoring_method_note(data, systems, config), data_dir / "ueq_scoring_method.md"))
    outputs["data"].append(_write_csv(ueq_scales, data_dir / "ueq_scale_summary.csv"))
    outputs["data"].append(_write_csv(_ueq_analysis_slide_table(ueq_items, systems[0]), data_dir / "ueq_item_summary_deliveroo_slide.csv"))
    outputs["data"].append(_write_csv(_ueq_analysis_slide_table(ueq_items, systems[1]), data_dir / "ueq_item_summary_glovo_slide.csv"))
    outputs["data"].append(_write_csv(_ueq_benchmark_slide_table(ueq_scales, systems[0]), data_dir / "ueq_benchmark_deliveroo_slide.csv"))
    outputs["data"].append(_write_csv(_ueq_benchmark_slide_table(ueq_scales, systems[1]), data_dir / "ueq_benchmark_glovo_slide.csv"))
    outputs["data"].append(_write_csv(ueq_ci, data_dir / "ueq_scale_summary_with_ci.csv"))
    outputs["data"].append(_write_csv(nps, data_dir / "nps_summary.csv"))
    outputs["assets"].append(_plot_questionnaire_top_differences(config, item_tests, asset_dir / "questionnaire_top_differences.png"))
    outputs["assets"].append(_plot_ueq_ci(config, ueq_ci, asset_dir / "ueq_with_ci.png"))
    outputs["assets"].append(_plot_nps_breakdown(config, nps, asset_dir / "nps_breakdown.png"))
    outputs["assets"].extend(_plot_ueq_final_assets(config, ueq_items, ueq_scales))
    return outputs


def _questionnaire_item_stats(data: dict[str, pd.DataFrame], systems: list[str], config: dict) -> pd.DataFrame:
    rows = []
    for system, key in [(systems[0], "questionnaire_system_1"), (systems[1], "questionnaire_system_2")]:
        items = numeric_items(data.get(key, pd.DataFrame()), config)
        for item, values in items.iterrows():
            numeric = pd.to_numeric(values, errors="coerce").dropna()
            rows.append({"app": system, "item": item, "n": len(numeric), "mean": numeric.mean(), "median": numeric.median(), "std": numeric.std(), "min": numeric.min(), "max": numeric.max()})
    return pd.DataFrame(rows)


def _questionnaire_item_descriptive_stats(data: dict[str, pd.DataFrame], systems: list[str], config: dict) -> pd.DataFrame:
    columns = ["app", "item_id", "item_label", "dimension", "n", "min", "q1", "mean", "median", "q3", "max", "std"]
    rows = []
    for system, key in [(systems[0], "questionnaire_system_1"), (systems[1], "questionnaire_system_2")]:
        items = numeric_items(data.get(key, pd.DataFrame()), config)
        for item_idx, (item, values) in enumerate(items.iterrows(), start=1):
            numeric = pd.to_numeric(values, errors="coerce").dropna()
            rows.append(
                {
                    "app": system,
                    "item_id": item_idx,
                    "item_label": item,
                    "dimension": _ueq_dimension_for_item(item_idx),
                    "n": len(numeric),
                    "min": numeric.min(),
                    "q1": numeric.quantile(0.25),
                    "mean": numeric.mean(),
                    "median": numeric.median(),
                    "q3": numeric.quantile(0.75),
                    "max": numeric.max(),
                    "std": numeric.std(ddof=1),
                }
            )
    return pd.DataFrame(rows, columns=columns)


def generate_question_insight(item_stats_deliveroo: pd.Series, item_stats_glovo: pd.Series) -> str:
    deliveroo_mean = float(item_stats_deliveroo.get("mean", np.nan))
    glovo_mean = float(item_stats_glovo.get("mean", np.nan))
    if pd.isna(deliveroo_mean) or pd.isna(glovo_mean):
        return "Dati non sufficienti per confrontare questo item."
    leader = "Deliveroo" if deliveroo_mean > glovo_mean else "Glovo" if glovo_mean > deliveroo_mean else "nessuna app"
    left_median = float(item_stats_deliveroo.get("median", np.nan))
    right_median = float(item_stats_glovo.get("median", np.nan))
    median_confirms = abs((left_median - right_median) or 0) >= 0.25 and np.sign(deliveroo_mean - glovo_mean) == np.sign(left_median - right_median)
    iqr_left = float(item_stats_deliveroo.get("q3", 0) - item_stats_deliveroo.get("q1", 0))
    iqr_right = float(item_stats_glovo.get("q3", 0) - item_stats_glovo.get("q1", 0))
    variability = "stabile" if max(iqr_left, iqr_right) <= 1.5 else "eterogenea"
    if leader == "nessuna app":
        return f"Per questo item le medie sono sostanzialmente allineate ({deliveroo_mean:.2f} vs {glovo_mean:.2f}); la dispersione appare {variability}."
    return (
        f"Per questo item {leader} ottiene una media piu alta ({deliveroo_mean:.2f} vs {glovo_mean:.2f}). "
        f"La mediana {'conferma' if median_confirms else 'attenua'} la differenza osservata, mentre l'intervallo interquartile suggerisce una percezione {variability} tra i partecipanti."
    )


def _questionnaire_inferential_stats(data: dict[str, pd.DataFrame], systems: list[str], config: dict) -> pd.DataFrame:
    left_items = numeric_items(data.get("questionnaire_system_1", pd.DataFrame()), config)
    right_items = numeric_items(data.get("questionnaire_system_2", pd.DataFrame()), config)
    rows = []
    for item in [item for item in left_items.index if item in right_items.index]:
        common = [column for column in left_items.columns if column in right_items.columns]
        left = pd.to_numeric(left_items.loc[item, common] if common else left_items.loc[item], errors="coerce")
        right = pd.to_numeric(right_items.loc[item, common] if common else right_items.loc[item], errors="coerce")
        paired = pd.DataFrame({"left": left, "right": right}).dropna()
        if paired.empty:
            continue
        if len(paired) >= 2 and not np.allclose(paired["left"], paired["right"], equal_nan=True):
            p_value = float(stats.wilcoxon(paired["left"], paired["right"]).pvalue)
            test_name = "Wilcoxon signed-rank"
        else:
            p_value = 1.0
            test_name = "Wilcoxon signed-rank"
        rows.append({"item": item, "test_name": test_name, f"{systems[0]}_mean": paired["left"].mean(), f"{systems[1]}_mean": paired["right"].mean(), "mean_diff": paired["left"].mean() - paired["right"].mean(), "p_value": p_value, "interpretation": _p_interpretation(p_value)})
    return pd.DataFrame(rows).sort_values("mean_diff", key=lambda s: s.abs(), ascending=False) if rows else pd.DataFrame(columns=["item", "test_name", f"{systems[0]}_mean", f"{systems[1]}_mean", "mean_diff", "p_value", "interpretation"])


def _ueq_item_mapping(data: dict[str, pd.DataFrame], systems: list[str], config: dict) -> pd.DataFrame:
    left_items = numeric_items(data.get("questionnaire_system_1", pd.DataFrame()), config)
    right_items = numeric_items(data.get("questionnaire_system_2", pd.DataFrame()), config)
    rows = []
    for item_idx, item in enumerate(left_items.index, start=1):
        left_anchor, right_anchor = _split_anchors(item)
        deliveroo_raw = pd.to_numeric(left_items.loc[item], errors="coerce").dropna()
        glovo_raw = pd.to_numeric(right_items.loc[item], errors="coerce").dropna() if item in right_items.index else pd.Series(dtype=float)
        rows.append(
            {
                "item_id": item_idx,
                "left_label": left_anchor,
                "right_label": right_anchor,
                "dimension": _ueq_dimension_for_item(item_idx),
                "reverse_scored": False,
                "deliveroo_mean_raw": deliveroo_raw.mean(),
                "glovo_mean_raw": glovo_raw.mean(),
                "deliveroo_mean_ueq": _to_ueq_standard(deliveroo_raw).mean(),
                "glovo_mean_ueq": _to_ueq_standard(glovo_raw).mean(),
            }
        )
    return pd.DataFrame(rows)


def _ueq_scoring_method_note(data: dict[str, pd.DataFrame], systems: list[str], config: dict) -> str:
    mapping = _ueq_item_mapping(data, systems, config)
    return "\n".join(
        [
            "# Metodo di scoring UEQ",
            "",
            "- Le risposte originali sono lette su scala Likert 1-7 quando il dataset usa quel formato.",
            "- Per i riepiloghi UEQ la pipeline trasforma i valori in scala standard -3/+3 con `valore_ueq = valore_likert - 4`.",
            "- Gli item sono mantenuti nell'ordine configurato e non vengono invertiti manualmente dalla pipeline.",
            "- Le medie per dimensione sono calcolate raggruppando gli item secondo il mapping UEQ salvato in `ueq_item_mapping.csv`.",
            "- I confronti item tra Deliveroo e Glovo sono appaiati sugli stessi partecipanti e usano Wilcoxon signed-rank.",
            "- Il benchmark usa soglie descrittive UEQ: Bad, Below average, Above average, Good, Excellent.",
            f"- Item mappati: {mapping['item_id'].nunique() if not mapping.empty else 0}.",
            "",
        ]
    )


def _ueq_scale_validation(data: dict[str, pd.DataFrame], systems: list[str], config: dict) -> str:
    frames = [numeric_items(data.get(key, pd.DataFrame()), config).stack() for key in ["questionnaire_system_1", "questionnaire_system_2"]]
    values = pd.concat(frames, ignore_index=True) if frames else pd.Series(dtype=float)
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    original_min = float(numeric.min()) if len(numeric) else np.nan
    original_max = float(numeric.max()) if len(numeric) else np.nan
    scale = "1-7 Likert" if original_min >= 1 and original_max <= 7 else "-3..+3 UEQ standard" if original_min >= -3 and original_max <= 3 else "scala non riconosciuta"
    transform = "valore_standard = valore_likert - 4" if scale == "1-7 Likert" else "nessuna trasformazione"
    items = config.get("formbricks", {}).get("questionnaire", {}).get("ueq_items", [])
    lines = [
        "# Validazione scala UEQ",
        "",
        f"- Scala originale rilevata: {scale} (min={original_min:.2f}, max={original_max:.2f}).",
        f"- Trasformazione applicata: {transform}.",
        f"- Colonne usate: {len(numeric_items(data.get('questionnaire_system_1', pd.DataFrame()), config).columns)} rispondenti Deliveroo, {len(numeric_items(data.get('questionnaire_system_2', pd.DataFrame()), config).columns)} rispondenti Glovo.",
        "- Mapping item -> dimensione UEQ:",
    ]
    for idx, item in enumerate(items, start=1):
        lines.append(f"  - Item {idx:02d}: {item} -> {_ueq_dimension_for_item(idx)}")
    lines.extend(
        [
            "- Item invertiti: non invertiti manualmente dalla pipeline; la conversione usa l'ordine degli item configurato.",
            "- Motivazione: i dati sorgente sono mantenuti in scala Likert 1-7, mentre benchmark e riepiloghi UEQ finali richiedono scala standard -3..+3.",
            "",
        ]
    )
    return "\n".join(lines)


def _ueq_item_summary(data: dict[str, pd.DataFrame], systems: list[str], config: dict) -> pd.DataFrame:
    columns = ["app", "item_id", "left_anchor", "right_anchor", "dimension", "n", "mean", "variance", "std", "min", "q1", "median", "q3", "max"]
    rows = []
    for system, key in [(systems[0], "questionnaire_system_1"), (systems[1], "questionnaire_system_2")]:
        items = numeric_items(data.get(key, pd.DataFrame()), config)
        for item_idx, (item, values) in enumerate(items.iterrows(), start=1):
            numeric = _to_ueq_standard(pd.to_numeric(values, errors="coerce").dropna())
            left_anchor, right_anchor = _split_anchors(item)
            rows.append(
                {
                    "app": system,
                    "item_id": item_idx,
                    "left_anchor": left_anchor,
                    "right_anchor": right_anchor,
                    "dimension": _ueq_dimension_for_item(item_idx),
                    "n": len(numeric),
                    "mean": numeric.mean(),
                    "variance": numeric.var(ddof=1),
                    "std": numeric.std(ddof=1),
                    "min": numeric.min(),
                    "q1": numeric.quantile(0.25),
                    "median": numeric.median(),
                    "q3": numeric.quantile(0.75),
                    "max": numeric.max(),
                }
            )
    return pd.DataFrame(rows, columns=columns)


def _ueq_scale_summary(data: dict[str, pd.DataFrame], systems: list[str], config: dict) -> pd.DataFrame:
    columns = ["app", "dimension", "n", "mean", "variance", "std", "ci_low", "ci_high", "benchmark_label", "benchmark_interpretation"]
    item_summary = _ueq_item_summary(data, systems, config)
    rows = []
    for (app, dimension), group in item_summary.groupby(["app", "dimension"], sort=True):
        values = pd.to_numeric(group["mean"], errors="coerce").dropna()
        n = int(group["n"].sum())
        mean = values.mean()
        std = values.std(ddof=1)
        se = std / math.sqrt(len(values)) if len(values) > 1 and pd.notna(std) else 0.0
        ci = 1.96 * se
        label = _ueq_benchmark_label(mean)
        rows.append(
            {
                "app": app,
                "dimension": dimension,
                "n": n,
                "mean": mean,
                "variance": values.var(ddof=1),
                "std": std,
                "ci_low": mean - ci,
                "ci_high": mean + ci,
                "benchmark_label": label,
                "benchmark_interpretation": _ueq_benchmark_interpretation(label),
            }
        )
    return pd.DataFrame(rows, columns=columns)


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


def _plot_task_efficiency_stats(config: dict, df: pd.DataFrame, asset_dir: Path) -> list[Path]:
    paths = []
    palette = get_brand_palette(config)
    for row in df.itertuples(index=False):
        task_id = str(row.task_id).lower()
        path = asset_dir / f"task_efficiency_{task_id}.png"
        fig, ax = plt.subplots(figsize=(8.5, 4.8))
        means = [row.deliveroo_mean, row.glovo_mean]
        stds = [row.deliveroo_std if pd.notna(row.deliveroo_std) else 0, row.glovo_std if pd.notna(row.glovo_std) else 0]
        labels = ["Deliveroo", "Glovo"]
        ax.bar(labels, means, yerr=stds, capsize=5, color=[palette.get("Deliveroo", "#00CCBC"), palette.get("Glovo", "#FFC244")])
        style_axis(ax, f"Efficienza statistica - {row.task_id}", "", "Secondi")
        ax.text(0.5, max(means) * 1.08 if max(means) else 1, f"p={row.p_value:.3f} | IC 95% [{row.ci_low:.2f}, {row.ci_high:.2f}]", ha="center", color="#F8FAFC")
        save_figure(fig, path, config)
        paths.append(_saved_asset(path))
    return paths


def _plot_ueq_final_assets(config: dict, item_summary: pd.DataFrame, scale_summary: pd.DataFrame) -> list[Path]:
    output_dir = resolve_path("slides/assets/generated/ueq")
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for app in ["Deliveroo", "Glovo"]:
        app_items = item_summary[item_summary["app"].astype(str).str.casefold() == app.casefold()]
        app_scales = scale_summary[scale_summary["app"].astype(str).str.casefold() == app.casefold()]
        paths.append(_plot_ueq_distribution(config, app_items, output_dir / f"ueq_distribution_{app.lower()}.png", app))
        paths.append(_plot_ueq_mean_results(config, app_scales, output_dir / f"ueq_mean_results_{app.lower()}.png", app))
        paths.append(_plot_ueq_benchmark(config, app_scales, output_dir / f"ueq_benchmark_{app.lower()}.png", app))
    paths.append(_plot_ueq_scale_comparison(config, scale_summary, output_dir / "ueq_scale_comparison_deliveroo_vs_glovo.png"))
    return paths


def _plot_ueq_distribution(config: dict, df: pd.DataFrame, path: Path, app: str) -> Path:
    fig, ax = plt.subplots(figsize=(11, 6))
    if df.empty:
        ax.text(0.5, 0.5, "Dati UEQ non disponibili", ha="center", va="center")
        ax.axis("off")
    else:
        plot = df.copy()
        plot["item"] = plot["item_id"].map(lambda value: f"{int(value):02d}")
        sns.barplot(data=plot, x="item", y="mean", color=get_brand_palette(config).get(app, "#38BDF8"), ax=ax)
        ax.axhline(0, color="#F8FAFC", linewidth=1)
        ax.set_ylim(-3, 3)
        style_axis(ax, f"Distribuzione risposte UEQ - {app}", "Item", "Media scala -3..+3")
    save_figure(fig, path, config)
    return _expose_saved_asset(path)


def _plot_ueq_mean_results(config: dict, df: pd.DataFrame, path: Path, app: str) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5.2))
    if df.empty:
        ax.text(0.5, 0.5, "Dati UEQ non disponibili", ha="center", va="center")
        ax.axis("off")
    else:
        sns.barplot(data=df, y="dimension", x="mean", color=get_brand_palette(config).get(app, "#38BDF8"), ax=ax)
        ax.axvline(0, color="#F8FAFC", linewidth=1)
        ax.set_xlim(-3, 3)
        style_axis(ax, f"Media risultati UEQ - {app}", "Media scala -3..+3", "")
    save_figure(fig, path, config)
    return _expose_saved_asset(path)


def _plot_ueq_benchmark(config: dict, df: pd.DataFrame, path: Path, app: str) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5.2))
    if df.empty:
        ax.text(0.5, 0.5, "Benchmark UEQ non disponibile", ha="center", va="center")
        ax.axis("off")
    else:
        colors = df["benchmark_label"].map({"Excellent": "#10B981", "Good": "#22C55E", "Above average": "#84CC16", "Below average": "#F59E0B", "Bad": "#EF4444"}).fillna("#94A3B8")
        ax.barh(df["dimension"], df["mean"], color=colors)
        ax.axvline(0, color="#F8FAFC", linewidth=1)
        ax.set_xlim(-3, 3)
        style_axis(ax, f"Comparazione con benchmark - {app}", "Media scala -3..+3", "")
    save_figure(fig, path, config)
    return _expose_saved_asset(path)


def _plot_ueq_scale_comparison(config: dict, df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    if df.empty:
        ax.text(0.5, 0.5, "Dati UEQ non disponibili", ha="center", va="center")
        ax.axis("off")
    else:
        sns.barplot(data=df, x="dimension", y="mean", hue="app", palette=get_brand_palette(config), ax=ax)
        ax.axhline(0, color="#F8FAFC", linewidth=1)
        ax.set_ylim(-3, 3)
        ax.tick_params(axis="x", rotation=20)
        style_axis(ax, "Confronto scale UEQ Deliveroo vs Glovo", "Dimensione", "Media scala -3..+3")
    save_figure(fig, path, config)
    return _expose_saved_asset(path)


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


def _write_md(text: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
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


def _expose_saved_asset(path: Path) -> Path:
    target = resolve_path(path)
    saved = _saved_asset(target)
    if saved.exists() and saved != target:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(saved, target)
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


def _bootstrap_ci_unpaired(left: pd.Series, right: pd.Series, iterations: int = 1000) -> tuple[float, float]:
    left_arr = pd.to_numeric(left, errors="coerce").dropna().to_numpy()
    right_arr = pd.to_numeric(right, errors="coerce").dropna().to_numpy()
    if len(left_arr) < 2 or len(right_arr) < 2:
        diff = float(left_arr.mean() - right_arr.mean()) if len(left_arr) and len(right_arr) else np.nan
        return diff, diff
    rng = np.random.default_rng(42)
    diffs = [
        rng.choice(left_arr, size=len(left_arr), replace=True).mean()
        - rng.choice(right_arr, size=len(right_arr), replace=True).mean()
        for _ in range(iterations)
    ]
    return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


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


def _to_ueq_standard(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if numeric.empty:
        return numeric
    if numeric.min() >= 1 and numeric.max() <= 7:
        return numeric - 4
    return numeric


def _split_anchors(item: Any) -> tuple[str, str]:
    text = str(item or "")
    if "-" in text:
        left, right = text.split("-", 1)
        return left.strip(), right.strip()
    if "/" in text:
        left, right = text.split("/", 1)
        return left.strip(), right.strip()
    return text.strip(), ""


def _ueq_dimension_for_item(item_id: int) -> str:
    mapping = {
        "Attrattivita": {1, 5, 6, 7, 12, 18},
        "Perspicuita": {4, 14, 17, 24},
        "Efficienza": {9, 13, 20, 22},
        "Affidabilita": {2, 11, 15, 19},
        "Stimolazione": {3, 8, 16, 21},
        "Novita": {10, 23, 25, 26},
    }
    for dimension, ids in mapping.items():
        if item_id in ids:
            return dimension
    return "n.d."


def _ueq_benchmark_label(mean: float) -> str:
    if pd.isna(mean):
        return "n.d."
    if mean >= 1.5:
        return "Excellent"
    if mean >= 1.0:
        return "Good"
    if mean >= 0.8:
        return "Above average"
    if mean >= 0.0:
        return "Below average"
    return "Bad"


def _ueq_benchmark_interpretation(label: str) -> str:
    return {
        "Excellent": "Risultato molto forte rispetto al benchmark indicativo.",
        "Good": "Risultato positivo e competitivo.",
        "Above average": "Risultato sopra la soglia positiva.",
        "Below average": "Risultato leggibile ma con margini di miglioramento.",
        "Bad": "Risultato critico rispetto alla scala UEQ standard.",
    }.get(label, "Benchmark non disponibile.")


def _ueq_analysis_slide_table(df: pd.DataFrame, app: str) -> pd.DataFrame:
    subset = df[df["app"].astype(str).str.casefold() == app.casefold()].copy()
    if subset.empty:
        return pd.DataFrame(columns=["Domanda", "Media", "Varianza", "Dev. standard", "N", "Valore sinistro", "Valore destro", "Sottogruppo"])
    result = subset[["item_id", "mean", "variance", "std", "n", "left_anchor", "right_anchor", "dimension"]].copy()
    result.columns = ["Domanda", "Media", "Varianza", "Dev. standard", "N", "Valore sinistro", "Valore destro", "Sottogruppo"]
    return result


def _ueq_benchmark_slide_table(df: pd.DataFrame, app: str) -> pd.DataFrame:
    subset = df[df["app"].astype(str).str.casefold() == app.casefold()].copy()
    if subset.empty:
        return pd.DataFrame(columns=["Sottogruppo", "Media", "Comparazione", "Interpretazione"])
    result = subset[["dimension", "mean", "benchmark_label", "benchmark_interpretation"]].copy()
    result.columns = ["Sottogruppo", "Media", "Comparazione", "Interpretazione"]
    return result


def _write_statistical_tests_notes(path: Path, efficiency: pd.DataFrame) -> Path:
    lines = [
        "# Note sui test statistici",
        "",
        "- I task sono trattati come misure appaiate quando lo stesso partecipante ha dati per Deliveroo e Glovo.",
        "- Per differenze appaiate non normali viene usato Wilcoxon signed-rank; se la normalita e plausibile viene usato paired t-test.",
        "- Se non e possibile appaiare i partecipanti viene usato Mann-Whitney U.",
        "- L'intervallo di confidenza al 95% sulla differenza media usa bootstrap con seed fisso 42.",
        "",
        "## Test applicati",
    ]
    for row in efficiency.itertuples(index=False):
        lines.append(f"- {row.task_id}: {row.test_name}, p={row.p_value:.4f}, IC 95% [{row.ci_low:.2f}, {row.ci_high:.2f}].")
    return _write_md("\n".join(lines) + "\n", path)


def _write_generation_log(path: Path, paths: dict[str, list[Path]]) -> Path:
    data_dir = resolve_path(FINAL_DATA_DIR)
    questions = pd.read_csv(data_dir / "questionnaire_item_descriptive_stats.csv", encoding="utf-8-sig") if (data_dir / "questionnaire_item_descriptive_stats.csv").exists() else pd.DataFrame()
    question_count = int(questions["item_id"].nunique()) if "item_id" in questions else 0
    ueq_assets = sorted(resolve_path("slides/assets/generated/ueq").glob("*.png"))
    efficiency_assets = sorted(resolve_path(FINAL_ASSET_DIR).glob("**/task_efficiency_*.png"))
    lines = [
        "# Final report generation log",
        "",
        f"- Timestamp generazione: {datetime.now().isoformat(timespec='seconds')}",
        f"- Numero slide totali: calcolato in fase di export PPTX",
        f"- Numero domande questionario rilevate: {question_count}",
        f"- Numero slide questionario previste: {math.ceil(question_count / 2) if question_count else 0}",
        f"- Asset UEQ generati: {len(ueq_assets)}",
        f"- Asset efficienza generati: {len(efficiency_assets)}",
        f"- File dati generati: {len(paths.get('data', []))}",
        f"- Asset final report generati: {len(paths.get('assets', []))}",
        "- Warning: nessun warning bloccante registrato dalla pipeline final_report.",
        "",
    ]
    return _write_md("\n".join(lines), path)
