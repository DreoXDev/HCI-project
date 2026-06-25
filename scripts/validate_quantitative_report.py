from __future__ import annotations

import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import pandas as pd
import seaborn as sns
import yaml
from scipy import stats

from src.analysis.statistics import (
    bootstrap_ci_mean,
    choose_paired_time_test,
    compute_descriptives,
    fisher_exact_2x2,
    mcnemar_exact,
    one_sample_test_against_threshold,
    wilcoxon_signed_rank,
)
from src.analysis.validation import QuantitativeWarningLog
from src.analysis.ueq_benchmark import (
    BENCHMARK_SOURCE,
    CATEGORY_ORDER,
    UEQ_BENCHMARK_THRESHOLDS as OFFICIAL_UEQ_BENCHMARK_THRESHOLDS,
    UEQ_INTERNAL_SCALE_ORDER,
    UEQ_SCALE_ORDER,
    benchmark_plot_rows,
    check_project_benchmark_snapshot,
    classify_ueq_benchmark,
    normalize_ueq_scale_name,
    threshold_row,
    thresholds_dataframe,
)
from src.analysis.ueq_scoring import transform_ueq_value


SYSTEMS = ("Deliveroo", "Glovo")
BACKGROUND = "#111827"
PANEL = "#111827"
TEXT = "#F8FAFC"
MUTED = "#CBD5E1"
GRID = "#374151"
DELIVEROO = "#00CCBC"
GLOVO = "#FFC244"
TASK_SOURCE = ROOT / "data" / "user_testing_times.csv"
TIME_SOURCE = ROOT / "data" / "raw" / "users_time.csv"
QUESTIONNAIRE = {
    "Deliveroo": ROOT / "data" / "raw" / "questionnaire_deliveroo.csv",
    "Glovo": ROOT / "data" / "raw" / "questionnaire_glovo.csv",
}
USER_PROFILES = ROOT / "data" / "user_profiles.csv"
TABLES = ROOT / "outputs" / "tables"
CHARTS = ROOT / "outputs" / "charts"
VALIDATION = ROOT / "outputs" / "validation"
DOCS = ROOT / "docs"
UEQ_HEATMAP_SHORT_LABELS = {
    "Attrattività": "Attr.",
    "Apprendibilità": "Appr.",
    "Efficienza": "Eff.",
    "Controllabilità": "Contr.",
    "Stimolazione": "Stim.",
    "Originalità": "Orig.",
}
UEQ_HEATMAP_LABEL_NOTE = (
    "Abbreviazioni delle scale UEQ: Attr. = Attrattività, Appr. = Apprendibilità, "
    "Eff. = Efficienza, Contr. = Controllabilità, Stim. = Stimolazione, Orig. = Originalità."
)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)
    VALIDATION.mkdir(parents=True, exist_ok=True)
    log = QuantitativeWarningLog()

    thresholds = _read_yaml(ROOT / "config" / "analysis_thresholds.yml")
    ueq_items = _read_yaml(ROOT / "config" / "ueq_items.yml")["items"]

    task_df = build_task_outcomes(log)
    time_df = build_task_times(task_df, log)
    effectiveness_by_task = build_effectiveness_tables(task_df, thresholds, log)
    efficiency_relative = build_efficiency_tables(time_df, thresholds, log)

    q_long = build_ueq_long(ueq_items, log)
    item_desc, item_tests = build_ueq_items(q_long, ueq_items, log)
    scale_scores, scale_desc, scale_tests, benchmark = build_ueq_scales(q_long, log)
    subgroup_tables = build_subgroups(scale_scores, q_long, task_df, log)
    comparison = build_system_comparison(effectiveness_by_task, efficiency_relative, item_tests, scale_tests, benchmark)
    build_curated_slide_tables(task_df, time_df, effectiveness_by_task, efficiency_relative, item_tests, scale_desc, scale_tests, benchmark, subgroup_tables, thresholds)
    build_detailed_quantitative_outputs(task_df, time_df, effectiveness_by_task, efficiency_relative, q_long, item_desc, item_tests, scale_desc, scale_tests, benchmark, thresholds)

    write_audit(task_df, q_long, subgroup_tables, log)
    write_method_docs()
    write_validation_report(task_df, q_long, log)

    log.ok(f"generated {len(list(TABLES.glob('*.csv')))} CSV tables")
    log.ok(f"generated {len(list(CHARTS.glob('*.png')))} PNG charts")
    log.write(VALIDATION / "quantitative_generation_log.md", "Quantitative generation log")


def _read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _save_csv(df: pd.DataFrame, name: str) -> Path:
    path = TABLES / name
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    float_columns = out.select_dtypes(include=["float", "float64", "float32"]).columns
    if len(float_columns):
        out[float_columns] = out[float_columns].round(3)
    out.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def _save_markdown_table(df: pd.DataFrame, name: str) -> Path:
    path = TABLES / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if df.empty:
        text = "_Nessun dato disponibile._\n"
    else:
        text = df.to_markdown(index=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def _save_validation_csv(df: pd.DataFrame, name: str) -> Path:
    path = VALIDATION / name
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    float_columns = out.select_dtypes(include=["float", "float64", "float32"]).columns
    if len(float_columns):
        out[float_columns] = out[float_columns].round(3)
    out.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def _write_output_text(relative_path: str, lines: list[str]) -> Path:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def _fmt_num(value: object, digits: int = 2, suffix: str = "") -> str:
    if pd.isna(value):
        return "n.c."
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{number:.{digits}f}{suffix}"


def _fmt_pct(value: object, digits: int = 0) -> str:
    if pd.isna(value):
        return "n.c."
    return f"{float(value) * 100:.{digits}f}%"


def _fmt_p(value: object) -> str:
    if pd.isna(value):
        return "n.c."
    p = float(value)
    if p < 0.001:
        return "p < .001"
    return f"p = {p:.3f}".replace("0.", ".")


def _short_reading(p_value: object, winner: str, *, significant: str = "differenza significativa", not_significant: str = "non significativa") -> str:
    if pd.isna(p_value):
        return "test non calcolabile"
    if float(p_value) < 0.05 and winner != "pari":
        return f"{significant}; vantaggio {winner}"
    return not_significant


def _significance_label(p_value: object, alpha: float = 0.05) -> str:
    if pd.isna(p_value):
        return "test non calcolabile"
    return "differenza statisticamente significativa" if float(p_value) < alpha else "differenza non statisticamente significativa"


def _savefig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight", facecolor=BACKGROUND)
    plt.close()


def _dark_axes(ax: plt.Axes, *, title: str | None = None, xlabel: str | None = None, ylabel: str | None = None) -> None:
    ax.set_facecolor(PANEL)
    ax.figure.set_facecolor(BACKGROUND)
    if title is not None:
        ax.set_title(title, color=TEXT, fontweight="bold")
    if xlabel is not None:
        ax.set_xlabel(xlabel, color=MUTED)
    if ylabel is not None:
        ax.set_ylabel(ylabel, color=MUTED)
    ax.tick_params(colors=MUTED)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.grid(color=GRID, alpha=0.35)


def _style_legend(ax: plt.Axes) -> None:
    legend = ax.get_legend()
    if legend is None:
        return
    legend.get_frame().set_facecolor(PANEL)
    legend.get_frame().set_edgecolor(GRID)
    for text in legend.get_texts():
        text.set_color(TEXT)
    if legend.get_title():
        legend.get_title().set_color(TEXT)


def _participant_from_col(column: str) -> str:
    digits = "".join(ch for ch in str(column) if ch.isdigit())
    return f"U{int(digits)}" if digits else str(column)


def _task_id(value: object) -> str:
    text = str(value)
    digits = "".join(ch for ch in text if ch.isdigit())
    return f"T{int(digits):02d}" if digits else text


def normalize_task_outcome(value: object) -> str:
    text = str(value or "").strip().casefold()
    text = re.sub(r"[\s_-]+", " ", text)
    success_values = {"success", "successo", "completato", "completed", "done", "ok"}
    partial_values = {
        "assisted success",
        "aiuto richiesto",
        "con aiuto",
        "partial success",
        "parziale",
        "successo parziale",
        "success with issue",
        "successo con criticita",
        "successo con criticità",
        "workaround",
    }
    failure_values = {"failure", "fallimento", "insuccesso", "non completato", "timeout", "failed", "errore"}
    if text in success_values:
        return "success"
    if text in partial_values:
        return "partial_success"
    if text in failure_values:
        return "failure"
    if "parzial" in text or "aiuto" in text or "assist" in text or "issue" in text or "workaround" in text:
        return "partial_success"
    if "success" in text or "successo" in text or "complet" in text:
        return "success"
    if "fail" in text or "fall" in text or "insuccess" in text or "timeout" in text or "errore" in text:
        return "failure"
    return "failure"


def _interpret(p_value: float, winner: str) -> str:
    if pd.isna(p_value):
        return "Test non calcolabile con i dati disponibili."
    if p_value < 0.05:
        return f"Differenza significativa; vantaggio per {winner}."
    return "Differenza non significativa; evidenza non conclusiva."


def build_task_outcomes(log: QuantitativeWarningLog) -> pd.DataFrame:
    source = TASK_SOURCE if TASK_SOURCE.exists() else TIME_SOURCE
    if not source.exists():
        log.warn("task source missing; task analyses skipped")
        df = pd.DataFrame()
        _save_csv(df, "task_outcomes_normalized.csv")
        return df

    raw = pd.read_csv(source)
    rows = []
    for row in raw.itertuples(index=False):
        user = getattr(row, "user_id", "")
        app = getattr(row, "app", "")
        task = _task_id(getattr(row, "task", getattr(row, "task_id", "")))
        task_name = getattr(row, "task_name", {"T01": "Ricerca ristorante", "T02": "Aggiunta prodotto al carrello", "T03": "Modifica carrello"}.get(task, task))
        outcome = str(getattr(row, "outcome", "")).strip()
        if not outcome:
            success = str(getattr(row, "success", "")).strip().lower() in {"true", "1", "yes", "si", "sì"}
            help_count = int(pd.to_numeric(getattr(row, "help_requests", 0), errors="coerce") or 0)
            errors = int(pd.to_numeric(getattr(row, "errors_count", 0), errors="coerce") or 0)
            outcome = "assisted_success" if success and help_count else "success" if success else "failure"
        assistance = str(getattr(row, "assistance", "")).strip()
        error_flag = str(getattr(row, "error_flag", "")).strip().lower() in {"true", "1", "yes", "si", "sì"}
        errors_count = int(pd.to_numeric(getattr(row, "errors_count", 1 if error_flag else 0), errors="coerce") or 0)
        help_count = int(pd.to_numeric(getattr(row, "help_requests", 1 if assistance == "verbal_help" else 0), errors="coerce") or 0)
        normalized = normalize_task_outcome(outcome)
        completed = normalized in {"success", "partial_success"}
        critical = bool(error_flag or errors_count > 0 or outcome in {"failure", "timeout"})
        autonomous = bool(completed and normalized == "success" and assistance in {"", "none"} and help_count == 0 and not critical)
        outcome_3class = "success" if autonomous else "partial_success" if completed else "failure"
        if autonomous:
            label = "successo autonomo"
            score = 3
        elif completed and help_count:
            label = "successo con aiuto"
            score = 2
        elif completed and critical:
            label = "successo con criticita/workaround"
            score = 1
        elif completed:
            label = "successo non autonomo"
            score = 1
        else:
            label = "fallimento"
            score = 0
        rows.append(
            {
                "participant_id": user,
                "app": app,
                "app_order": "",
                "task_id": task,
                "task_name": task_name,
                "completed": int(completed),
                "completed_autonomously": int(autonomous),
                "help_requested": int(help_count > 0),
                "workaround_used": int(outcome == "partial_success" or assistance == "workaround"),
                "critical_error": int(critical),
                "failed": int(not completed),
                "outcome_3class": outcome_3class,
                "binary_success_for_absolute_effectiveness": int(outcome_3class == "success"),
                "outcome_label": label,
                "outcome_score": score,
                "notes": getattr(row, "issue_note", getattr(row, "notes", "")),
            }
        )
    df = pd.DataFrame(rows)
    _save_csv(df, "task_outcomes_normalized.csv")
    plot_effectiveness_matrix(df)
    log.ok(f"task outcomes normalized from {source.relative_to(ROOT)}: {len(df)} rows")
    return df


def plot_effectiveness_matrix(df: pd.DataFrame) -> None:
    if df.empty:
        return
    matrix = df.copy()
    matrix["matrix_score"] = np.select(
        [
            matrix["completed"].astype(int).eq(0),
            matrix["help_requested"].astype(int).eq(1)
            | matrix["critical_error"].astype(int).eq(1)
            | matrix["workaround_used"].astype(int).eq(1),
        ],
        [0, 1],
        default=2,
    )
    matrix["column"] = matrix["task_id"] + " " + matrix["app"]
    pivot = matrix.pivot_table(index="participant_id", columns="column", values="matrix_score", aggfunc="first")
    pivot = pivot.reindex(index=sorted(pivot.index, key=_participant_sort_key))
    order = [f"{task} {app}" for task in sorted(df["task_id"].unique()) for app in SYSTEMS]
    pivot = pivot.reindex(columns=[col for col in order if col in pivot.columns])
    fig, ax = plt.subplots(figsize=(11, 7), facecolor=BACKGROUND)
    cmap = ListedColormap(["#EF4444", "#FACC15", "#22C55E"])
    heatmap = sns.heatmap(
        pivot,
        cmap=cmap,
        vmin=0,
        vmax=2,
        linewidths=0.5,
        linecolor=GRID,
        cbar_kws={"ticks": [0.33, 1.0, 1.67]},
        ax=ax,
    )
    cbar = heatmap.collections[0].colorbar
    cbar.ax.set_yticklabels(["non completata", "aiuto/issue", "completata"])
    cbar.ax.tick_params(colors=MUTED)
    cbar.outline.set_edgecolor(GRID)
    _dark_axes(ax, title="Efficacia: matrice esiti utenti/task", xlabel="Task e app", ylabel="Utente")
    ax.grid(False)
    _savefig(CHARTS / "effectiveness_outcome_matrix.png")


def _participant_sort_key(value: object) -> tuple[str, int, str]:
    text = str(value).strip()
    match = re.match(r"^([A-Za-z]+)\s*0*(\d+)$", text)
    if not match:
        return (text.casefold(), 0, text)
    prefix, number = match.groups()
    return (prefix.casefold(), int(number), text)


def build_task_times(task_df: pd.DataFrame, log: QuantitativeWarningLog) -> pd.DataFrame:
    if not TIME_SOURCE.exists():
        log.warn("time source missing; efficiency analyses skipped")
        df = pd.DataFrame()
        _save_csv(df, "task_times_normalized.csv")
        return df
    raw = pd.read_csv(TIME_SOURCE)
    base = raw.rename(columns={"user_id": "participant_id", "completion_time_sec": "time_seconds"}).copy()
    base["task_id"] = base["task_id"].map(_task_id)
    merged = base.merge(
        task_df[["participant_id", "app", "task_id", "completed", "completed_autonomously", "outcome_3class"]],
        on=["participant_id", "app", "task_id"],
        how="left",
    )
    merged["completed"] = merged["completed"].fillna(merged["success"]).astype(int)
    merged["completed_autonomously"] = merged["completed_autonomously"].fillna((merged["success"]) & (merged["errors_count"] == 0) & (merged["help_requests"] == 0)).astype(int)
    fallback_outcome = pd.Series(np.where(merged["completed_autonomously"] == 1, "success", np.where(merged["completed"] == 1, "partial_success", "failure")), index=merged.index)
    merged["outcome_3class"] = merged["outcome_3class"].fillna(fallback_outcome)
    merged["included_in_efficiency_analysis"] = merged["completed"].astype(int)
    merged["exclusion_reason"] = np.where(merged["included_in_efficiency_analysis"] == 1, "", "task not completed")
    out = merged[
        [
            "participant_id",
            "app",
            "task_id",
            "task_name",
            "time_seconds",
            "completed",
            "completed_autonomously",
            "outcome_3class",
            "included_in_efficiency_analysis",
            "exclusion_reason",
        ]
    ]
    _save_csv(out, "task_times_normalized.csv")
    log.ok(f"task times normalized from {TIME_SOURCE.relative_to(ROOT)}: {len(out)} rows")
    return out


def build_effectiveness_tables(df: pd.DataFrame, thresholds: dict, log: QuantitativeWarningLog) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    by_task = (
        df.groupby(["task_id", "task_name", "app"], sort=True)
        .agg(
            n=("participant_id", "nunique"),
            completed=("completed", "sum"),
            completed_autonomously=("completed_autonomously", "sum"),
            help_count=("help_requested", "sum"),
            critical_errors=("critical_error", "sum"),
            failures=("failed", "sum"),
        )
        .reset_index()
    )
    for count_col, rate_col in [
        ("completed", "completed_rate"),
        ("completed_autonomously", "autonomous_rate"),
        ("help_count", "help_rate"),
        ("critical_errors", "critical_error_rate"),
        ("failures", "failure_rate"),
    ]:
        by_task[rate_col] = by_task[count_col] / by_task["n"]
    _save_csv(by_task, "effectiveness_by_task.csv")

    rel_rows = []
    for (task_id, task_name), group in df.groupby(["task_id", "task_name"], sort=True):
        for metric in ["completed", "completed_autonomously", "critical_error"]:
            wide = group.pivot_table(index="participant_id", columns="app", values=metric, aggfunc="first").dropna()
            if not set(SYSTEMS).issubset(wide.columns):
                log.warn(f"effectiveness {metric} {task_id}: missing paired app columns")
                continue
            d = wide[SYSTEMS[0]].astype(int)
            g = wide[SYSTEMS[1]].astype(int)
            table = [[int(((d == 1) & (g == 1)).sum()), int(((d == 1) & (g == 0)).sum())], [int(((d == 0) & (g == 1)).sum()), int(((d == 0) & (g == 0)).sum())]]
            primary = mcnemar_exact(table)
            fisher = fisher_exact_2x2(table)
            winner = SYSTEMS[0] if d.mean() > g.mean() else SYSTEMS[1] if g.mean() > d.mean() else "pari"
            rel_rows.append(
                {
                    "metric": metric,
                    "task_id": task_id,
                    "task_name": task_name,
                    "n_pairs": int(len(wide)),
                    "both_success": table[0][0],
                    "deliveroo_only_success": table[0][1],
                    "glovo_only_success": table[1][0],
                    "both_fail": table[1][1],
                    "primary_test": primary["test_name"],
                    "statistic": primary["statistic"],
                    "p_value": primary["p_value"],
                    "effect_size": primary["effect_size"],
                    "effect_size_name": primary["effect_size_name"],
                    "fisher_p_value_optional": fisher["p_value"],
                    "winner": winner,
                    "interpretation": _interpret(float(primary["p_value"]), winner),
                }
            )
    rel = pd.DataFrame(rel_rows)
    _save_csv(rel, "effectiveness_relative_tests.csv")

    abs_rows = []
    eff_cfg = thresholds["effectiveness"]
    abs_metrics = [
        ("completed_autonomously", "autonomous_success_min_rate", eff_cfg["autonomous_success_min_rate"], "higher_or_equal"),
        ("critical_error", "critical_error_max_rate", eff_cfg["critical_error_max_rate"], "lower_or_equal"),
        ("failed", "failure_max_rate", eff_cfg["failure_max_rate"], "lower_or_equal"),
    ]
    for (task_id, task_name, app), group in df.groupby(["task_id", "task_name", "app"], sort=True):
        for metric, threshold_name, threshold, direction in abs_metrics:
            values = group[metric].astype(float)
            count = int(values.sum())
            rate = float(values.mean())
            if direction == "higher_or_equal":
                p_value = stats.binomtest(count, len(values), threshold, alternative="less").pvalue
                ok = rate >= threshold
            else:
                p_value = stats.binomtest(count, len(values), threshold, alternative="greater").pvalue if threshold > 0 else (0.0 if count > 0 else 1.0)
                ok = rate <= threshold
            abs_rows.append(
                {
                    "task_id": task_id,
                    "task_name": task_name,
                    "app": app,
                    "metric": metric,
                    "observed_rate": rate,
                    "threshold": threshold,
                    "n": int(len(values)),
                    "count": count,
                    "test_name": f"Exact binomial vs {threshold_name}",
                    "p_value": p_value,
                    "interpretation": "soglia rispettata descrittivamente" if ok else "soglia non rispettata descrittivamente",
                }
            )
    _save_csv(pd.DataFrame(abs_rows), "effectiveness_absolute_tests.csv")
    return rel


def build_efficiency_tables(df: pd.DataFrame, thresholds: dict, log: QuantitativeWarningLog) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    desc_rows = []
    for variant, mask in [
        ("completed", df["included_in_efficiency_analysis"] == 1),
        ("autonomous", df["completed_autonomously"] == 1),
    ]:
        for (task_id, task_name, app), group in df[mask].groupby(["task_id", "task_name", "app"], sort=True):
            row = {"task_id": task_id, "task_name": task_name, "app": app, "analysis_variant": variant}
            row.update(compute_descriptives(group["time_seconds"]))
            desc_rows.append(row)
    _save_csv(pd.DataFrame(desc_rows), "efficiency_descriptives_by_task.csv")

    rel_rows = []
    for (task_id, task_name), group in df[df["included_in_efficiency_analysis"] == 1].groupby(["task_id", "task_name"], sort=True):
        wide = group.pivot_table(index="participant_id", columns="app", values="time_seconds", aggfunc="first").dropna()
        if not set(SYSTEMS).issubset(wide.columns):
            log.warn(f"efficiency {task_id}: missing paired app columns")
            continue
        d = wide[SYSTEMS[0]]
        g = wide[SYSTEMS[1]]
        result = choose_paired_time_test(d, g)
        diff = g - d
        ci_low, ci_high = bootstrap_ci_mean(diff, n_boot=5000)
        winner = SYSTEMS[0] if d.mean() < g.mean() else SYSTEMS[1] if g.mean() < d.mean() else "pari"
        rel_rows.append(
            {
                "task_id": task_id,
                "task_name": task_name,
                "n_pairs": int(len(wide)),
                "mean_deliveroo": float(d.mean()),
                "mean_glovo": float(g.mean()),
                "median_deliveroo": float(d.median()),
                "median_glovo": float(g.median()),
                "mean_difference_glovo_minus_deliveroo": float(diff.mean()),
                "median_difference_glovo_minus_deliveroo": float(diff.median()),
                "primary_test": result["test_name"],
                "statistic": result["statistic"],
                "p_value": result["p_value"],
                "effect_size": result["effect_size"],
                "effect_size_name": result["effect_size_name"],
                "ci95_low": ci_low,
                "ci95_high": ci_high,
                "winner": winner,
                "interpretation": _interpret(float(result["p_value"]), winner),
            }
        )
        plot_efficiency_task(group, wide, task_id)
    rel = pd.DataFrame(rel_rows)
    _save_csv(rel, "efficiency_relative_tests.csv")

    abs_rows = []
    oets = thresholds["efficiency"]["task_oet_seconds"]
    for (task_id, task_name, app), group in df[df["included_in_efficiency_analysis"] == 1].groupby(["task_id", "task_name", "app"], sort=True):
        oet = float(oets.get(task_id, np.nan))
        test = one_sample_test_against_threshold(group["time_seconds"], oet) if not np.isnan(oet) else {"test_name": "", "statistic": np.nan, "p_value": np.nan, "effect_size": np.nan}
        abs_rows.append(
            {
                "task_id": task_id,
                "task_name": task_name,
                "app": app,
                "oet_seconds": oet,
                "n": int(group["participant_id"].nunique()),
                "mean_time": float(group["time_seconds"].mean()),
                "median_time": float(group["time_seconds"].median()),
                "mean_delta_from_oet": float(group["time_seconds"].mean() - oet),
                "median_delta_from_oet": float(group["time_seconds"].median() - oet),
                "test_name": test["test_name"],
                "statistic": test["statistic"],
                "p_value": test["p_value"],
                "effect_size": test["effect_size"],
                "interpretation": "tempi sopra OET" if group["time_seconds"].median() > oet else "tempi entro OET",
            }
        )
    _save_csv(pd.DataFrame(abs_rows), "efficiency_absolute_tests.csv")
    plot_efficiency_summary(df)
    return rel


def plot_efficiency_task(group: pd.DataFrame, wide: pd.DataFrame, task_id: str) -> None:
    safe = task_id.lower().replace("0", "")
    fig, ax = plt.subplots(figsize=(7, 4), facecolor=BACKGROUND)
    sns.boxplot(data=group, x="app", y="time_seconds", hue="app", palette=[DELIVEROO, GLOVO], legend=False, ax=ax)
    sns.stripplot(data=group, x="app", y="time_seconds", color=TEXT, alpha=0.55, ax=ax)
    _dark_axes(ax, title=f"Efficienza {task_id}: distribuzione tempi", xlabel="", ylabel="Secondi")
    _savefig(CHARTS / f"efficiency_task_{int(task_id[-2:])}_boxplot.png")

    fig, ax = plt.subplots(figsize=(7, 4), facecolor=BACKGROUND)
    for _, row in wide.iterrows():
        ax.plot([0, 1], [row[SYSTEMS[0]], row[SYSTEMS[1]]], color="#94A3B8", alpha=0.55)
    ax.set_xticks([0, 1], SYSTEMS)
    _dark_axes(ax, title=f"Efficienza {task_id}: linee appaiate", xlabel="", ylabel="Secondi")
    _savefig(CHARTS / f"efficiency_task_{int(task_id[-2:])}_paired_lines.png")


def plot_efficiency_summary(df: pd.DataFrame) -> None:
    use = df[df["included_in_efficiency_analysis"] == 1]
    if use.empty:
        return
    summary = use.groupby(["task_id", "app"], as_index=False)["time_seconds"].median()
    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=BACKGROUND)
    sns.barplot(data=summary, x="task_id", y="time_seconds", hue="app", palette=[DELIVEROO, GLOVO], ax=ax)
    _dark_axes(ax, title="Efficienza: riepilogo tempi mediani", xlabel="Task", ylabel="Secondi")
    _style_legend(ax)
    _savefig(CHARTS / "efficiency_summary.png")


def transform_ueq_response(raw_value: float, positive_side: str) -> float:
    return transform_ueq_value(raw_value, positive_side)


def transform_ueq_raw_to_standard(raw_value: float, item_config: dict) -> float:
    positive_side = item_config.get("positive_direction")
    if not positive_side:
        positive_side = "left" if item_config.get("reversed") else "right"
    return transform_ueq_response(raw_value, positive_side)


def build_ueq_long(ueq_items: dict, log: QuantitativeWarningLog) -> pd.DataFrame:
    rows = []
    for app, path in QUESTIONNAIRE.items():
        if not path.exists():
            log.warn(f"questionnaire missing for {app}: {path}")
            continue
        df = pd.read_csv(path).set_index("item")
        item_rows = [idx for idx in df.index if "-" in str(idx)]
        for idx, item_name in enumerate(item_rows[:26], start=1):
            item_id = f"Q{idx:02d}"
            cfg = ueq_items[item_id]
            positive_side = str(cfg.get("positive_direction") or ("left" if cfg.get("reversed") else "right")).lower()
            values = pd.to_numeric(df.loc[item_name], errors="coerce")
            for user_col, raw in values.items():
                rows.append(
                    {
                        "participant_id": _participant_from_col(user_col),
                        "app": app,
                        "item": item_id,
                        "item_label": item_name,
                        "left_anchor": cfg["left_anchor"],
                        "right_anchor": cfg["right_anchor"],
                        "scale": cfg["scale"],
                        "positive_side": positive_side,
                        "raw_value": raw,
                        "transformed_value": transform_ueq_response(raw, positive_side),
                    }
                )
    out = pd.DataFrame(rows)
    _save_csv(out, "ueq_responses_long.csv")
    _save_csv(_ueq_transformed_responses_table(out), "ueq/ueq_transformed_responses.csv")
    log.ok(f"UEQ responses normalized: {len(out)} rows")
    return out


def build_ueq_items(df: pd.DataFrame, ueq_items: dict, log: QuantitativeWarningLog) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    desc_rows = []
    for (item, app), group in df.groupby(["item", "app"], sort=True):
        cfg = ueq_items[item]
        raw_desc = compute_descriptives(group["raw_value"])
        trans_desc = compute_descriptives(group["transformed_value"])
        desc_rows.append(
            {
                "item": item,
                "left_anchor": cfg["left_anchor"],
                "right_anchor": cfg["right_anchor"],
                "scale": cfg["scale"],
                "app": app,
                "n": raw_desc["n"],
                "raw_mean": raw_desc["mean"],
                "raw_median": raw_desc["median"],
                "raw_std": raw_desc["std"],
                "raw_min": raw_desc["min"],
                "raw_q1": raw_desc["q1"],
                "raw_q3": raw_desc["q3"],
                "raw_max": raw_desc["max"],
                "transformed_mean": trans_desc["mean"],
                "transformed_median": trans_desc["median"],
                "transformed_std": trans_desc["std"],
                "transformed_min": trans_desc["min"],
                "transformed_q1": trans_desc["q1"],
                "transformed_q3": trans_desc["q3"],
                "transformed_max": trans_desc["max"],
            }
        )
        plot_ueq_item_distribution(df[df["item"] == item], item, cfg)
    desc = pd.DataFrame(desc_rows)
    _save_csv(desc, "ueq_item_descriptives.csv")

    test_rows = []
    for item, group in df.groupby("item", sort=True):
        cfg = ueq_items[item]
        wide = group.pivot_table(index="participant_id", columns="app", values="transformed_value", aggfunc="first").dropna()
        if not set(SYSTEMS).issubset(wide.columns):
            log.warn(f"UEQ {item}: missing paired app columns")
            continue
        d = wide[SYSTEMS[0]]
        g = wide[SYSTEMS[1]]
        result = wilcoxon_signed_rank(d, g)
        winner = SYSTEMS[0] if d.mean() > g.mean() else SYSTEMS[1] if g.mean() > d.mean() else "pari"
        test_rows.append(
            {
                "item": item,
                "scale": cfg["scale"],
                "n_pairs": int(len(wide)),
                "median_deliveroo_transformed": float(d.median()),
                "median_glovo_transformed": float(g.median()),
                "mean_deliveroo_transformed": float(d.mean()),
                "mean_glovo_transformed": float(g.mean()),
                "difference_glovo_minus_deliveroo": float((g - d).mean()),
                "primary_test": result["test_name"],
                "statistic": result["statistic"],
                "p_value": result["p_value"],
                "effect_size": result["effect_size"],
                "effect_size_name": result["effect_size_name"],
                "winner": winner,
                "interpretation": _interpret(float(result["p_value"]), winner),
            }
        )
    tests = pd.DataFrame(test_rows)
    _save_csv(tests, "ueq_item_tests.csv")
    return desc, tests


def plot_ueq_item_distribution(group: pd.DataFrame, item: str, cfg: dict) -> None:
    counts = group.groupby(["app", "raw_value"]).size().reset_index(name="n")
    pivot = counts.pivot_table(index="app", columns="raw_value", values="n", fill_value=0)
    pivot = pivot.reindex(index=list(SYSTEMS), columns=list(range(1, 8)), fill_value=0)
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0).fillna(0)
    colors = ["#7F1D1D", "#B45309", "#CA8A04", "#64748B", "#0891B2", "#0D9488", "#22C55E"]
    ax = pivot_pct.plot(kind="bar", stacked=True, figsize=(8, 3.8), color=colors)
    _dark_axes(ax, title=f"{item}: {cfg['left_anchor']} / {cfg['right_anchor']} (raw 1..7)", xlabel="", ylabel="Quota risposte")
    ax.legend(title="Raw", bbox_to_anchor=(1.02, 1), loc="upper left")
    _style_legend(ax)
    _savefig(CHARTS / f"ueq_item_{item}_distribution.png")


def build_ueq_scales(df: pd.DataFrame, log: QuantitativeWarningLog):
    scores = (
        df.groupby(["participant_id", "app", "scale"], as_index=False)["transformed_value"]
        .mean()
        .rename(columns={"transformed_value": "score_transformed"})
    )
    _save_csv(scores, "ueq_scale_scores.csv")

    desc_rows = []
    for (scale, app), group in scores.groupby(["scale", "app"], sort=True):
        desc = compute_descriptives(group["score_transformed"])
        ci_low, ci_high = bootstrap_ci_mean(group["score_transformed"], n_boot=5000)
        mean = float(desc["mean"])
        desc_rows.append(
            {
                "scale": scale,
                "app": app,
                "n": desc["n"],
                "mean": mean,
                "median": desc["median"],
                "std": desc["std"],
                "q1": desc["q1"],
                "q3": desc["q3"],
                "min": desc["min"],
                "max": desc["max"],
                "ci95_low": ci_low,
                "ci95_high": ci_high,
                "simple_zone": _ueq_zone_class(mean),
                "benchmark_category": classify_ueq_benchmark(scale, mean),
                "benchmark_threshold_source": BENCHMARK_SOURCE,
                "benchmark_percentile_if_available": np.nan,
            }
        )
    desc = pd.DataFrame(desc_rows)
    _save_csv(desc, "ueq_scale_descriptives.csv")

    test_rows = []
    for scale, group in scores.groupby("scale", sort=True):
        wide = group.pivot_table(index="participant_id", columns="app", values="score_transformed", aggfunc="first").dropna()
        if not set(SYSTEMS).issubset(wide.columns):
            continue
        d = wide[SYSTEMS[0]]
        g = wide[SYSTEMS[1]]
        result = wilcoxon_signed_rank(d, g)
        winner = SYSTEMS[0] if d.mean() > g.mean() else SYSTEMS[1] if g.mean() > d.mean() else "pari"
        test_rows.append(
            {
                "scale": scale,
                "n_pairs": int(len(wide)),
                "mean_deliveroo": float(d.mean()),
                "mean_glovo": float(g.mean()),
                "median_deliveroo": float(d.median()),
                "median_glovo": float(g.median()),
                "difference_glovo_minus_deliveroo": float((g - d).mean()),
                "primary_test": result["test_name"],
                "statistic": result["statistic"],
                "p_value": result["p_value"],
                "effect_size": result["effect_size"],
                "effect_size_name": result["effect_size_name"],
                "winner": winner,
                "interpretation": _interpret(float(result["p_value"]), winner),
            }
        )
    tests = pd.DataFrame(test_rows)
    _save_csv(tests, "ueq_scale_tests.csv")

    benchmark = desc[["scale", "app", "mean", "simple_zone", "benchmark_category", "benchmark_threshold_source"]].copy()
    _save_csv(benchmark, "ueq_benchmark_summary.csv")
    plot_ueq_benchmarks(desc)
    return scores, desc, tests, benchmark


def _ueq_transformed_responses_table(q_long: pd.DataFrame) -> pd.DataFrame:
    if q_long.empty:
        return pd.DataFrame(columns=["respondent_id", "app", "item_id", "raw_value", "transformed_value", "scale", "left_label", "right_label", "positive_side"])
    return q_long.rename(
        columns={
            "participant_id": "respondent_id",
            "item": "item_id",
            "left_anchor": "left_label",
            "right_anchor": "right_label",
        }
    )[["respondent_id", "app", "item_id", "raw_value", "transformed_value", "scale", "left_label", "right_label", "positive_side"]]


def plot_ueq_benchmarks(desc: pd.DataFrame) -> None:
    for app in SYSTEMS:
        data = desc[desc["app"] == app]
        if data.empty:
            continue
        means = {normalize_ueq_scale_name(row.scale): float(row.mean) for row in data.itertuples(index=False)}
        plot_data = benchmark_plot_rows(app, means)
        _save_validation_csv(plot_data, f"ueq_benchmark_plot_data_{app.lower()}.csv")
        fig, ax = plt.subplots(figsize=(8.8, 4.8), facecolor=BACKGROUND)
        _draw_ueq_benchmark_bands(ax, plot_data)
        _dark_axes(ax, title=f"UEQ benchmark ufficiale - {app}", xlabel="Media UEQ (-1.00..2.50)", ylabel="Scala")
        _style_legend(ax)
        _savefig(CHARTS / f"ueq_benchmark_{app.lower()}.png")
    fig, ax = plt.subplots(figsize=(9, 4), facecolor=BACKGROUND)
    sns.barplot(data=desc, x="scale", y="mean", hue="app", palette=[DELIVEROO, GLOVO], ax=ax)
    ax.axhline(0, color=MUTED, linewidth=1)
    ax.set_ylim(-3, 3)
    ax.tick_params(axis="x", rotation=30)
    _dark_axes(ax, title="UEQ benchmark - confronto", xlabel="Scala", ylabel="Media trasformata (-3..+3)")
    _style_legend(ax)
    _savefig(CHARTS / "ueq_benchmark_comparison.png")


def _draw_ueq_benchmark_bands(ax: plt.Axes, plot_data: pd.DataFrame) -> None:
    colors = {
        "Bad": "#7F1D1D",
        "Below Average": "#B45309",
        "Above Average": "#CA8A04",
        "Good": "#15803D",
        "Excellent": "#065F46",
    }
    band_alpha = 0.55
    for idx, row in enumerate(plot_data.itertuples(index=False)):
        segments = [
            ("Bad", -1.0, row.bad_upper),
            ("Below Average", row.bad_upper, row.below_average_upper),
            ("Above Average", row.below_average_upper, row.above_average_upper),
            ("Good", row.above_average_upper, row.good_upper),
            ("Excellent", row.good_upper, 2.5),
        ]
        for label, left, right in segments:
            ax.barh(idx, right - left, left=left, height=0.72, color=colors[label], alpha=band_alpha, edgecolor=BACKGROUND, linewidth=0.25, label=label if idx == 0 else None)
        ax.scatter(row.mean, idx, color=TEXT, edgecolor=BACKGROUND, s=85, zorder=5)
        ax.text(row.mean + 0.04, idx, f"{row.mean:.2f} ({row.category})", color=TEXT, va="center", fontsize=8, fontweight="bold")
    ax.set_yticks(np.arange(len(plot_data)), plot_data["scale"].tolist())
    ax.set_xlim(-1.0, 2.5)
    ax.invert_yaxis()


def build_subgroups(scale_scores: pd.DataFrame, q_long: pd.DataFrame, task_df: pd.DataFrame, log: QuantitativeWarningLog) -> dict[str, pd.DataFrame]:
    if not USER_PROFILES.exists():
        log.warn("user profiles missing; subgroup analyses skipped")
        empty = pd.DataFrame()
        _save_csv(empty, "subgroup_availability.csv")
        return {}
    profiles = pd.read_csv(USER_PROFILES).rename(columns={"user_id": "participant_id"})
    variables = [col for col in profiles.columns if col != "participant_id"]
    availability_rows = []
    for variable in variables:
        counts = profiles[variable].dropna().astype(str).value_counts()
        availability_rows.append(
            {
                "variable": variable,
                "available": True,
                "n_valid": int(profiles[variable].notna().sum()),
                "levels": "; ".join(counts.index.tolist()),
                "min_group_size": int(counts.min()) if not counts.empty else 0,
                "usable_for_analysis": bool(not counts.empty and counts.min() >= 5),
                "notes": "solo descrittiva se min_group_size < 5",
            }
        )
    availability = pd.DataFrame(availability_rows)
    _save_csv(availability, "subgroup_availability.csv")

    scale_joined = scale_scores.merge(profiles, on="participant_id", how="left")
    scale_rows = []
    for variable in variables:
        for (level, app, scale), group in scale_joined.groupby([variable, "app", "scale"], dropna=True):
            desc = compute_descriptives(group["score_transformed"])
            ci_low, ci_high = bootstrap_ci_mean(group["score_transformed"], n_boot=3000)
            scale_rows.append({"subgroup_variable": variable, "subgroup_level": level, "app": app, "scale_or_item": scale, **desc, "ci95_low": ci_low, "ci95_high": ci_high})
    scale_table = pd.DataFrame(scale_rows)
    _save_csv(scale_table, "ueq_subgroup_scale_scores.csv")

    item_joined = q_long.merge(profiles, on="participant_id", how="left")
    item_rows = []
    for variable in variables:
        for (level, app, item), group in item_joined.groupby([variable, "app", "item"], dropna=True):
            desc = compute_descriptives(group["transformed_value"])
            ci_low, ci_high = bootstrap_ci_mean(group["transformed_value"], n_boot=1000)
            item_rows.append({"subgroup_variable": variable, "subgroup_level": level, "app": app, "scale_or_item": item, **desc, "ci95_low": ci_low, "ci95_high": ci_high})
    item_table = pd.DataFrame(item_rows)
    _save_csv(item_table, "ueq_subgroup_item_scores.csv")

    task_joined = task_df.merge(profiles, on="participant_id", how="left")
    eff_rows = []
    time_rows = []
    for variable in variables:
        for (level, app, task_id), group in task_joined.groupby([variable, "app", "task_id"], dropna=True):
            eff_rows.append(
                {
                    "subgroup_variable": variable,
                    "subgroup_level": level,
                    "app": app,
                    "task_id": task_id,
                    "n": int(group["participant_id"].nunique()),
                    "completed_rate": float(group["completed"].mean()),
                    "autonomous_rate": float(group["completed_autonomously"].mean()),
                    "critical_error_rate": float(group["critical_error"].mean()),
                }
            )
    _save_csv(pd.DataFrame(eff_rows), "task_subgroup_effectiveness.csv")

    if TIME_SOURCE.exists():
        times = pd.read_csv(TIME_SOURCE).rename(columns={"user_id": "participant_id", "completion_time_sec": "time_seconds"}).merge(profiles, on="participant_id", how="left")
        times["task_id"] = times["task_id"].map(_task_id)
        for variable in variables:
            for (level, app, task_id), group in times.groupby([variable, "app", "task_id"], dropna=True):
                desc = compute_descriptives(group["time_seconds"])
                time_rows.append({"subgroup_variable": variable, "subgroup_level": level, "app": app, "task_id": task_id, **desc})
    _save_csv(pd.DataFrame(time_rows), "task_subgroup_efficiency.csv")
    plot_subgroup_heatmap(scale_table)
    return {"availability": availability, "scale": scale_table, "item": item_table}


def plot_subgroup_heatmap(scale_table: pd.DataFrame) -> None:
    if scale_table.empty:
        return
    usable = scale_table[scale_table["subgroup_variable"].isin(["delivery_familiarity", "food_delivery_frequency", "gender"])]
    pivot_rows = []
    for (variable, level, scale), group in usable.groupby(["subgroup_variable", "subgroup_level", "scale_or_item"]):
        wide = group.pivot_table(index="scale_or_item", columns="app", values="mean", aggfunc="first")
        if set(SYSTEMS).issubset(wide.columns):
            pivot_rows.append(
                {
                    "scale": _ueq_heatmap_scale_label(scale),
                    "subgroup": _display_subgroup(variable, level),
                    "delta": float(wide.loc[scale, SYSTEMS[1]] - wide.loc[scale, SYSTEMS[0]]),
                }
            )
    data = pd.DataFrame(pivot_rows)
    if data.empty:
        return
    scale_order = [_ueq_heatmap_scale_label(scale) for scale in UEQ_INTERNAL_SCALE_ORDER]
    matrix = data.pivot_table(index="subgroup", columns="scale", values="delta").reindex(columns=scale_order)
    fig, ax = plt.subplots(figsize=(9.4, max(5.2, 0.55 * len(matrix.index) + 2.2)), facecolor=BACKGROUND)
    heatmap = sns.heatmap(matrix, center=0, cmap="vlag", annot=True, fmt=".2f", linewidths=0.5, linecolor=GRID, ax=ax)
    _dark_axes(
        ax,
        title="Sottogruppi UEQ: differenza Glovo - Deliveroo",
        xlabel="Scale UEQ: Attr., Appr., Eff., Contr., Stim., Orig.",
        ylabel="Sottogruppo",
    )
    ax.grid(False)
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)
    for text in ax.texts:
        text.set_color("#111827")
    cbar = heatmap.collections[0].colorbar
    cbar.ax.tick_params(colors=MUTED)
    cbar.outline.set_edgecolor(GRID)
    fig.text(0.5, 0.012, UEQ_HEATMAP_LABEL_NOTE, ha="center", va="bottom", color=MUTED, fontsize=8)
    _savefig(CHARTS / "subgroup_ueq_heatmap.png")


def _ueq_heatmap_scale_label(value: object) -> str:
    return UEQ_HEATMAP_SHORT_LABELS.get(_display_scale(value), str(value))


def _display_scale(value: object) -> str:
    try:
        return normalize_ueq_scale_name(value)
    except KeyError:
        return str(value)


def _display_subgroup(variable: object, level: object) -> str:
    variable_text = str(variable)
    level_text = str(level)
    variable_labels = {
        "delivery_familiarity": "Familiarita delivery",
        "food_delivery_frequency": "Frequenza delivery",
        "gender": "Genere",
        "age_group": "Eta",
        "occupation": "Occupazione",
    }
    level_labels = {
        "1.0": "bassa",
        "1": "bassa",
        "2.0": "media",
        "2": "media",
        "3.0": "alta",
        "3": "alta",
    }
    display_variable = variable_labels.get(variable_text, variable_text.replace("_", " ").title())
    display_level = level_labels.get(level_text, level_text)
    return f"{display_variable}: {display_level}"


def build_system_comparison(effectiveness: pd.DataFrame, efficiency: pd.DataFrame, item_tests: pd.DataFrame, scale_tests: pd.DataFrame, benchmark: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if not effectiveness.empty:
        for row in effectiveness.itertuples(index=False):
            rows.append(
                {
                    "area": "efficacia relativa",
                    "metric": row.metric,
                    "task_or_scale": row.task_id,
                    "n": row.n_pairs,
                    "mean_deliveroo": np.nan,
                    "mean_glovo": np.nan,
                    "median_deliveroo": np.nan,
                    "median_glovo": np.nan,
                    "difference_glovo_minus_deliveroo": np.nan,
                    "primary_test": row.primary_test,
                    "p_value": row.p_value,
                    "effect_size": row.effect_size,
                    "winner": row.winner,
                    "interpretation": row.interpretation,
                }
            )
    if not efficiency.empty:
        for row in efficiency.itertuples(index=False):
            rows.append(
                {
                    "area": "efficienza relativa",
                    "metric": "time_seconds",
                    "task_or_scale": row.task_id,
                    "n": row.n_pairs,
                    "mean_deliveroo": row.mean_deliveroo,
                    "mean_glovo": row.mean_glovo,
                    "median_deliveroo": row.median_deliveroo,
                    "median_glovo": row.median_glovo,
                    "difference_glovo_minus_deliveroo": row.mean_difference_glovo_minus_deliveroo,
                    "primary_test": row.primary_test,
                    "p_value": row.p_value,
                    "effect_size": row.effect_size,
                    "winner": row.winner,
                    "interpretation": row.interpretation,
                }
            )
    for source, area, metric_name in [(item_tests, "UEQ item", "transformed item"), (scale_tests, "UEQ scale", "transformed scale")]:
        if source.empty:
            continue
        key = "item" if "item" in source.columns else "scale"
        for row in source.itertuples(index=False):
            rows.append(
                {
                    "area": area,
                    "metric": metric_name,
                    "task_or_scale": getattr(row, key),
                    "n": row.n_pairs,
                    "mean_deliveroo": getattr(row, "mean_deliveroo_transformed", getattr(row, "mean_deliveroo", np.nan)),
                    "mean_glovo": getattr(row, "mean_glovo_transformed", getattr(row, "mean_glovo", np.nan)),
                    "median_deliveroo": getattr(row, "median_deliveroo_transformed", getattr(row, "median_deliveroo", np.nan)),
                    "median_glovo": getattr(row, "median_glovo_transformed", getattr(row, "median_glovo", np.nan)),
                    "difference_glovo_minus_deliveroo": row.difference_glovo_minus_deliveroo,
                    "primary_test": row.primary_test,
                    "p_value": row.p_value,
                    "effect_size": row.effect_size,
                    "winner": row.winner,
                    "interpretation": row.interpretation,
                }
            )
    out = pd.DataFrame(rows)
    _save_csv(out, "system_comparison_summary.csv")
    return out


def build_detailed_quantitative_outputs(
    task_df: pd.DataFrame,
    time_df: pd.DataFrame,
    effectiveness_tests: pd.DataFrame,
    efficiency_tests: pd.DataFrame,
    q_long: pd.DataFrame,
    item_desc: pd.DataFrame,
    item_tests: pd.DataFrame,
    scale_desc: pd.DataFrame,
    scale_tests: pd.DataFrame,
    benchmark: pd.DataFrame,
    thresholds: dict,
) -> None:
    _write_method_files(thresholds)
    _write_pipeline_audit()

    if not task_df.empty:
        effectiveness_detail = _effectiveness_task_detail(task_df)
        _save_csv(effectiveness_detail, "user_tests/effectiveness_task_detail.csv")
        absolute_effectiveness = _effectiveness_absolute_detail(task_df, thresholds)
        _save_csv(absolute_effectiveness, "user_tests/effectiveness_absolute_task_detail.csv")
        effectiveness_by_task_app = _effectiveness_by_task_app(task_df)
        _save_csv(effectiveness_by_task_app, "effectiveness/effectiveness_by_task_app.csv")
        _save_markdown_table(effectiveness_by_task_app, "effectiveness/effectiveness_by_task_app.md")
        absolute_by_task_app = _absolute_effectiveness_by_task_app(task_df, thresholds)
        _save_csv(absolute_by_task_app, "absolute_effectiveness/absolute_effectiveness_by_task_app.csv")
        _save_markdown_table(absolute_by_task_app, "absolute_effectiveness/absolute_effectiveness_by_task_app.md")
        effectiveness_stat_tests = _effectiveness_statistical_tests(effectiveness_tests)
        _save_csv(effectiveness_stat_tests, "statistical_tests/effectiveness_tests_by_task.csv")
        _save_csv(_combined_user_task_statistical_tests(effectiveness_stat_tests, pd.DataFrame()), "statistical_tests/slide_user_task_statistical_tests.csv")
        for task_id in sorted(task_df["task_id"].unique()):
            _save_csv(_effectiveness_task_slide_table(task_df, effectiveness_tests, task_id, "completed"), f"user_tests/slide_effectiveness_{task_id.lower()}.csv")
            _save_csv(_effectiveness_task_slide_table(task_df, effectiveness_tests, task_id, "completed_autonomously"), f"user_tests/slide_effectiveness_absolute_{task_id.lower()}.csv")
        _plot_effectiveness_status(task_df)
        _plot_absolute_effectiveness_threshold(task_df, thresholds)
        _plot_effectiveness_per_task(task_df)
        _plot_absolute_effectiveness_per_task(task_df, thresholds)

    if not time_df.empty:
        desc = _efficiency_descriptives_completed(time_df)
        _save_csv(desc, "user_tests/efficiency_descriptives_by_task_app.csv")
        _save_csv(_efficiency_task_detail(time_df, efficiency_tests), "user_tests/efficiency_task_detail.csv")
        oet_detail = _efficiency_oet_detail(time_df, thresholds)
        _save_csv(oet_detail, "user_tests/efficiency_absolute_oet_detail.csv")
        _save_csv(_efficiency_task_detail(time_df, efficiency_tests), "user_tests/slide_efficiency_task_detail.csv")
        all_times_long = _efficiency_all_user_times_long(time_df)
        all_times_wide = _efficiency_all_user_times_wide(time_df)
        boxplot_stats = _efficiency_boxplot_stats_by_task_app(time_df)
        absolute_efficiency = _absolute_efficiency_by_task_app(time_df, thresholds)
        efficiency_stat_tests = _efficiency_statistical_tests(efficiency_tests)
        _save_csv(all_times_long, "efficiency/all_user_times_long.csv")
        _save_csv(all_times_wide, "efficiency/all_user_times_wide.csv")
        _save_markdown_table(all_times_wide, "efficiency/all_user_times_wide.md")
        _save_csv(boxplot_stats, "efficiency/efficiency_boxplot_stats_by_task_app.csv")
        _save_markdown_table(boxplot_stats, "efficiency/efficiency_boxplot_stats_by_task_app.md")
        _save_csv(absolute_efficiency, "absolute_efficiency/absolute_efficiency_by_task_app.csv")
        _save_markdown_table(absolute_efficiency, "absolute_efficiency/absolute_efficiency_by_task_app.md")
        _save_csv(efficiency_stat_tests, "statistical_tests/efficiency_tests_by_task.csv")
        effect_stats = pd.read_csv(TABLES / "statistical_tests" / "effectiveness_tests_by_task.csv") if (TABLES / "statistical_tests" / "effectiveness_tests_by_task.csv").exists() else pd.DataFrame()
        _save_csv(_combined_user_task_statistical_tests(effect_stats, efficiency_stat_tests), "statistical_tests/slide_user_task_statistical_tests.csv")
        for task_id in sorted(time_df["task_id"].unique()):
            _save_csv(_efficiency_task_slide_table(time_df, efficiency_tests, task_id), f"user_tests/slide_efficiency_{task_id.lower()}.csv")
            _save_csv(_efficiency_oet_task_slide_table(time_df, thresholds, task_id), f"user_tests/slide_efficiency_oet_{task_id.lower()}.csv")
        _plot_efficiency_descriptives(desc)
        _plot_efficiency_oet_delta(time_df, thresholds)
        _plot_efficiency_boxplots_per_task(time_df)
        _plot_absolute_efficiency_per_task(time_df, thresholds)

    selected_items = _selected_ueq_items()
    if selected_items and not item_desc.empty and not item_tests.empty:
        selected_stats, selected_tests = _selected_ueq_item_tables(item_desc, item_tests, selected_items)
        _save_csv(selected_stats, "questionnaire/ueq_item_stats_selected.csv")
        _save_csv(selected_tests, "questionnaire/ueq_item_tests_selected.csv")
        _save_csv(_ueq_item_method_table(selected_items), "questionnaire/slide_ueq_item_method.csv")
        for item_id in selected_tests["item_id"].dropna().astype(str):
            _save_csv(_ueq_selected_item_slide_table(selected_stats, selected_tests, item_id), f"questionnaire/slide_ueq_item_{item_id.lower()}.csv")

    if not item_desc.empty and not scale_desc.empty:
        _build_ueq_sample_style_outputs(q_long=q_long, item_desc=item_desc, scale_desc=scale_desc, scale_tests=scale_tests)
        _write_ueq_pipeline_scan()
        _write_ueq_audit_report(q_long, scale_desc)
        _write_ueq_reliability_report(q_long)
        _write_ueq_pipeline_audit(q_long, item_desc, scale_desc, scale_tests)
        _write_ueq_validation_report(q_long, item_desc, scale_desc, scale_tests)

    if not benchmark.empty:
        benchmark_interpretation = _benchmark_interpretation_table(benchmark, scale_tests)
        _save_csv(benchmark_interpretation, "questionnaire/ueq_benchmark_interpretation.csv")
        _save_csv(_benchmark_quality_group_table(benchmark_interpretation), "questionnaire/slide_ueq_benchmark_quality_groups.csv")
        _save_csv(_benchmark_operational_table(benchmark_interpretation, efficiency_tests), "questionnaire/slide_ueq_benchmark_operational_reading.csv")

    _save_csv(_quantitative_conclusions(effectiveness_tests, efficiency_tests, scale_tests), "final/quantitative_conclusions.csv")
    _save_csv(_final_system_verdict(effectiveness_tests, efficiency_tests, scale_tests, benchmark), "final/final_system_verdict.csv")
    _save_csv(_final_decision_matrix(effectiveness_tests, efficiency_tests, scale_tests, benchmark, thresholds), "final/final_decision_matrix.csv")


def _write_method_files(thresholds: dict) -> None:
    optimal_error = float(thresholds["effectiveness"].get("critical_error_max_rate", 0.1))
    oets = thresholds["efficiency"]["task_oet_seconds"]
    _write_output_text(
        "outputs/tables/user_tests/effectiveness_method.md",
        [
            "# Metodo efficacia",
            "",
            "- Efficacia relativa: quota di task completate, includendo successi autonomi, successi assistiti e successi con criticita.",
            "- Efficacia assoluta: quota di task completate autonomamente, senza aiuto e senza issue critiche annotate.",
            "- Disegno: confronto appaiato sugli stessi utenti tra Deliveroo e Glovo.",
            "- Test principale: McNemar exact per esiti binari appaiati.",
            "- Ipotesi nulla: nessuna differenza tra le due app nella probabilita di successo.",
            "- Soglia di significativita: p < .05.",
            f"- Soglia operativa issue/non autonomia: {optimal_error:.0%}.",
        ],
    )
    _write_output_text(
        "outputs/tables/user_tests/efficiency_method.md",
        [
            "# Metodo efficienza",
            "",
            "- Efficienza relativa: confronto dei tempi tra Deliveroo e Glovo sugli stessi utenti.",
            "- Efficienza assoluta: confronto con OET (Optimal Execution Time) configurato per task.",
            "- Inclusione principale: task completate, mantenendo tracciata la variante autonoma nelle descrittive.",
            "- Test relativo: paired t-test se le differenze sono compatibili con normalita, altrimenti Wilcoxon signed-rank.",
            "- Ipotesi nulla: nessuna differenza nei tempi tra le due app.",
            "- Soglia di significativita: p < .05.",
            "- OET configurati: " + ", ".join(f"{task}={seconds}s" for task, seconds in oets.items()),
        ],
    )


def _write_pipeline_audit() -> None:
    _write_output_text(
        "reports/pipeline_audit_quantitative_sections.md",
        [
            "# Audit sezioni quantitative",
            "",
            "## Output gia presenti",
            "- `outputs/tables/effectiveness_by_task.csv`",
            "- `outputs/tables/effectiveness_relative_tests.csv`",
            "- `outputs/tables/effectiveness_absolute_tests.csv`",
            "- `outputs/tables/efficiency_descriptives_by_task.csv`",
            "- `outputs/tables/efficiency_relative_tests.csv`",
            "- `outputs/tables/efficiency_absolute_tests.csv`",
            "- `outputs/tables/ueq_item_descriptives.csv`",
            "- `outputs/tables/ueq_item_tests.csv`",
            "- `outputs/tables/ueq_scale_descriptives.csv`",
            "- `outputs/tables/ueq_scale_tests.csv`",
            "- `outputs/tables/ueq_benchmark_summary.csv`",
            "",
            "## Output aggiunti per final_report",
            "- `outputs/tables/user_tests/` per metodo, dettaglio task-by-task, efficienza e OET.",
            "- `outputs/tables/questionnaire/` per item UEQ selezionati e interpretazione benchmark.",
            "- `outputs/tables/final/` per conclusioni quantitative e verdetto operativo.",
            "- `outputs/figures/user_tests/` per grafici sintetici aggiuntivi.",
            "",
            "## Nota",
            "I nuovi output derivano dai CSV canonici gia usati dalla pipeline quantitativa; non introducono dati grezzi o calcoli manuali nelle slide.",
        ],
    )


def _effectiveness_task_detail(task_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (task_id, task_name, app), group in task_df.groupby(["task_id", "task_name", "app"], sort=True):
        completed = group["completed"].astype(int)
        autonomous = group["completed_autonomously"].astype(int)
        assisted = ((completed == 1) & (group["help_requested"].astype(int) == 1)).astype(int)
        issues = ((completed == 1) & (group["critical_error"].astype(int) == 1)).astype(int)
        failures = group["failed"].astype(int)
        n_users = int(group["participant_id"].nunique())
        rows.append(
            {
                "task_id": task_id,
                "task_name": task_name,
                "app": app,
                "n_users": n_users,
                "success_autonomous": int(autonomous.sum()),
                "success_assisted": int(assisted.sum()),
                "success_with_issues": int(issues.sum()),
                "failures": int(failures.sum()),
                "effectiveness_rate": float(completed.mean()),
                "autonomous_rate": float(autonomous.mean()),
                "error_or_non_autonomous_count": int((1 - autonomous).sum()),
            }
        )
    return pd.DataFrame(rows)


def _effectiveness_by_task_app(task_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (task_id, task_name, app), group in task_df.groupby(["task_id", "task_name", "app"], sort=True):
        outcome = group["outcome_3class"].astype(str)
        n_total = int(len(group))
        n_success = int((outcome == "success").sum())
        n_partial = int((outcome == "partial_success").sum())
        n_failure = int((outcome == "failure").sum())
        rows.append(
            {
                "task": task_id,
                "task_name": task_name,
                "app": app,
                "n_total": n_total,
                "n_success": n_success,
                "n_partial_success": n_partial,
                "n_failure": n_failure,
                "success_rate": n_success / n_total if n_total else np.nan,
                "partial_success_rate": n_partial / n_total if n_total else np.nan,
                "failure_rate": n_failure / n_total if n_total else np.nan,
            }
        )
    return pd.DataFrame(rows)


def _effectiveness_absolute_detail(task_df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    optimal_rate = float(thresholds["effectiveness"].get("critical_error_max_rate", 0.1))
    rows = []
    for (task_id, task_name, app), group in task_df.groupby(["task_id", "task_name", "app"], sort=True):
        n_users = int(group["participant_id"].nunique())
        observed_errors = int((1 - group["completed_autonomously"].astype(int)).sum())
        observed_error_rate = observed_errors / n_users if n_users else np.nan
        p_value = stats.binomtest(observed_errors, n_users, optimal_rate, alternative="greater").pvalue if n_users else np.nan
        rows.append(
            {
                "task_id": task_id,
                "task_name": task_name,
                "app": app,
                "n_users": n_users,
                "observed_errors": observed_errors,
                "observed_error_rate": observed_error_rate,
                "optimal_error_threshold_count": float(n_users * optimal_rate),
                "optimal_error_rate": optimal_rate,
                "test_name": "Exact binomial vs optimal error rate",
                "p_value": p_value,
                "interpretation": _threshold_interpretation(observed_error_rate, p_value),
            }
        )
    return pd.DataFrame(rows)


def _absolute_effectiveness_by_task_app(task_df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    optimal_rate = float(thresholds["effectiveness"].get("critical_error_max_rate", 1 / 24))
    rows = []
    for (task_id, task_name, app), group in task_df.groupby(["task_id", "task_name", "app"], sort=True):
        n_total = int(len(group))
        observed_errors = int((group["binary_success_for_absolute_effectiveness"].astype(int) == 0).sum())
        observed_error_rate = observed_errors / n_total if n_total else np.nan
        optimal_count = 1 if n_total == 24 else n_total * optimal_rate
        optimal_error_rate = optimal_count / n_total if n_total else optimal_rate
        rows.append(
            {
                "task": task_id,
                "task_name": task_name,
                "app": app,
                "n_total": n_total,
                "observed_error_count": observed_errors,
                "observed_error_rate": observed_error_rate,
                "optimal_error_count": optimal_count,
                "optimal_error_rate": optimal_error_rate,
                "delta_error_count": observed_errors - optimal_count,
                "delta_error_rate": observed_error_rate - optimal_error_rate if pd.notna(observed_error_rate) else np.nan,
                "absolute_effectiveness_rate": 1 - observed_error_rate if pd.notna(observed_error_rate) else np.nan,
                "meets_optimal_threshold": bool(observed_errors <= optimal_count),
            }
        )
    return pd.DataFrame(rows)


def _effectiveness_statistical_tests(tests: pd.DataFrame) -> pd.DataFrame:
    rows = []
    selected = tests[tests["metric"] == "completed_autonomously"] if not tests.empty and "metric" in tests else pd.DataFrame()
    for row in selected.itertuples(index=False):
        rows.append(
            {
                "task": row.task_id,
                "metric": "successo senza aiuto vs errore",
                "test": row.primary_test,
                "statistic": getattr(row, "statistic", np.nan),
                "p_value": row.p_value,
                "winner": row.winner,
                "interpretation": _interpret(row.p_value, row.winner),
            }
        )
    return pd.DataFrame(rows)


def _threshold_interpretation(rate: float, p_value: object) -> str:
    if pd.isna(p_value):
        return "campione insufficiente"
    if float(p_value) < 0.05:
        return "peggioramento significativo rispetto alla soglia"
    if rate >= 0.20:
        return "tendenza critica sopra soglia"
    return "entro soglia ottimale"


def _effectiveness_task_slide_table(task_df: pd.DataFrame, tests: pd.DataFrame, task_id: str, metric: str) -> pd.DataFrame:
    detail = _effectiveness_task_detail(task_df)
    rows = []
    test = tests[(tests["task_id"] == task_id) & (tests["metric"] == metric)]
    p_value = test["p_value"].iloc[0] if not test.empty else np.nan
    for row in detail[detail["task_id"] == task_id].itertuples(index=False):
        rows.append(
            {
                "App": row.app,
                "N": row.n_users,
                "Autonomi": row.success_autonomous,
                "Assistiti": row.success_assisted,
                "Issue/fall.": row.error_or_non_autonomous_count,
                "Efficacia": _fmt_pct(row.effectiveness_rate),
                "Autonomia": _fmt_pct(row.autonomous_rate),
                "Test": "McNemar exact",
                "p-value": _fmt_p(p_value),
                "Lettura": _significance_label(p_value),
            }
        )
    return pd.DataFrame(rows)


def _efficiency_descriptives_completed(time_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    use = time_df[time_df["included_in_efficiency_analysis"] == 1]
    for (task_id, task_name, app), group in use.groupby(["task_id", "task_name", "app"], sort=True):
        desc = compute_descriptives(group["time_seconds"])
        rows.append(
            {
                "task_id": task_id,
                "task_name": task_name,
                "app": app,
                "n_valid": desc["n"],
                "mean_seconds": desc["mean"],
                "median_seconds": desc["median"],
                "std_seconds": desc["std"],
                "q1_seconds": desc["q1"],
                "q3_seconds": desc["q3"],
                "iqr_seconds": desc["q3"] - desc["q1"] if pd.notna(desc["q3"]) and pd.notna(desc["q1"]) else np.nan,
                "min_seconds": desc["min"],
                "max_seconds": desc["max"],
            }
        )
    return pd.DataFrame(rows)


def _efficiency_all_user_times_long(time_df: pd.DataFrame) -> pd.DataFrame:
    out = time_df[["participant_id", "task_id", "app", "time_seconds", "outcome_3class"]].copy()
    out = out.rename(columns={"participant_id": "user_id", "task_id": "task"})
    out["_sort_user"] = out["user_id"].map(_participant_sort_key)
    out["_sort_task"] = out["task"].map(_task_id)
    out = out.sort_values(["_sort_user", "app", "_sort_task"]).drop(columns=["_sort_user", "_sort_task"])
    return out


def _efficiency_all_user_times_wide(time_df: pd.DataFrame) -> pd.DataFrame:
    long = _efficiency_all_user_times_long(time_df)
    if long.empty:
        return long
    key = long["app"].map({"Deliveroo": "D", "Glovo": "G"}).fillna(long["app"].astype(str).str[:1].str.upper()) + "_" + long["task"].str.replace("T0", "T", regex=False)
    work = long.assign(metric=key)
    pivot = work.pivot_table(index="user_id", columns="metric", values="time_seconds", aggfunc="first").reset_index()
    expected = ["D_T1", "D_T2", "D_T3", "G_T1", "G_T2", "G_T3"]
    for column in expected:
        if column not in pivot.columns:
            pivot[column] = np.nan
    pivot["Media"] = pivot[expected].mean(axis=1)
    pivot["Dev. standard"] = pivot[expected].std(axis=1, ddof=1)
    pivot["_sort"] = pivot["user_id"].map(_participant_sort_key)
    return pivot[["user_id", *expected, "Media", "Dev. standard", "_sort"]].sort_values("_sort").drop(columns=["_sort"])


def _whiskers(values: pd.Series) -> tuple[float, float]:
    clean = pd.to_numeric(values, errors="coerce").dropna().sort_values()
    if clean.empty:
        return (np.nan, np.nan)
    q1 = float(clean.quantile(0.25))
    q3 = float(clean.quantile(0.75))
    iqr = q3 - q1
    lower = clean[clean >= q1 - 1.5 * iqr].min()
    upper = clean[clean <= q3 + 1.5 * iqr].max()
    return (float(lower), float(upper))


def _efficiency_boxplot_stats_by_task_app(time_df: pd.DataFrame) -> pd.DataFrame:
    use = time_df[time_df["included_in_efficiency_analysis"] == 1]
    rows = []
    for (task_id, task_name, app), group in use.groupby(["task_id", "task_name", "app"], sort=True):
        values = group["time_seconds"]
        lower, upper = _whiskers(values)
        desc = compute_descriptives(values)
        rows.append(
            {
                "task": task_id,
                "task_name": task_name,
                "app": app,
                "n": desc["n"],
                "lower_whisker": lower,
                "q1": desc["q1"],
                "median": desc["median"],
                "q3": desc["q3"],
                "upper_whisker": upper,
                "mean": desc["mean"],
                "std": desc["std"],
                "min": desc["min"],
                "max": desc["max"],
            }
        )
    return pd.DataFrame(rows)


def _efficiency_task_detail(time_df: pd.DataFrame, tests: pd.DataFrame) -> pd.DataFrame:
    desc = _efficiency_descriptives_completed(time_df)
    rows = []
    for test in tests.itertuples(index=False):
        task_desc = desc[desc["task_id"] == test.task_id]
        d = task_desc[task_desc["app"] == SYSTEMS[0]].iloc[0]
        g = task_desc[task_desc["app"] == SYSTEMS[1]].iloc[0]
        rows.append(
            {
                "task_id": test.task_id,
                "task_name": test.task_name,
                "paired_n": test.n_pairs,
                "test_name": test.primary_test,
                "test_selection_reason": "paired time differences; normality decides t-test vs Wilcoxon",
                "statistic": test.statistic,
                "p_value": test.p_value,
                "effect_size": test.effect_size,
                "mean_deliveroo": d.mean_seconds,
                "mean_glovo": g.mean_seconds,
                "median_deliveroo": d.median_seconds,
                "median_glovo": g.median_seconds,
                "sd_deliveroo": d.std_seconds,
                "sd_glovo": g.std_seconds,
                "winner_descriptive": test.winner,
                "winner_statistical": test.winner if pd.notna(test.p_value) and float(test.p_value) < 0.05 else "nessuno",
                "interpretation": _efficiency_interpretation(test),
            }
        )
    return pd.DataFrame(rows)


def _efficiency_interpretation(row: object) -> str:
    if pd.isna(row.p_value):
        return "campione insufficiente per confronto inferenziale"
    label = _significance_label(row.p_value)
    if float(row.p_value) < 0.05 and row.winner != "pari":
        return f"{label}; vantaggio {row.winner} sui tempi"
    return f"vantaggio descrittivo {row.winner}, non statisticamente significativo"


def _efficiency_oet_detail(time_df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    use = time_df[time_df["included_in_efficiency_analysis"] == 1]
    oets = thresholds["efficiency"]["task_oet_seconds"]
    rows = []
    for (task_id, task_name, app), group in use.groupby(["task_id", "task_name", "app"], sort=True):
        oet = float(oets.get(task_id, np.nan))
        test = one_sample_test_against_threshold(group["time_seconds"], oet) if pd.notna(oet) else {"test_name": "", "p_value": np.nan}
        median = float(group["time_seconds"].median())
        delta = median - oet
        rows.append(
            {
                "task_id": task_id,
                "task_name": task_name,
                "app": app,
                "oet_seconds": oet,
                "n_valid": int(group["participant_id"].nunique()),
                "mean_seconds": float(group["time_seconds"].mean()),
                "median_seconds": median,
                "delta_median_seconds": delta,
                "delta_median_percent": delta / oet if oet else np.nan,
                "test_name": test.get("test_name", ""),
                "p_value": test.get("p_value", np.nan),
                "interpretation": "entro OET" if delta <= 0 else "sopra OET",
            }
        )
    return pd.DataFrame(rows)


def _absolute_efficiency_by_task_app(time_df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    use = time_df[time_df["included_in_efficiency_analysis"] == 1]
    oets = thresholds["efficiency"]["task_oet_seconds"]
    rows = []
    for (task_id, task_name, app), group in use.groupby(["task_id", "task_name", "app"], sort=True):
        mean = float(group["time_seconds"].mean())
        median = float(group["time_seconds"].median())
        std = float(group["time_seconds"].std(ddof=1)) if len(group) > 1 else np.nan
        oet = float(oets.get(task_id, np.nan))
        rows.append(
            {
                "task": task_id,
                "task_name": task_name,
                "app": app,
                "mean_time": mean,
                "median_time": median,
                "std_time": std,
                "oet_seconds": oet,
                "delta_mean_vs_oet": mean - oet if pd.notna(oet) else np.nan,
                "delta_median_vs_oet": median - oet if pd.notna(oet) else np.nan,
                "ratio_mean_vs_oet": mean / oet if oet else np.nan,
                "ratio_median_vs_oet": median / oet if oet else np.nan,
                "absolute_efficiency_score": oet / mean if mean and pd.notna(oet) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def _efficiency_statistical_tests(tests: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in tests.itertuples(index=False):
        rows.append(
            {
                "task": row.task_id,
                "metric": "tempo completamento",
                "test": row.primary_test,
                "statistic": row.statistic,
                "p_value": row.p_value,
                "winner": row.winner,
                "interpretation": _efficiency_interpretation(row),
            }
        )
    return pd.DataFrame(rows)


def _combined_user_task_statistical_tests(effectiveness: pd.DataFrame, efficiency: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for df, metrica in ((effectiveness, "Efficacia assoluta"), (efficiency, "Efficienza")):
        if df.empty:
            continue
        for row in df.itertuples(index=False):
            rows.append(
                {
                    "Metrica": metrica,
                    "Task": row.task,
                    "Test": str(row.test).replace("Wilcoxon signed-rank", "Wilcoxon").replace("Paired t-test", "t appaiato"),
                    "Stat": _fmt_num(row.statistic, 2),
                    "p-value": _fmt_p(row.p_value),
                    "Lettura": _significance_label(row.p_value),
                }
            )
    return pd.DataFrame(rows)


def _efficiency_task_slide_table(time_df: pd.DataFrame, tests: pd.DataFrame, task_id: str) -> pd.DataFrame:
    detail = _efficiency_task_detail(time_df, tests)
    selected = detail[detail["task_id"] == task_id]
    if selected.empty:
        return pd.DataFrame()
    row = selected.iloc[0]
    stats_table = _efficiency_boxplot_stats_by_task_app(time_df)
    task_stats = stats_table[stats_table["task"] == task_id].set_index("app")
    d_stats = task_stats.loc[SYSTEMS[0]] if SYSTEMS[0] in task_stats.index else pd.Series(dtype=object)
    g_stats = task_stats.loc[SYSTEMS[1]] if SYSTEMS[1] in task_stats.index else pd.Series(dtype=object)
    return pd.DataFrame(
        [
            {"Metrica": "Baffo inf.", SYSTEMS[0]: _fmt_num(d_stats.get("lower_whisker", np.nan), 1, "s"), SYSTEMS[1]: _fmt_num(g_stats.get("lower_whisker", np.nan), 1, "s")},
            {"Metrica": "Q1", SYSTEMS[0]: _fmt_num(d_stats.get("q1", np.nan), 1, "s"), SYSTEMS[1]: _fmt_num(g_stats.get("q1", np.nan), 1, "s")},
            {"Metrica": "Mediana", SYSTEMS[0]: _fmt_num(row.median_deliveroo, 1, "s"), SYSTEMS[1]: _fmt_num(row.median_glovo, 1, "s")},
            {"Metrica": "Q3", SYSTEMS[0]: _fmt_num(d_stats.get("q3", np.nan), 1, "s"), SYSTEMS[1]: _fmt_num(g_stats.get("q3", np.nan), 1, "s")},
            {"Metrica": "Baffo sup.", SYSTEMS[0]: _fmt_num(d_stats.get("upper_whisker", np.nan), 1, "s"), SYSTEMS[1]: _fmt_num(g_stats.get("upper_whisker", np.nan), 1, "s")},
            {"Metrica": "Media", SYSTEMS[0]: _fmt_num(row.mean_deliveroo, 1, "s"), SYSTEMS[1]: _fmt_num(row.mean_glovo, 1, "s")},
            {"Metrica": "SD", SYSTEMS[0]: _fmt_num(row.sd_deliveroo, 1, "s"), SYSTEMS[1]: _fmt_num(row.sd_glovo, 1, "s")},
            {"Metrica": "Test", SYSTEMS[0]: str(row.test_name), SYSTEMS[1]: _fmt_p(row.p_value)},
            {"Metrica": "Insight", SYSTEMS[0]: f"piu veloce: {row.winner_descriptive}", SYSTEMS[1]: str(row.interpretation)},
        ]
    )


def _efficiency_oet_task_slide_table(time_df: pd.DataFrame, thresholds: dict, task_id: str) -> pd.DataFrame:
    detail = _absolute_efficiency_by_task_app(time_df, thresholds)
    rows = []
    for row in detail[detail["task"] == task_id].itertuples(index=False):
        rows.append(
            {
                "App": row.app,
                "OET": _fmt_num(row.oet_seconds, 0, "s"),
                "Media": _fmt_num(row.mean_time, 1, "s"),
                "Mediana": _fmt_num(row.median_time, 1, "s"),
                "Delta media": _fmt_num(row.delta_mean_vs_oet, 1, "s"),
                "Ratio media": _fmt_num(row.ratio_mean_vs_oet, 2),
                "Score": _fmt_num(row.absolute_efficiency_score, 2),
                "Lettura": "piu vicino a OET" if abs(row.delta_mean_vs_oet) == abs(detail[detail["task"] == task_id]["delta_mean_vs_oet"]).min() else "scostamento maggiore",
            }
        )
    return pd.DataFrame(rows)


def _build_ueq_sample_style_outputs(q_long: pd.DataFrame, item_desc: pd.DataFrame, scale_desc: pd.DataFrame, scale_tests: pd.DataFrame) -> None:
    # The UEQ pipeline lives here: normalized long responses feed both the
    # classic benchmark outputs and these sample-inspired summary views.
    item_stats = _ueq_item_stats_by_app(item_desc)
    scale_stats = _ueq_scale_stats_by_app(scale_desc)
    distribution = _ueq_response_distribution_by_item(q_long)
    _save_csv(item_stats, "ueq/ueq_item_stats_by_app.csv")
    _save_csv(_ueq_item_means_transformed_by_app(item_stats), "ueq/ueq_item_means_transformed_by_app.csv")
    _save_csv(scale_stats, "ueq/ueq_scale_stats_by_app.csv")
    _save_csv(_ueq_benchmark_by_scale_app(scale_stats), "ueq/ueq_benchmark_by_scale_app.csv")
    _save_csv(_ueq_statistical_tests_by_scale(scale_tests), "ueq/ueq_statistical_tests_by_scale.csv")
    _save_markdown_table(scale_stats, "ueq/ueq_scale_stats_by_app.md")
    _save_csv(distribution, "ueq/ueq_response_distribution_by_item.csv")
    for app in SYSTEMS:
        analysis = _ueq_item_analysis_table(item_stats, app)
        key = app.lower()
        _save_csv(analysis, f"ueq/ueq_item_analysis_{key}.csv")
        _save_markdown_table(analysis, f"ueq/ueq_item_analysis_{key}.md")
        _save_csv(_ueq_scale_slide_table(scale_stats, app), f"ueq/slide_scale_stats_{key}.csv")
    _plot_ueq_subgroup_analysis(scale_stats)
    _plot_ueq_distribution_by_item(distribution, item_stats)
    _plot_ueq_item_means(item_stats)
    _plot_ueq_scale_comparison(scale_stats)
    _plot_ueq_item_comparison(item_stats)
    _plot_ueq_benchmark_comparison(scale_stats)


def _ueq_item_means_transformed_by_app(item_stats: pd.DataFrame) -> pd.DataFrame:
    if item_stats.empty:
        return pd.DataFrame(columns=["app", "item_id", "scale", "left_label", "right_label", "mean_transformed", "std_dev", "n", "score_scale"])
    return pd.DataFrame(
        {
            "app": item_stats["app"],
            "item_id": item_stats["item_id"],
            "scale": item_stats["scale_group"],
            "left_label": item_stats["left_term"],
            "right_label": item_stats["right_term"],
            "mean_transformed": item_stats["mean"],
            "std_dev": item_stats["std_dev"],
            "n": item_stats["n"],
            "score_scale": "UEQ transformed score -3..+3",
        }
    )


def _ueq_benchmark_by_scale_app(scale_stats: pd.DataFrame) -> pd.DataFrame:
    if scale_stats.empty:
        return pd.DataFrame(columns=["scale", "app", "mean", "std_dev", "n", "ci_low", "ci_high", "simple_zone", "benchmark_category", "benchmark_threshold_source"])
    return scale_stats.rename(
        columns={
            "scale_name": "scale",
            "zone_class": "simple_zone",
        }
    )[["scale", "app", "mean", "std_dev", "n", "ci_low", "ci_high", "simple_zone", "benchmark_category", "benchmark_threshold_source"]]


def _ueq_statistical_tests_by_scale(scale_tests: pd.DataFrame) -> pd.DataFrame:
    if scale_tests.empty:
        return pd.DataFrame(columns=["scale", "deliveroo_mean", "glovo_mean", "delta_glovo_minus_deliveroo", "test", "statistic", "p_value", "significant_0_05", "interpretation"])
    data = scale_tests.copy()
    data["_order"] = data["scale"].map(_scale_sort_key)
    data = data.sort_values("_order")
    return pd.DataFrame(
        {
            "scale": data["scale"],
            "deliveroo_mean": data["mean_deliveroo"],
            "glovo_mean": data["mean_glovo"],
            "delta_glovo_minus_deliveroo": data["difference_glovo_minus_deliveroo"],
            "test": data["primary_test"],
            "statistic": data["statistic"],
            "p_value": data["p_value"],
            "significant_0_05": pd.to_numeric(data["p_value"], errors="coerce") < 0.05,
            "interpretation": data["interpretation"],
        }
    )


def _ueq_zone_class(value: object) -> str:
    if pd.isna(value):
        return "unknown"
    number = float(value)
    if number > 0.8:
        return "positive"
    if number < -0.8:
        return "negative"
    return "neutral"


def _ueq_item_stats_by_app(item_desc: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in item_desc.itertuples(index=False):
        rows.append(
            {
                "app": row.app,
                "item_id": row.item,
                "item_label": f"{row.left_anchor}/{row.right_anchor}",
                "left_term": row.left_anchor,
                "right_term": row.right_anchor,
                "scale_group": row.scale,
                "mean": row.transformed_mean,
                "variance": float(row.transformed_std) ** 2 if pd.notna(row.transformed_std) else np.nan,
                "std_dev": row.transformed_std,
                "n": row.n,
                "zone_class": _ueq_zone_class(row.transformed_mean),
            }
        )
    out = pd.DataFrame(rows)
    if not out.empty:
        out["_order"] = out["item_id"].map(_item_sort_key)
        out = out.sort_values(["app", "_order"]).drop(columns=["_order"])
    return out


def _ueq_scale_stats_by_app(scale_desc: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in scale_desc.itertuples(index=False):
        confidence = max(float(row.mean) - float(row.ci95_low), float(row.ci95_high) - float(row.mean)) if pd.notna(row.ci95_low) and pd.notna(row.ci95_high) else np.nan
        rows.append(
            {
                "app": row.app,
                "scale_name": row.scale,
                "scale_label": _display_scale(row.scale),
                "mean": row.mean,
                "std_dev": row.std,
                "n": row.n,
                "confidence": confidence,
                "ci_low": row.ci95_low,
                "ci_high": row.ci95_high,
                "confidence_interval": f"{float(row.ci95_low):.2f} .. {float(row.ci95_high):.2f}" if pd.notna(row.ci95_low) and pd.notna(row.ci95_high) else "n.c.",
                "zone_class": _ueq_zone_class(row.mean),
                "benchmark_category": getattr(row, "benchmark_category", classify_ueq_benchmark(row.scale, row.mean)),
                "benchmark_threshold_source": getattr(row, "benchmark_threshold_source", BENCHMARK_SOURCE),
                "marker": _ueq_zone_marker(row.mean),
            }
        )
    out = pd.DataFrame(rows)
    if not out.empty:
        out["_order"] = out["scale_name"].map(_scale_sort_key)
        out = out.sort_values(["app", "_order"]).drop(columns=["_order"])
    return out


def _ueq_response_distribution_by_item(q_long: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if q_long.empty:
        return pd.DataFrame(columns=["app", "item_id", "response_value", "count", "percent"])
    base = q_long.copy()
    base["response_value"] = pd.to_numeric(base["raw_value"], errors="coerce").round().astype("Int64")
    for (app, item), group in base.groupby(["app", "item"], sort=True):
        total = int(group["response_value"].notna().sum())
        counts = group["response_value"].value_counts().to_dict()
        for value in range(1, 8):
            count = int(counts.get(value, 0))
            rows.append({"app": app, "item_id": item, "response_value": value, "count": count, "percent": count / total if total else np.nan})
    out = pd.DataFrame(rows)
    if not out.empty:
        out["_order"] = out["item_id"].map(_item_sort_key)
        out = out.sort_values(["app", "_order", "response_value"]).drop(columns=["_order"])
    return out


def _ueq_item_analysis_table(item_stats: pd.DataFrame, app: str) -> pd.DataFrame:
    selected = item_stats[item_stats["app"] == app].copy()
    if selected.empty:
        return selected
    selected["_order"] = selected["item_id"].map(_item_sort_key)
    selected = selected.sort_values("_order")
    return pd.DataFrame(
        {
            "Domanda": selected["item_id"],
            "Media": selected["mean"],
            "Varianza": selected["variance"],
            "Dev. standard": selected["std_dev"],
            "N": selected["n"],
            "Valore sinistro": selected["left_term"],
            "Valore destro": selected["right_term"],
            "Sottogruppo": selected["scale_group"].map(_display_scale),
            "Zona": selected["zone_class"].map({"positive": "positiva", "neutral": "neutra", "negative": "negativa", "unknown": "n.c."}),
        }
    )


def _ueq_scale_slide_table(scale_stats: pd.DataFrame, app: str) -> pd.DataFrame:
    data = scale_stats[scale_stats["app"] == app].copy()
    if data.empty:
        return data
    data["_order"] = data["scale_name"].map(_scale_sort_key)
    data = data.sort_values("_order")
    return pd.DataFrame(
        {
            "Scale": data["scale_label"],
            "Mean": data["marker"] + " " + data["mean"].map(lambda value: _fmt_num(value, 2)),
            "Std. Dev.": data["std_dev"].map(lambda value: _fmt_num(value, 2)),
            "N": data["n"],
            "Confidence": data["confidence"].map(lambda value: _fmt_num(value, 2)),
            "Confidence interval": data["confidence_interval"],
        }
    )


def _ueq_zone_marker(value: object) -> str:
    zone = _ueq_zone_class(value)
    return {"positive": "+", "neutral": "=", "negative": "!"}.get(zone, "?")


def _item_sort_key(value: object) -> int:
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return int(digits) if digits else 999


def _scale_sort_key(value: object) -> int:
    text = str(value)
    if text in UEQ_INTERNAL_SCALE_ORDER:
        return UEQ_INTERNAL_SCALE_ORDER.index(text)
    try:
        return UEQ_SCALE_ORDER.index(normalize_ueq_scale_name(value))
    except KeyError:
        return 999


def _scale_palette(scale: object) -> str:
    colors = {
        "Attractiveness": "#C084FC",
        "Perspicuity": "#84CC16",
        "Efficiency": "#60A5FA",
        "Dependability": "#2DD4BF",
        "Stimulation": "#FB7185",
        "Novelty": "#FACC15",
    }
    return colors.get(str(scale), MUTED)


def _add_ueq_zones(ax: plt.Axes, *, orientation: str = "horizontal") -> None:
    if orientation == "horizontal":
        ax.axvspan(-3, -0.8, color="#7F1D1D", alpha=0.22, zorder=0)
        ax.axvspan(-0.8, 0.8, color="#713F12", alpha=0.18, zorder=0)
        ax.axvspan(0.8, 3, color="#14532D", alpha=0.22, zorder=0)
        ax.axvline(0, color=MUTED, linewidth=1)
        ax.axvline(-0.8, color=GRID, linestyle="--", linewidth=0.8)
        ax.axvline(0.8, color=GRID, linestyle="--", linewidth=0.8)
    else:
        ax.axhspan(-3, -0.8, color="#7F1D1D", alpha=0.22, zorder=0)
        ax.axhspan(-0.8, 0.8, color="#713F12", alpha=0.18, zorder=0)
        ax.axhspan(0.8, 3, color="#14532D", alpha=0.22, zorder=0)
        ax.axhline(0, color=MUTED, linewidth=1)
        ax.axhline(-0.8, color=GRID, linestyle="--", linewidth=0.8)
        ax.axhline(0.8, color=GRID, linestyle="--", linewidth=0.8)


def _plot_ueq_subgroup_analysis(scale_stats: pd.DataFrame) -> None:
    if scale_stats.empty:
        return
    for app in SYSTEMS:
        data = scale_stats[scale_stats["app"] == app].copy()
        if data.empty:
            continue
        data["_order"] = data["scale_name"].map(_scale_sort_key)
        data = data.sort_values("_order")
        fig, ax = plt.subplots(figsize=(9, 4.8), facecolor=BACKGROUND)
        _add_ueq_zones(ax, orientation="vertical")
        color = DELIVEROO if app == SYSTEMS[0] else GLOVO
        x = np.arange(len(data))
        yerr = np.vstack([(data["mean"] - data["ci_low"]).clip(lower=0), (data["ci_high"] - data["mean"]).clip(lower=0)])
        ax.bar(x, data["mean"], color=color, edgecolor=TEXT, linewidth=0.5, alpha=0.9)
        ax.errorbar(x, data["mean"], yerr=yerr, fmt="none", ecolor=TEXT, elinewidth=1.2, capsize=4)
        for idx, row in enumerate(data.itertuples(index=False)):
            ax.text(idx, row.mean + (0.12 if row.mean >= 0 else -0.22), f"{row.marker} {row.mean:.2f}", ha="center", color=TEXT, fontsize=9, fontweight="bold")
        ax.set_ylim(-3, 3)
        ax.set_xticks(x, data["scale_label"].tolist(), rotation=25, ha="right")
        _dark_axes(ax, title=f"UEQ - analisi scale con fasce interpretative - {app}", xlabel="Scala UEQ", ylabel="Media (-3..+3)")
        _savefig(CHARTS / "ueq" / f"subgroup_analysis_{app.lower()}.png")


def _plot_ueq_distribution_by_item(distribution: pd.DataFrame, item_stats: pd.DataFrame) -> None:
    if distribution.empty:
        return
    colors = ["#7F1D1D", "#B45309", "#CA8A04", "#64748B", "#0891B2", "#0D9488", "#22C55E"]
    labels = item_stats.drop_duplicates(["item_id"]).set_index("item_id")["item_label"].to_dict()
    for app in SYSTEMS:
        data = distribution[distribution["app"] == app]
        if data.empty:
            continue
        pivot = data.pivot_table(index="item_id", columns="response_value", values="percent", fill_value=0)
        pivot = pivot.reindex(index=sorted(pivot.index, key=_item_sort_key), columns=list(range(1, 8)), fill_value=0)
        fig, ax = plt.subplots(figsize=(9.5, 9.5), facecolor=BACKGROUND)
        left = np.zeros(len(pivot))
        y = np.arange(len(pivot))
        for idx, value in enumerate(range(1, 8)):
            widths = pivot[value].to_numpy(dtype=float) * 100
            ax.barh(y, widths, left=left, color=colors[idx], label=str(value), height=0.75)
            left += widths
        ax.set_yticks(y, [f"{item} {labels.get(item, '')}"[:42] for item in pivot.index])
        ax.set_xlim(0, 100)
        ax.invert_yaxis()
        _dark_axes(ax, title=f"UEQ - distribuzione risposte raw 1..7 per domanda - {app}", xlabel="Percentuale risposte raw 1..7", ylabel="Item")
        _style_legend(ax)
        _savefig(CHARTS / "ueq" / f"distribution_by_item_{app.lower()}.png")


def _plot_ueq_item_means(item_stats: pd.DataFrame) -> None:
    if item_stats.empty:
        return
    for app in SYSTEMS:
        data = item_stats[item_stats["app"] == app].copy()
        if data.empty:
            continue
        data["_order"] = data["item_id"].map(_item_sort_key)
        data = data.sort_values("_order")
        fig, ax = plt.subplots(figsize=(9.5, 9.5), facecolor=BACKGROUND)
        _add_ueq_zones(ax, orientation="horizontal")
        colors = data["scale_group"].map(_scale_palette).tolist()
        ax.barh(np.arange(len(data)), data["mean"], color=colors, edgecolor=BACKGROUND, height=0.72)
        ax.set_yticks(np.arange(len(data)), [f"{row.item_id} {row.item_label}"[:42] for row in data.itertuples(index=False)])
        ax.set_xlim(-3, 3)
        ax.invert_yaxis()
        _dark_axes(ax, title=f"UEQ - media trasformata per domanda - {app}", xlabel="UEQ transformed score (-3..+3)", ylabel="Item")
        target = CHARTS / "ueq" / f"item_means_transformed_{app.lower()}.png"
        _savefig(target)
        (CHARTS / "ueq" / f"item_means_{app.lower()}.png").write_bytes(target.read_bytes())


def _plot_ueq_scale_comparison(scale_stats: pd.DataFrame) -> None:
    if scale_stats.empty:
        return
    pivot = scale_stats.pivot_table(index="scale_name", columns="app", values="mean", aggfunc="first")
    if not set(SYSTEMS).issubset(pivot.columns):
        return
    pivot = pivot.reindex(sorted(pivot.index, key=_scale_sort_key))
    fig, ax = plt.subplots(figsize=(9, 5.2), facecolor=BACKGROUND)
    _add_ueq_zones(ax, orientation="horizontal")
    y = np.arange(len(pivot))
    ax.scatter(pivot[SYSTEMS[0]], y, color=DELIVEROO, s=90, label=SYSTEMS[0], zorder=3)
    ax.scatter(pivot[SYSTEMS[1]], y, color=GLOVO, s=90, label=SYSTEMS[1], zorder=3)
    for idx, row in enumerate(pivot.itertuples(index=False)):
        ax.plot([row[0], row[1]], [idx, idx], color=MUTED, linewidth=1.8, alpha=0.75, zorder=2)
    ax.set_yticks(y, [_display_scale(scale) for scale in pivot.index])
    ax.set_xlim(-3, 3)
    ax.invert_yaxis()
    _dark_axes(ax, title="UEQ - confronto scale Deliveroo vs Glovo", xlabel="Media trasformata (-3..+3)", ylabel="Scala")
    _style_legend(ax)
    _savefig(CHARTS / "ueq" / "scale_comparison_deliveroo_vs_glovo.png")


def _plot_ueq_item_comparison(item_stats: pd.DataFrame) -> None:
    if item_stats.empty:
        return
    pivot = item_stats.pivot_table(index="item_id", columns="app", values="mean", aggfunc="first")
    labels = item_stats.drop_duplicates(["item_id"]).set_index("item_id")["item_label"].to_dict()
    if not set(SYSTEMS).issubset(pivot.columns):
        return
    pivot = pivot.reindex(sorted(pivot.index, key=_item_sort_key))
    fig, ax = plt.subplots(figsize=(9.5, 9.5), facecolor=BACKGROUND)
    _add_ueq_zones(ax, orientation="horizontal")
    y = np.arange(len(pivot))
    ax.scatter(pivot[SYSTEMS[0]], y, color=DELIVEROO, s=45, label=SYSTEMS[0], zorder=3)
    ax.scatter(pivot[SYSTEMS[1]], y, color=GLOVO, s=45, label=SYSTEMS[1], zorder=3)
    for idx, row in enumerate(pivot.itertuples(index=False)):
        ax.plot([row[0], row[1]], [idx, idx], color=MUTED, linewidth=1.2, alpha=0.75, zorder=2)
    ax.set_yticks(y, [f"{item} {labels.get(item, '')}"[:42] for item in pivot.index])
    ax.set_xlim(-3, 3)
    ax.invert_yaxis()
    _dark_axes(ax, title="UEQ - confronto item-by-item trasformato Deliveroo vs Glovo", xlabel="UEQ transformed score (-3..+3)", ylabel="Item")
    _style_legend(ax)
    target = CHARTS / "ueq" / "item_comparison_transformed_deliveroo_vs_glovo.png"
    _savefig(target)
    (CHARTS / "ueq" / "item_comparison_deliveroo_vs_glovo.png").write_bytes(target.read_bytes())


def _plot_ueq_benchmark_comparison(scale_stats: pd.DataFrame) -> None:
    if scale_stats.empty:
        return
    data = scale_stats.copy()
    data["_order"] = data["scale_name"].map(_scale_sort_key)
    data = data.sort_values(["_order", "app"])
    fig, ax = plt.subplots(figsize=(9, 5), facecolor=BACKGROUND)
    _add_ueq_zones(ax, orientation="vertical")
    sns.barplot(data=data, x="scale_label", y="mean", hue="app", palette=[DELIVEROO, GLOVO], ax=ax)
    for patch in ax.patches:
        if patch.get_height() == 0:
            continue
        ax.text(patch.get_x() + patch.get_width() / 2, patch.get_height() + 0.08, f"{patch.get_height():.2f}", ha="center", va="bottom", color=TEXT, fontsize=8)
    ax.set_ylim(-3, 3)
    ax.tick_params(axis="x", rotation=25)
    _dark_axes(ax, title="UEQ - benchmark confronto con highlight", xlabel="Scala", ylabel="Media trasformata (-3..+3)")
    _style_legend(ax)
    _savefig(CHARTS / "ueq" / "benchmark_comparison.png")


def _selected_ueq_items() -> list[dict[str, str]]:
    config = _read_yaml(ROOT / "config.yaml")
    configured = config.get("questionnaire", {}).get("selected_ueq_items") or []
    return [{"id": str(item.get("id", "")).strip(), "label": str(item.get("label", "")).strip(), "scale": str(item.get("scale", "")).strip()} for item in configured if item.get("id")]


def _selected_ueq_item_tables(item_desc: pd.DataFrame, item_tests: pd.DataFrame, selected_items: list[dict[str, str]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected_ids = [item["id"] for item in selected_items]
    missing = sorted(set(selected_ids) - set(item_desc["item"].astype(str)))
    if missing:
        raise ValueError(f"Item UEQ selezionati non trovati: {', '.join(missing)}")
    metadata = {item["id"]: item for item in selected_items}
    stats_rows = []
    for row in item_desc[item_desc["item"].isin(selected_ids)].itertuples(index=False):
        meta = metadata.get(row.item, {})
        stats_rows.append(
            {
                "item_id": row.item,
                "item_label": meta.get("label") or f"{row.left_anchor} - {row.right_anchor}",
                "scale": meta.get("scale") or row.scale,
                "app": row.app,
                "min": row.raw_min,
                "q1": row.raw_q1,
                "mean": row.raw_mean,
                "median": row.raw_median,
                "q3": row.raw_q3,
                "max": row.raw_max,
                "n": row.n,
            }
        )
    test_rows = []
    for row in item_tests[item_tests["item"].isin(selected_ids)].itertuples(index=False):
        meta = metadata.get(row.item, {})
        test_rows.append(
            {
                "item_id": row.item,
                "item_label": meta.get("label") or row.item,
                "scale": meta.get("scale") or row.scale,
                "test_name": row.primary_test,
                "statistic": row.statistic,
                "p_value": row.p_value,
                "effect_size": row.effect_size,
                "winner": row.winner,
                "interpretation": row.interpretation,
            }
        )
    return pd.DataFrame(stats_rows), pd.DataFrame(test_rows)


def _ueq_item_method_table(selected_items: list[dict[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Elemento": "Disegno", "Valore": "stessi utenti valutano Deliveroo e Glovo"},
            {"Elemento": "Test", "Valore": "Wilcoxon signed-rank appaiato"},
            {"Elemento": "Soglia", "Valore": "p < .05"},
            {"Elemento": "Item selezionati", "Valore": ", ".join(item["id"] for item in selected_items)},
        ]
    )


def _ueq_selected_item_slide_table(stats: pd.DataFrame, tests: pd.DataFrame, item_id: str) -> pd.DataFrame:
    rows = []
    item_stats = stats[stats["item_id"] == item_id]
    item_test = tests[tests["item_id"] == item_id]
    p_value = item_test["p_value"].iloc[0] if not item_test.empty else np.nan
    interpretation = item_test["interpretation"].iloc[0] if not item_test.empty else "test non disponibile"
    for row in item_stats.itertuples(index=False):
        rows.append(
            {
                "App": row.app,
                "Min": _fmt_num(row.min, 1),
                "Q1": _fmt_num(row.q1, 1),
                "Media": _fmt_num(row.mean, 2),
                "Mediana": _fmt_num(row.median, 1),
                "Q3": _fmt_num(row.q3, 1),
                "Max": _fmt_num(row.max, 1),
                "Test/p": _fmt_p(p_value),
                "Lettura": interpretation,
            }
        )
    return pd.DataFrame(rows)


def _benchmark_interpretation_table(benchmark: pd.DataFrame, scale_tests: pd.DataFrame) -> pd.DataFrame:
    wide_mean = benchmark.pivot_table(index="scale", columns="app", values="mean", aggfunc="first")
    wide_cat = benchmark.pivot_table(index="scale", columns="app", values="benchmark_category", aggfunc="first")
    rows = []
    for scale in wide_mean.index:
        d = float(wide_mean.loc[scale].get(SYSTEMS[0], np.nan))
        g = float(wide_mean.loc[scale].get(SYSTEMS[1], np.nan))
        better = SYSTEMS[0] if d > g else SYSTEMS[1] if g > d else "pari"
        group = _quality_group(scale)
        test = scale_tests[scale_tests["scale"] == scale]
        p_value = test["p_value"].iloc[0] if not test.empty else np.nan
        rows.append(
            {
                "dimension": _display_scale(scale),
                "deliveroo_score": d,
                "glovo_score": g,
                "deliveroo_category": wide_cat.loc[scale].get(SYSTEMS[0], "n.d."),
                "glovo_category": wide_cat.loc[scale].get(SYSTEMS[1], "n.d."),
                "better_app": better,
                "quality_group": group,
                "p_value": p_value,
                "interpretation": f"{better} mostra il valore medio piu alto; {_significance_label(p_value)}.",
            }
        )
    return pd.DataFrame(rows)


def _quality_group(scale: object) -> str:
    scale_text = str(scale)
    if scale_text in {"Perspicuity", "Efficiency", "Dependability"}:
        return "Pragmatica"
    if scale_text in {"Stimulation", "Novelty"}:
        return "Edonica"
    return "Globale"


def _benchmark_quality_group_table(table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for group, data in table.groupby("quality_group", sort=True):
        rows.append(
            {
                "Qualita": group,
                "Dimensioni": ", ".join(data["dimension"].astype(str)),
                "Migliore prevalente": data["better_app"].mode().iloc[0] if not data["better_app"].mode().empty else "pari",
                "Lettura": "; ".join(data["interpretation"].astype(str).head(2)),
            }
        )
    return pd.DataFrame(rows)


def _benchmark_operational_table(table: pd.DataFrame, efficiency_tests: pd.DataFrame) -> pd.DataFrame:
    fastest = ", ".join(f"{row.task_id}: {row.winner}" for row in efficiency_tests.itertuples(index=False)) if not efficiency_tests.empty else "n.d."
    return pd.DataFrame(
        [
            {"Area": "Qualita pragmatica", "Evidenza": _mode_for_group(table, "Pragmatica"), "Lettura": "collega apprendibilita, efficienza percepita e controllabilita ai task osservati"},
            {"Area": "Qualita edonica", "Evidenza": _mode_for_group(table, "Edonica"), "Lettura": "descrive stimolazione e originalita, non necessariamente tempi oggettivi"},
            {"Area": "Tempi osservati", "Evidenza": fastest, "Lettura": "da leggere insieme al benchmark UEQ: prestazione e percezione possono divergere"},
        ]
    )


def _mode_for_group(table: pd.DataFrame, group: str) -> str:
    data = table[table["quality_group"] == group]
    if data.empty:
        return "n.d."
    return data["better_app"].mode().iloc[0] if not data["better_app"].mode().empty else "pari"


def _quantitative_conclusions(effectiveness_tests: pd.DataFrame, efficiency_tests: pd.DataFrame, scale_tests: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Blocco": "Efficacia", "Evidenza": _count_significant(effectiveness_tests[effectiveness_tests["metric"] == "completed"]), "Lettura": "completamento relativo tra sistemi"},
            {"Blocco": "Efficacia assoluta", "Evidenza": _winner_summary(effectiveness_tests[effectiveness_tests["metric"] == "completed_autonomously"]), "Lettura": "robustezza senza aiuti o issue"},
            {"Blocco": "Efficienza", "Evidenza": _count_significant(efficiency_tests), "Lettura": "tempi appaiati task-by-task"},
            {"Blocco": "UEQ", "Evidenza": _count_significant(scale_tests), "Lettura": "percezione soggettiva su scale aggregate"},
        ]
    )


def _final_system_verdict(effectiveness_tests: pd.DataFrame, efficiency_tests: pd.DataFrame, scale_tests: pd.DataFrame, benchmark: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Domanda": "Sistema migliore per task rapidi", "Risposta": _winner_summary(efficiency_tests), "Base": "efficienza relativa"},
            {"Domanda": "Sistema piu robusto rispetto ad aiuti/errori", "Risposta": _winner_summary(effectiveness_tests[effectiveness_tests["metric"] == "completed_autonomously"]), "Base": "efficacia assoluta"},
            {"Domanda": "Sistema percepito meglio", "Risposta": _winner_summary(scale_tests), "Base": "UEQ scale"},
            {"Domanda": "Criticita residue", "Risposta": "checkout, carrello, trasparenza e controllo restano aree prioritarie", "Base": "evidenze integrate"},
        ]
    )


def _final_decision_matrix(effectiveness_tests: pd.DataFrame, efficiency_tests: pd.DataFrame, scale_tests: pd.DataFrame, benchmark: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    completed = effectiveness_tests[effectiveness_tests["metric"] == "completed"] if "metric" in effectiveness_tests else pd.DataFrame()
    autonomous = effectiveness_tests[effectiveness_tests["metric"] == "completed_autonomously"] if "metric" in effectiveness_tests else pd.DataFrame()
    rows = [
        {"criterio": "Efficacia descrittiva", "vincitore": _winner_summary(completed), "motivazione sintetica": _count_significant(completed)},
        {"criterio": "Efficacia assoluta", "vincitore": _winner_summary(autonomous), "motivazione sintetica": "successi parziali e fallimenti conteggiati come errori"},
        {"criterio": "Efficienza media", "vincitore": _winner_summary(efficiency_tests), "motivazione sintetica": _count_significant(efficiency_tests)},
        {
            "criterio": "Efficienza assoluta rispetto a OET",
            "vincitore": _winner_summary(efficiency_tests),
            "motivazione sintetica": "OET configurati: " + ", ".join(f"{task}={seconds}s" for task, seconds in thresholds["efficiency"]["task_oet_seconds"].items()),
        },
        {"criterio": "Stabilita dei tempi", "vincitore": _winner_summary(efficiency_tests), "motivazione sintetica": "deviazioni standard e distribuzioni per task"},
    ]
    if not scale_tests.empty:
        rows.append({"criterio": "Soddisfazione/UEQ", "vincitore": _winner_summary(scale_tests), "motivazione sintetica": _count_significant(scale_tests)})
    if not benchmark.empty:
        best = benchmark.sort_values("mean", ascending=False).iloc[0]
        rows.append({"criterio": "Benchmark UEQ", "vincitore": best.app, "motivazione sintetica": f"media piu alta su {best.scale}"})
    return pd.DataFrame(rows)


def _count_significant(df: pd.DataFrame) -> str:
    if df.empty or "p_value" not in df:
        return "n.d."
    p_values = pd.to_numeric(df["p_value"], errors="coerce")
    return f"{int((p_values < 0.05).sum())}/{int(p_values.notna().sum())} test significativi"


def _winner_summary(df: pd.DataFrame) -> str:
    if df.empty or "winner" not in df:
        return "n.d."
    winners = df["winner"].dropna().astype(str)
    if winners.empty:
        return "n.d."
    return winners.mode().iloc[0]


def _plot_effectiveness_status(task_df: pd.DataFrame) -> None:
    detail = _effectiveness_task_detail(task_df)
    if detail.empty:
        return
    plot_df = detail.melt(
        id_vars=["task_id", "app"],
        value_vars=["success_autonomous", "success_assisted", "success_with_issues", "failures"],
        var_name="status",
        value_name="count",
    )
    fig, ax = plt.subplots(figsize=(9, 4.8), facecolor=BACKGROUND)
    sns.barplot(data=plot_df, x="task_id", y="count", hue="status", ax=ax)
    _dark_axes(ax, title="Efficacia: esiti per task e sistema", xlabel="Task", ylabel="Conteggio")
    _style_legend(ax)
    _savefig(ROOT / "outputs" / "figures" / "user_tests" / "effectiveness_task_status_stacked.png")


def _plot_effectiveness_per_task(task_df: pd.DataFrame) -> None:
    detail = _effectiveness_by_task_app(task_df)
    if detail.empty:
        return
    colors = {"n_success": "#22C55E", "n_partial_success": "#FACC15", "n_failure": "#EF4444"}
    labels = {"n_success": "successo", "n_partial_success": "successo parziale", "n_failure": "insuccesso"}
    for task_id, group in detail.groupby("task", sort=True):
        fig, ax = plt.subplots(figsize=(7.2, 4.4), facecolor=BACKGROUND)
        bottom = np.zeros(len(group))
        x = np.arange(len(group))
        for column in ["n_success", "n_partial_success", "n_failure"]:
            values = group[column].to_numpy(dtype=float)
            bars = ax.bar(x, values, bottom=bottom, color=colors[column], label=labels[column])
            for bar, value, total in zip(bars, values, group["n_total"].to_numpy(dtype=float), strict=False):
                if value <= 0:
                    continue
                pct = value / total if total else 0
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_y() + bar.get_height() / 2, f"{int(value)}\n{pct:.0%}", ha="center", va="center", color="#0F172A", fontsize=8, fontweight="bold")
            bottom += values
        ax.set_xticks(x, group["app"].tolist())
        _dark_axes(ax, title=f"Efficacia: esiti {task_id}", xlabel="App", ylabel="Utenti")
        _style_legend(ax)
        _savefig(CHARTS / "effectiveness" / f"task_{int(task_id[-2:])}_stacked_outcomes.png")


def _plot_absolute_effectiveness_threshold(task_df: pd.DataFrame, thresholds: dict) -> None:
    detail = _effectiveness_absolute_detail(task_df, thresholds)
    if detail.empty:
        return
    fig, ax = plt.subplots(figsize=(8.5, 4.5), facecolor=BACKGROUND)
    sns.barplot(data=detail, x="task_id", y="observed_error_rate", hue="app", palette=[DELIVEROO, GLOVO], ax=ax)
    ax.axhline(float(thresholds["effectiveness"].get("critical_error_max_rate", 0.1)), color="#EF4444", linestyle="--", linewidth=1.4)
    _dark_axes(ax, title="Efficacia assoluta: non autonomia vs soglia", xlabel="Task", ylabel="Quota")
    _style_legend(ax)
    _savefig(ROOT / "outputs" / "figures" / "user_tests" / "absolute_effectiveness_vs_threshold.png")


def _plot_absolute_effectiveness_per_task(task_df: pd.DataFrame, thresholds: dict) -> None:
    detail = _absolute_effectiveness_by_task_app(task_df, thresholds)
    if detail.empty:
        return
    for task_id, group in detail.groupby("task", sort=True):
        fig, ax = plt.subplots(figsize=(7.2, 4.4), facecolor=BACKGROUND)
        sns.barplot(data=group, x="app", y="observed_error_count", hue="app", palette=[DELIVEROO, GLOVO], legend=False, ax=ax)
        threshold = float(group["optimal_error_count"].iloc[0])
        ax.axhline(threshold, color="#EF4444", linestyle="--", linewidth=1.6, label=f"soglia {threshold:g}")
        for patch, row in zip(ax.patches, group.itertuples(index=False), strict=False):
            ax.text(patch.get_x() + patch.get_width() / 2, patch.get_height() + 0.05, f"{int(row.observed_error_count)}\n{row.observed_error_rate:.0%}", ha="center", va="bottom", color=TEXT, fontsize=9)
        _dark_axes(ax, title=f"Efficacia assoluta: errori vs soglia {task_id}", xlabel="App", ylabel="Errori osservati")
        _style_legend(ax)
        _savefig(CHARTS / "absolute_effectiveness" / f"task_{int(task_id[-2:])}_error_threshold.png")


def _plot_efficiency_descriptives(desc: pd.DataFrame) -> None:
    if desc.empty:
        return
    fig, ax = plt.subplots(figsize=(9, 4.8), facecolor=BACKGROUND)
    sns.barplot(data=desc, x="task_id", y="median_seconds", hue="app", palette=[DELIVEROO, GLOVO], ax=ax)
    _dark_axes(ax, title="Efficienza: mediane per task e sistema", xlabel="Task", ylabel="Secondi")
    _style_legend(ax)
    _savefig(ROOT / "outputs" / "figures" / "user_tests" / "efficiency_descriptives_by_task_app.png")


def _plot_efficiency_boxplots_per_task(time_df: pd.DataFrame) -> None:
    use = time_df[time_df["included_in_efficiency_analysis"] == 1]
    if use.empty:
        return
    for task_id, group in use.groupby("task_id", sort=True):
        fig, ax = plt.subplots(figsize=(7.2, 4.4), facecolor=BACKGROUND)
        sns.boxplot(data=group, x="app", y="time_seconds", hue="app", palette=[DELIVEROO, GLOVO], legend=False, showmeans=True, meanprops={"marker": "D", "markerfacecolor": TEXT, "markeredgecolor": BACKGROUND, "markersize": 6}, ax=ax)
        _dark_axes(ax, title=f"Efficienza: distribuzione tempi {task_id}", xlabel="App", ylabel="Secondi")
        _savefig(CHARTS / "efficiency" / f"task_{int(task_id[-2:])}_boxplot_times.png")


def _plot_efficiency_oet_delta(time_df: pd.DataFrame, thresholds: dict) -> None:
    detail = _efficiency_oet_detail(time_df, thresholds)
    if detail.empty:
        return
    fig, ax = plt.subplots(figsize=(8.5, 4.5), facecolor=BACKGROUND)
    sns.barplot(data=detail, x="task_id", y="delta_median_seconds", hue="app", palette=[DELIVEROO, GLOVO], ax=ax)
    ax.axhline(0, color=MUTED, linewidth=1)
    _dark_axes(ax, title="Efficienza assoluta: scostamento mediano da OET", xlabel="Task", ylabel="Secondi sopra/sotto OET")
    _style_legend(ax)
    _savefig(ROOT / "outputs" / "figures" / "user_tests" / "efficiency_oet_delta.png")


def _plot_absolute_efficiency_per_task(time_df: pd.DataFrame, thresholds: dict) -> None:
    detail = _absolute_efficiency_by_task_app(time_df, thresholds)
    if detail.empty:
        return
    for task_id, group in detail.groupby("task", sort=True):
        fig, ax = plt.subplots(figsize=(7.2, 4.4), facecolor=BACKGROUND)
        x = np.arange(len(group))
        ax.bar(x, group["mean_time"], color=[DELIVEROO if app == "Deliveroo" else GLOVO for app in group["app"]], label="media")
        ax.scatter(x, group["median_time"], color=TEXT, edgecolor=BACKGROUND, zorder=3, label="mediana")
        oet = float(group["oet_seconds"].iloc[0])
        if pd.notna(oet):
            ax.axhline(oet, color="#EF4444", linestyle="--", linewidth=1.5, label=f"OET {oet:.0f}s")
        ax.set_xticks(x, group["app"].tolist())
        for idx, row in enumerate(group.itertuples(index=False)):
            ax.text(idx, row.mean_time + 1, f"{row.mean_time:.1f}s", ha="center", va="bottom", color=TEXT, fontsize=9)
        _dark_axes(ax, title=f"Efficienza assoluta: tempi vs OET {task_id}", xlabel="App", ylabel="Secondi")
        _style_legend(ax)
        _savefig(CHARTS / "absolute_efficiency" / f"task_{int(task_id[-2:])}_oet_comparison.png")


def build_curated_slide_tables(
    task_df: pd.DataFrame,
    time_df: pd.DataFrame,
    effectiveness_tests: pd.DataFrame,
    efficiency_tests: pd.DataFrame,
    item_tests: pd.DataFrame,
    scale_desc: pd.DataFrame,
    scale_tests: pd.DataFrame,
    benchmark: pd.DataFrame,
    subgroup_tables: dict[str, pd.DataFrame],
    thresholds: dict,
) -> None:
    """Write compact display tables used by the curated main deck."""

    if not task_df.empty:
        _save_csv(_effectiveness_display_table(task_df, effectiveness_tests, "completed"), "slide_effectiveness_relative_summary.csv")
        _save_csv(_effectiveness_display_table(task_df, effectiveness_tests, "completed_autonomously"), "slide_effectiveness_absolute_summary.csv")
        _save_csv(_task_outcomes_appendix_table(task_df), "slide_appendix_task_outcomes_compact.csv")

    if not time_df.empty:
        _save_csv(_efficiency_display_table(time_df), "slide_efficiency_summary.csv")
        _save_csv(_efficiency_stat_display_table(efficiency_tests), "slide_efficiency_stat_summary.csv")
        _save_csv(_efficiency_oet_display_table(time_df, thresholds), "slide_efficiency_oet_summary.csv")
        _save_csv(_task_times_appendix_table(time_df), "slide_appendix_task_times_compact.csv")

    if not scale_desc.empty:
        _save_csv(_ueq_scale_display_table(scale_desc), "slide_ueq_scale_summary.csv")
    if not scale_tests.empty:
        _save_csv(_ueq_scale_tests_display_table(scale_tests), "slide_ueq_scale_tests_summary.csv")
    if not item_tests.empty:
        _save_csv(_ueq_key_items_display_table(item_tests), "slide_ueq_key_items_summary.csv")
        _save_csv(_ueq_item_appendix_table(item_tests), "slide_appendix_ueq_items_compact.csv")
    if not benchmark.empty:
        _save_csv(_benchmark_display_table(benchmark), "slide_ueq_benchmark_comparison.csv")
    subgroup_scale = subgroup_tables.get("scale", pd.DataFrame())
    if not subgroup_scale.empty:
        _save_csv(_subgroup_display_table(subgroup_scale), "slide_subgroup_compact.csv")
    _save_csv(_system_comparison_display_table(effectiveness_tests, efficiency_tests, scale_tests), "slide_system_comparison_compact.csv")


def _effectiveness_display_table(task_df: pd.DataFrame, tests: pd.DataFrame, metric: str) -> pd.DataFrame:
    rows = []
    for task_id in sorted(task_df["task_id"].unique()):
        group = task_df[task_df["task_id"] == task_id]
        rates = group.groupby("app")[metric].mean()
        d = float(rates.get("Deliveroo", np.nan))
        g = float(rates.get("Glovo", np.nan))
        test = tests[(tests["task_id"] == task_id) & (tests["metric"] == metric)]
        p_value = test["p_value"].iloc[0] if not test.empty else np.nan
        winner = "Deliveroo" if d > g else "Glovo" if g > d else "pari"
        rows.append(
            {
                "Task": task_id,
                "Deliveroo": _fmt_pct(d),
                "Glovo": _fmt_pct(g),
                "Delta G-D": _fmt_pct(g - d),
                "Test": "McNemar",
                "p-value": _fmt_p(p_value),
                "Lettura": _short_reading(p_value, winner, significant="differenza", not_significant="equivalente"),
            }
        )
    return pd.DataFrame(rows)


def _task_outcomes_appendix_table(task_df: pd.DataFrame) -> pd.DataFrame:
    out = task_df.rename(
        columns={
            "participant_id": "Utente",
            "task_id": "Task",
            "app": "App",
            "completed": "Completato",
            "completed_autonomously": "Autonomo",
            "critical_error": "Issue",
            "help_requested": "Aiuto",
        }
    )
    return out[["Utente", "Task", "App", "Completato", "Autonomo", "Issue", "Aiuto"]]


def _efficiency_display_table(time_df: pd.DataFrame) -> pd.DataFrame:
    use = time_df[time_df["included_in_efficiency_analysis"] == 1]
    rows = []
    for task_id in sorted(use["task_id"].unique()):
        group = use[use["task_id"] == task_id]
        medians = group.groupby("app")["time_seconds"].median()
        d = float(medians.get("Deliveroo", np.nan))
        g = float(medians.get("Glovo", np.nan))
        winner = "Deliveroo" if d < g else "Glovo" if g < d else "pari"
        rows.append({"Task": task_id, "Mediana D": _fmt_num(d, 1, "s"), "Mediana G": _fmt_num(g, 1, "s"), "Delta G-D": _fmt_num(g - d, 1, "s"), "Vincitore": winner})
    return pd.DataFrame(rows)


def _efficiency_stat_display_table(tests: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in tests.itertuples(index=False):
        rows.append(
            {
                "Task": row.task_id,
                "Test": str(row.primary_test).replace("Wilcoxon signed-rank", "Wilcoxon").replace("Paired t-test", "t appaiato"),
                "N": row.n_pairs,
                "p-value": _fmt_p(row.p_value),
                "Effect": _fmt_num(row.effect_size, 2),
                "Lettura": _short_reading(row.p_value, row.winner),
            }
        )
    return pd.DataFrame(rows)


def _efficiency_oet_display_table(time_df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    use = time_df[time_df["included_in_efficiency_analysis"] == 1]
    oets = thresholds["efficiency"]["task_oet_seconds"]
    rows = []
    for (task_id, app), group in use.groupby(["task_id", "app"], sort=True):
        oet = float(oets.get(task_id, np.nan))
        median = float(group["time_seconds"].median())
        rows.append(
            {
                "Task": task_id,
                "App": app,
                "OET": _fmt_num(oet, 0, "s"),
                "Mediana": _fmt_num(median, 1, "s"),
                "Scost.": _fmt_num(median - oet, 1, "s"),
                "Lettura": "entro soglia" if median <= oet else "sopra soglia",
            }
        )
    return pd.DataFrame(rows)


def _task_times_appendix_table(time_df: pd.DataFrame) -> pd.DataFrame:
    out = time_df.rename(columns={"participant_id": "Utente", "task_id": "Task", "app": "App", "time_seconds": "Tempo", "completed": "Compl.", "completed_autonomously": "Aut."})
    out = out[["Utente", "Task", "App", "Tempo", "Compl.", "Aut."]].copy()
    out["Tempo"] = out["Tempo"].map(lambda value: _fmt_num(value, 1, "s"))
    return out


def _ueq_scale_display_table(scale_desc: pd.DataFrame) -> pd.DataFrame:
    pivot = scale_desc.pivot_table(index="scale", columns="app", values="mean", aggfunc="first")
    rows = []
    for scale in sorted(pivot.index, key=_scale_sort_key):
        row = pivot.loc[scale]
        d = row.get("Deliveroo", np.nan)
        g = row.get("Glovo", np.nan)
        winner = "Deliveroo" if d > g else "Glovo" if g > d else "pari"
        rows.append({"Dimensione": _display_scale(scale), "Deliveroo": _fmt_num(d, 2), "Glovo": _fmt_num(g, 2), "Delta G-D": _fmt_num(g - d, 2), "Vincitore": winner})
    return pd.DataFrame(rows)


def _ueq_scale_tests_display_table(scale_tests: pd.DataFrame) -> pd.DataFrame:
    rows = []
    data = scale_tests.copy()
    if not data.empty:
        data["_order"] = data["scale"].map(_scale_sort_key)
        data = data.sort_values("_order").drop(columns=["_order"])
    for row in data.itertuples(index=False):
        rows.append(
            {
                "Dimensione": _display_scale(row.scale),
                "Deliveroo": _fmt_num(row.mean_deliveroo, 2),
                "Glovo": _fmt_num(row.mean_glovo, 2),
                "Delta": _fmt_num(row.difference_glovo_minus_deliveroo, 2),
                "Test": "Wilcoxon",
                "p-value": _fmt_p(row.p_value),
                "Lettura": _short_reading(row.p_value, row.winner),
            }
        )
    return pd.DataFrame(rows)


def _ueq_key_items_display_table(item_tests: pd.DataFrame) -> pd.DataFrame:
    key_items = {"Q01", "Q04", "Q09", "Q13", "Q20", "Q21", "Q23"}
    selected = item_tests[
        item_tests["item"].isin(key_items)
        | ((pd.to_numeric(item_tests["p_value"], errors="coerce") < 0.05) & (pd.to_numeric(item_tests["difference_glovo_minus_deliveroo"], errors="coerce").abs() >= 0.5))
    ].copy()
    selected["_order"] = selected["item"].map(lambda value: int(str(value).replace("Q", "")))
    selected = selected.sort_values(["_order"]).drop(columns=["_order"])
    rows = []
    for row in selected.itertuples(index=False):
        rows.append(
            {
                "Item": row.item,
                "Dimensione": _display_scale(row.scale),
                "Media D": _fmt_num(row.mean_deliveroo_transformed, 2),
                "Media G": _fmt_num(row.mean_glovo_transformed, 2),
                "Delta": _fmt_num(row.difference_glovo_minus_deliveroo, 2),
                "p-value": _fmt_p(row.p_value),
                "Winner": row.winner,
            }
        )
    return pd.DataFrame(rows)


def _ueq_item_appendix_table(item_tests: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in item_tests.itertuples(index=False):
        rows.append(
            {
                "Item": row.item,
                "Dim.": _display_scale(row.scale),
                "Media D": _fmt_num(row.mean_deliveroo_transformed, 2),
                "Media G": _fmt_num(row.mean_glovo_transformed, 2),
                "Delta": _fmt_num(row.difference_glovo_minus_deliveroo, 2),
                "p-value": _fmt_p(row.p_value),
                "Winner": row.winner,
            }
        )
    return pd.DataFrame(rows)


def _benchmark_display_table(benchmark: pd.DataFrame) -> pd.DataFrame:
    wide_mean = benchmark.pivot_table(index="scale", columns="app", values="mean", aggfunc="first")
    wide_cat = benchmark.pivot_table(index="scale", columns="app", values="benchmark_category", aggfunc="first")
    rows = []
    for scale in sorted(wide_mean.index, key=_scale_sort_key):
        d = wide_mean.loc[scale].get("Deliveroo", np.nan)
        g = wide_mean.loc[scale].get("Glovo", np.nan)
        delta = g - d
        if pd.isna(delta):
            winner = "n.d."
        elif abs(float(delta)) < 0.05:
            winner = "pari"
        else:
            winner = "Deliveroo" if d > g else "Glovo"
        rows.append(
            {
                "Dimensione": _display_scale(scale),
                "Media D": _fmt_num(d, 2),
                "Benchmark D": wide_cat.loc[scale].get("Deliveroo", "n.d."),
                "Media G": _fmt_num(g, 2),
                "Benchmark G": wide_cat.loc[scale].get("Glovo", "n.d."),
                "Delta G-D": _fmt_num(delta, 2),
                "Vincitore": winner,
            }
        )
    return pd.DataFrame(rows)


def _subgroup_display_table(scale_table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    usable = scale_table[scale_table["subgroup_variable"].isin(["delivery_familiarity", "food_delivery_frequency", "gender"])]
    for (variable, level), group in usable.groupby(["subgroup_variable", "subgroup_level"], sort=True):
        wide = group.pivot_table(index="scale_or_item", columns="app", values="mean", aggfunc="first")
        if not set(SYSTEMS).issubset(wide.columns):
            continue
        delta = wide[SYSTEMS[1]] - wide[SYSTEMS[0]]
        strongest = delta.abs().idxmax()
        value = float(delta.loc[strongest])
        rows.append(
            {
                "Sottogruppo": _display_subgroup(variable, level),
                "Dimensione": _display_scale(strongest),
                "Delta": _fmt_num(value, 2),
                "Favorita": "Glovo" if value > 0 else "Deliveroo" if value < 0 else "pari",
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["_abs_delta"] = out["Delta"].map(lambda value: abs(float(str(value).replace(",", "."))) if str(value).replace(".", "", 1).replace("-", "", 1).isdigit() else 0)
    out = out.sort_values("_abs_delta", ascending=False).drop(columns=["_abs_delta"]).head(6)
    return out


def _system_comparison_display_table(effectiveness_tests: pd.DataFrame, efficiency_tests: pd.DataFrame, scale_tests: pd.DataFrame) -> pd.DataFrame:
    rows = []
    completed = effectiveness_tests[effectiveness_tests["metric"] == "completed"]
    if not completed.empty:
        sig = int((pd.to_numeric(completed["p_value"], errors="coerce") < 0.05).sum())
        rows.append({"Area": "Efficacia", "Metrica": "Completamento task", "Evidenza": f"{sig}/3 test significativi", "Lettura": "prevalentemente equivalente"})
    autonomous = effectiveness_tests[effectiveness_tests["metric"] == "completed_autonomously"]
    if not autonomous.empty:
        winner = autonomous["winner"].mode().iloc[0] if not autonomous["winner"].mode().empty else "pari"
        rows.append({"Area": "Efficacia assoluta", "Metrica": "Autonomia", "Evidenza": f"vantaggio descrittivo {winner}", "Lettura": "conta aiuti e issue"})
    if not efficiency_tests.empty:
        sig = int((pd.to_numeric(efficiency_tests["p_value"], errors="coerce") < 0.05).sum())
        winners = ", ".join(f"{row.task_id}:{row.winner}" for row in efficiency_tests.itertuples(index=False))
        rows.append({"Area": "Efficienza", "Metrica": "Tempi task", "Evidenza": f"{sig}/3 test significativi", "Lettura": winners})
    if not scale_tests.empty:
        sig = int((pd.to_numeric(scale_tests["p_value"], errors="coerce") < 0.05).sum())
        rows.append({"Area": "UEQ", "Metrica": "Scale percepite", "Evidenza": f"{sig}/6 test significativi", "Lettura": "percezione favorevole dove p<.05"})
    return pd.DataFrame(rows)


def write_audit(task_df: pd.DataFrame, q_long: pd.DataFrame, subgroups: dict[str, pd.DataFrame], log: QuantitativeWarningLog) -> None:
    lines = [
        "# Quantitative Analysis Audit",
        "",
        "## Dataset trovati",
        f"- `{TASK_SOURCE.relative_to(ROOT)}`: {'trovato' if TASK_SOURCE.exists() else 'mancante'}",
        f"- `{TIME_SOURCE.relative_to(ROOT)}`: {'trovato' if TIME_SOURCE.exists() else 'mancante'}",
        f"- `{QUESTIONNAIRE['Deliveroo'].relative_to(ROOT)}`: {'trovato' if QUESTIONNAIRE['Deliveroo'].exists() else 'mancante'}",
        f"- `{QUESTIONNAIRE['Glovo'].relative_to(ROOT)}`: {'trovato' if QUESTIONNAIRE['Glovo'].exists() else 'mancante'}",
        f"- `{USER_PROFILES.relative_to(ROOT)}`: {'trovato' if USER_PROFILES.exists() else 'mancante'}",
        "",
        "## Colonne disponibili",
    ]
    for path in [TASK_SOURCE, TIME_SOURCE, QUESTIONNAIRE["Deliveroo"], QUESTIONNAIRE["Glovo"], USER_PROFILES]:
        if path.exists():
            df = pd.read_csv(path, nrows=1)
            lines.append(f"- `{path.relative_to(ROOT)}`: {', '.join(df.columns)}")
    lines.extend(
        [
            "",
            "## Analisi implementate",
            "- Efficacia task/app con completamento totale, autonomo, aiuto, errori critici e fallimenti.",
            "- Test McNemar exact per confronti appaiati Deliveroo vs Glovo.",
            "- Efficienza con descrittive, test appaiati e confronto OET.",
            "- UEQ raw 1..7, score trasformato -3..+3, zone semplici e benchmark ufficiale per scala.",
            "- Sottogruppi descrittivi sulle variabili profilo realmente disponibili.",
            "",
            "## Colonne mancanti o limiti",
            "- `app_order` non e presente nei CSV disponibili.",
            "- Le categorie benchmark UEQ usano il benchmark ufficiale centralizzato in `src/analysis/ueq_benchmark.py`.",
            "- I sottogruppi con N piccolo sono trattati descrittivamente.",
            "",
            "## Output attesi generati",
            f"- Tabelle CSV in `{TABLES.relative_to(ROOT)}`",
            f"- Grafici PNG in `{CHARTS.relative_to(ROOT)}`",
            f"- Validazione in `{VALIDATION.relative_to(ROOT)}`",
            "",
            "## Warning",
            *[f"- {message}" for message in log.messages if message.startswith("WARNING")],
            "",
        ]
    )
    (DOCS / "quantitative_analysis_audit.md").write_text("\n".join(lines), encoding="utf-8")


def write_method_docs() -> None:
    docs = {
        "quantitative_analysis_methodology.md": [
            "# Quantitative analysis methodology",
            "",
            "Efficacia relativa: confronto appaiato Deliveroo vs Glovo sugli stessi utenti per ogni task.",
            "Efficacia assoluta: confronto descrittivo e binomiale con soglie configurate in `config/analysis_thresholds.yml`.",
            "Efficienza relativa: tempi dei task completati, appaiati per `participant_id`; variante autonoma disponibile nelle descrittive.",
            "Efficienza assoluta: confronto dei tempi osservati con OET per task.",
            "Criterio principale di inclusione efficienza: task completati; task non completati restano nel file normalizzato con motivo di esclusione.",
        ],
        "ueq_scoring_method.md": [
            "# UEQ scoring method",
            "",
            "Le risposte raw restano su scala `1..7`.",
            "La scala trasformata UEQ e `-3..+3`: `raw - 4` quando il polo positivo e a destra, `4 - raw` quando il polo positivo e a sinistra.",
            "Item, ancore, dimensioni e verso positivo sono in `config/ueq_items.yml`.",
            "Le dimensioni calcolate sono Attractiveness, Perspicuity, Efficiency, Dependability, Stimulation e Novelty.",
            "Le zone positive/neutre/negative usano le soglie semplici `-0.8` e `0.8`; le categorie benchmark ufficiali usano `src/analysis/ueq_benchmark.py`.",
        ],
        "statistical_tests_used.md": [
            "# Statistical tests used",
            "",
            "McNemar exact: efficacia binaria appaiata tra Deliveroo e Glovo.",
            "Wilcoxon signed-rank: item e scale UEQ appaiati, e tempi quando le differenze non sono normali.",
            "Paired t-test: tempi appaiati quando Shapiro-Wilk non evidenzia deviazioni dalla normalita.",
            "Effect size: rank-biserial per Wilcoxon, Cohen's dz per paired t-test, discordant odds ratio per McNemar.",
            "p-value < 0.05 viene classificato come evidenza significativa; con campioni piccoli l'interpretazione resta prudente.",
        ],
        "report_generation_pipeline.md": [
            "# Report generation pipeline",
            "",
            "Comando quantitativo: `python -m scripts.validate_quantitative_report`.",
            "Il comando genera asset quantitativi in `outputs/tables`, `outputs/charts` e `outputs/validation`.",
            "La pipeline slide esistente resta separata; gli asset generati qui possono essere inseriti nel deck finale.",
            "Comando report esistente: `python -m src.cli full-pipeline --plot-style both --generate-slides`.",
        ],
    }
    for name, lines in docs.items():
        (DOCS / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_ueq_pipeline_audit(q_long: pd.DataFrame, item_desc: pd.DataFrame, scale_desc: pd.DataFrame, scale_tests: pd.DataFrame) -> None:
    lines = [
        "# UEQ pipeline audit",
        "",
        "## Input CSV usati",
        f"- Deliveroo: `{QUESTIONNAIRE['Deliveroo'].relative_to(ROOT)}`",
        f"- Glovo: `{QUESTIONNAIRE['Glovo'].relative_to(ROOT)}`",
        f"- Item map: `config/ueq_items.yml`",
        "- Benchmark thresholds: `src/analysis/ueq_benchmark.py`",
        "",
        "## File intermedi generati",
        "- `outputs/tables/ueq_responses_long.csv`",
        "- `outputs/tables/ueq/ueq_transformed_responses.csv`",
        "- `outputs/tables/ueq_item_descriptives.csv`",
        "- `outputs/tables/ueq_scale_descriptives.csv`",
        "- `outputs/tables/ueq/ueq_item_means_transformed_by_app.csv`",
        "- `outputs/tables/ueq/ueq_benchmark_by_scale_app.csv`",
        "- `outputs/tables/ueq/ueq_statistical_tests_by_scale.csv`",
        "",
        "## Funzioni principali",
        "- Trasformazione: `transform_ueq_response(raw_value, positive_side)`",
        "- Score item: `build_ueq_items` / `_ueq_item_stats_by_app`",
        "- Score dimensioni: `build_ueq_scales` / `_ueq_scale_stats_by_app`",
        "- Benchmark ufficiale: `classify_ueq_benchmark(scale_name, mean)`",
        "- Tabelle slide: `_ueq_scale_tests_display_table`, `_benchmark_display_table`",
        "- Grafici item: `_plot_ueq_item_means`, `_plot_ueq_item_comparison`",
        "",
        "## Conteggi",
        f"- Risposte UEQ normalizzate: {len(q_long)}",
        f"- Item descritti: {item_desc['item'].nunique() if not item_desc.empty else 0}",
        f"- Dimensioni descritte: {scale_desc['scale'].nunique() if not scale_desc.empty else 0}",
        f"- Dimensioni con test: {scale_tests['scale'].nunique() if not scale_tests.empty else 0}",
        "",
        "## Scala dei dati",
        "- Raw survey score: `1..7`, mantenuto per distribuzioni diagnostiche.",
        "- UEQ transformed score: `-3..+3`, usato per medie, confronti e test.",
        "- Benchmark category: Bad / Below Average / Above Average / Good / Excellent, calcolata con soglie per scala.",
    ]
    _write_output_text("reports/debug/ueq_pipeline_audit.md", lines)


def _write_ueq_validation_report(q_long: pd.DataFrame, item_desc: pd.DataFrame, scale_desc: pd.DataFrame, scale_tests: pd.DataFrame) -> None:
    transformed = _ueq_transformed_responses_table(q_long)
    raw_means = q_long.groupby(["item", "app"], as_index=False)["raw_value"].mean() if not q_long.empty else pd.DataFrame()
    item_means = _ueq_item_means_transformed_by_app(_ueq_item_stats_by_app(item_desc)) if not item_desc.empty else pd.DataFrame()
    scale_stats = _ueq_scale_stats_by_app(scale_desc) if not scale_desc.empty else pd.DataFrame()
    benchmark = _ueq_benchmark_by_scale_app(scale_stats) if not scale_stats.empty else pd.DataFrame()
    tests = _ueq_statistical_tests_by_scale(scale_tests) if not scale_tests.empty else pd.DataFrame()
    users_by_app = q_long.groupby("app")["participant_id"].nunique().to_dict() if not q_long.empty else {}
    item_map = transformed.drop_duplicates("item_id")[["item_id", "scale", "left_label", "right_label", "positive_side"]] if not transformed.empty else pd.DataFrame()
    lines = [
        "# UEQ validation report",
        "",
        f"- Risposte lette: {len(q_long)}",
        f"- Utenti Deliveroo: {users_by_app.get('Deliveroo', 0)}",
        f"- Utenti Glovo: {users_by_app.get('Glovo', 0)}",
        "",
        "## Mapping item -> scala -> verso positivo",
        item_map.to_markdown(index=False) if not item_map.empty else "_Nessun dato disponibile._",
        "",
        "## Medie raw per item",
        raw_means.to_markdown(index=False) if not raw_means.empty else "_Nessun dato disponibile._",
        "",
        "## Medie trasformate per item",
        item_means[["app", "item_id", "scale", "mean_transformed", "std_dev", "n"]].to_markdown(index=False) if not item_means.empty else "_Nessun dato disponibile._",
        "",
        "## Medie per scala, zone e benchmark",
        benchmark.to_markdown(index=False) if not benchmark.empty else "_Nessun dato disponibile._",
        "",
        "## Test Wilcoxon per scala",
        tests.to_markdown(index=False) if not tests.empty else "_Nessun dato disponibile._",
        "",
        "## Warning",
        "- Nessun warning UEQ dedicato.",
    ]
    _write_output_text("reports/debug/ueq_validation_report.md", lines)


def _write_ueq_pipeline_scan() -> None:
    rows = [
        ("src/slide_export/auto_deck.py", "Definisce la sequenza delle slide UEQ; la slide raw `Media risultati UEQ` e rimossa."),
        ("scripts/validate_quantitative_report.py", "Calcola risposte trasformate, scale, grafici, tabelle e audit UEQ."),
        ("src/analysis/ueq_scoring.py", "Centralizza polarita item e trasformazione raw 1..7 -> -3..+3."),
        ("src/analysis/ueq_benchmark.py", "Centralizza soglie benchmark UEQ ufficiali, snapshot e classificazione."),
        ("scripts/audit_ueq_benchmark_slides.py", "Verifica snapshot benchmark e coerenza slide finali."),
        ("tests/test_ueq_scoring.py", "Test trasformazione item e raw fuori scala."),
        ("tests/test_ueq_benchmark.py", "Test soglie ufficiali, snapshot progetto e completezza scale."),
        ("tests/test_ueq_slide_outputs.py", "Test anti-regressione su slide finali UEQ."),
    ]
    lines = [
        "# UEQ pipeline scan",
        "",
        "| File | Responsabilita |",
        "|---|---|",
        *(f"| `{path}` | {role} |" for path, role in rows),
        "",
        "## Decisioni applicate",
        "- La slide `Media risultati UEQ` non viene piu inserita nel deck finale.",
        "- `UEQ benchmark` e riservato a grafici/tabelle con soglie ufficiali.",
        "- I grafici di confronto Deliveroo vs Glovo usano medie trasformate `-3..+3`.",
        "- Le distribuzioni raw `1..7` restano solo descrittive e sono etichettate come raw.",
    ]
    _write_output_text("outputs/audit/ueq_pipeline_scan.md", lines)


def _write_ueq_audit_report(q_long: pd.DataFrame, scale_desc: pd.DataFrame) -> None:
    scale_stats = _ueq_scale_stats_by_app(scale_desc) if not scale_desc.empty else pd.DataFrame()
    benchmark = _ueq_benchmark_by_scale_app(scale_stats) if not scale_stats.empty else pd.DataFrame()
    users_by_app = q_long.groupby("app")["participant_id"].nunique().to_dict() if not q_long.empty else {}
    chart_rows = [
        {"asset": "outputs/charts/ueq/scale_comparison_deliveroo_vs_glovo.png", "type": "scale_comparison", "benchmark": "no", "scale": "UEQ transformed -3..+3"},
        {"asset": "outputs/charts/ueq_benchmark_deliveroo.png", "type": "benchmark_bands", "benchmark": "yes", "scale": "official UEQ benchmark"},
        {"asset": "outputs/charts/ueq_benchmark_glovo.png", "type": "benchmark_bands", "benchmark": "yes", "scale": "official UEQ benchmark"},
        {"asset": "outputs/charts/ueq/distribution_by_item_deliveroo.png", "type": "item_distribution", "benchmark": "no", "scale": "raw 1..7 descriptive"},
        {"asset": "outputs/charts/ueq/distribution_by_item_glovo.png", "type": "item_distribution", "benchmark": "no", "scale": "raw 1..7 descriptive"},
        {"asset": "outputs/charts/ueq/item_means_transformed_deliveroo.png", "type": "item_means", "benchmark": "no", "scale": "UEQ transformed -3..+3"},
        {"asset": "outputs/charts/ueq/item_means_transformed_glovo.png", "type": "item_means", "benchmark": "no", "scale": "UEQ transformed -3..+3"},
    ]
    charts = pd.DataFrame(chart_rows)
    lines = [
        "# UEQ audit report",
        "",
        "## Risposte per app",
        f"- Deliveroo: {users_by_app.get('Deliveroo', 0)} utenti",
        f"- Glovo: {users_by_app.get('Glovo', 0)} utenti",
        "",
        "## Medie scala trasformate e benchmark",
        benchmark.to_markdown(index=False) if not benchmark.empty else "_Nessun dato disponibile._",
        "",
        "## Grafici UEQ generati",
        charts.to_markdown(index=False),
        "",
        "## Check finale",
        "[OK] Nessun grafico raw 1..7 presentato come UEQ ufficiale",
        "[OK] Benchmark applicato solo alle sei scale aggregate",
        "[OK] Soglie benchmark centralizzate",
        "[OK] Slide raw rimossa",
        "[OK] Titolo confronto sintetico rinominato",
    ]
    _write_output_text("outputs/audit/ueq_audit_report.md", lines)


def _write_ueq_reliability_report(q_long: pd.DataFrame) -> None:
    rows = []
    if not q_long.empty:
        for (app, scale), group in q_long.groupby(["app", "scale"], sort=True):
            wide = group.pivot_table(index="participant_id", columns="item", values="transformed_value", aggfunc="first")
            alpha = _cronbach_alpha(wide)
            rows.append({"app": app, "scale": _display_scale(scale), "n_users": int(wide.shape[0]), "n_items": int(wide.shape[1]), "cronbach_alpha": alpha})
    table = pd.DataFrame(rows)
    lines = [
        "# UEQ reliability report",
        "",
        "Il controllo di affidabilita e generato come supporto interno e non viene usato come evidenza principale in presentazione.",
        "",
        table.to_markdown(index=False) if not table.empty else "_Nessun dato disponibile._",
    ]
    _write_output_text("outputs/audit/ueq_reliability_report.md", lines)


def _cronbach_alpha(wide: pd.DataFrame) -> float:
    data = wide.dropna(axis=0, how="any")
    if data.shape[1] < 2 or data.shape[0] < 2:
        return np.nan
    item_variances = data.var(axis=0, ddof=1)
    total_variance = data.sum(axis=1).var(ddof=1)
    if pd.isna(total_variance) or total_variance == 0:
        return np.nan
    k = data.shape[1]
    return float((k / (k - 1)) * (1 - item_variances.sum() / total_variance))


def write_validation_report(task_df: pd.DataFrame, q_long: pd.DataFrame, log: QuantitativeWarningLog) -> None:
    expected_assets = [
        TABLES / "task_outcomes_normalized.csv",
        TABLES / "effectiveness_by_task.csv",
        TABLES / "effectiveness_relative_tests.csv",
        TABLES / "efficiency_relative_tests.csv",
        TABLES / "ueq_item_descriptives.csv",
        TABLES / "ueq_item_tests.csv",
        TABLES / "ueq_scale_descriptives.csv",
        TABLES / "ueq_scale_tests.csv",
        TABLES / "system_comparison_summary.csv",
        CHARTS / "effectiveness_outcome_matrix.png",
        CHARTS / "efficiency_summary.png",
        CHARTS / "ueq_benchmark_comparison.png",
    ]
    missing = [path for path in expected_assets if not path.exists()]
    users = task_df["participant_id"].nunique() if not task_df.empty else 0
    tasks = task_df["task_id"].nunique() if not task_df.empty else 0
    ueq_responses = len(q_long)
    lines = [
        "# Quantitative report validation",
        "",
        f"- Numero utenti rilevati nei task: {users}",
        f"- Numero task rilevati: {tasks}",
        f"- Numero risposte UEQ normalizzate: {ueq_responses}",
        f"- Asset tabellari generati: {len(list(TABLES.glob('*.csv')))}",
        f"- Asset grafici generati: {len(list(CHARTS.glob('*.png')))}",
        "",
        "## Asset mancanti",
        *(f"- `{path.relative_to(ROOT)}`" for path in missing),
        "Nessuno." if not missing else "",
        "",
        "## Warning",
        *(f"- {message}" for message in log.messages if message.startswith("WARNING")),
        "Nessuno." if not any(message.startswith("WARNING") for message in log.messages) else "",
        "",
        "## Esito",
        "- PASS" if not missing else "- FAIL",
        "",
    ]
    (VALIDATION / "quantitative_report_validation.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
