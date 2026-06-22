from __future__ import annotations

import sys
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


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)
    VALIDATION.mkdir(parents=True, exist_ok=True)
    log = QuantitativeWarningLog()

    thresholds = _read_yaml(ROOT / "config" / "analysis_thresholds.yml")
    ueq_items = _read_yaml(ROOT / "config" / "ueq_items.yml")["items"]
    benchmark_thresholds = _read_yaml(ROOT / "config" / "ueq_benchmark_thresholds.yml")["categories"]

    task_df = build_task_outcomes(log)
    time_df = build_task_times(task_df, log)
    effectiveness_by_task = build_effectiveness_tables(task_df, thresholds, log)
    efficiency_relative = build_efficiency_tables(time_df, thresholds, log)

    q_long = build_ueq_long(ueq_items, log)
    item_desc, item_tests = build_ueq_items(q_long, ueq_items, log)
    scale_scores, scale_desc, scale_tests, benchmark = build_ueq_scales(q_long, benchmark_thresholds, log)
    subgroup_tables = build_subgroups(scale_scores, q_long, task_df, log)
    comparison = build_system_comparison(effectiveness_by_task, efficiency_relative, item_tests, scale_tests, benchmark)
    build_curated_slide_tables(task_df, time_df, effectiveness_by_task, efficiency_relative, item_tests, scale_desc, scale_tests, benchmark, subgroup_tables, thresholds)

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
        completed = outcome in {"success", "assisted_success", "partial_success", "success_with_issue"}
        critical = bool(error_flag or errors_count > 0 or outcome in {"failure", "timeout"})
        autonomous = bool(completed and outcome == "success" and assistance in {"", "none"} and help_count == 0 and not critical)
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
        task_df[["participant_id", "app", "task_id", "completed", "completed_autonomously"]],
        on=["participant_id", "app", "task_id"],
        how="left",
    )
    merged["completed"] = merged["completed"].fillna(merged["success"]).astype(int)
    merged["completed_autonomously"] = merged["completed_autonomously"].fillna((merged["success"]) & (merged["errors_count"] == 0) & (merged["help_requests"] == 0)).astype(int)
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


def transform_ueq_raw_to_standard(raw_value: float, item_config: dict) -> float:
    if pd.isna(raw_value):
        return np.nan
    raw = float(raw_value)
    return 4.0 - raw if item_config.get("reversed") else raw - 4.0


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
                        "raw_value": raw,
                        "transformed_value": transform_ueq_raw_to_standard(raw, cfg),
                    }
                )
    out = pd.DataFrame(rows)
    _save_csv(out, "ueq_responses_long.csv")
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


def build_ueq_scales(df: pd.DataFrame, benchmark_thresholds: dict, log: QuantitativeWarningLog):
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
                "benchmark_category": benchmark_category(mean, benchmark_thresholds),
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

    benchmark = desc[["scale", "app", "mean", "benchmark_category"]].copy()
    _save_csv(benchmark, "ueq_benchmark_summary.csv")
    plot_ueq_benchmarks(desc)
    return scores, desc, tests, benchmark


def benchmark_category(value: float, thresholds: dict) -> str:
    for name, threshold in sorted(thresholds.items(), key=lambda item: item[1], reverse=True):
        if value >= float(threshold):
            return name
    return "Bad"


def plot_ueq_benchmarks(desc: pd.DataFrame) -> None:
    for app in SYSTEMS:
        data = desc[desc["app"] == app]
        fig, ax = plt.subplots(figsize=(8, 4), facecolor=BACKGROUND)
        sns.barplot(data=data, x="scale", y="mean", color=DELIVEROO if app == "Deliveroo" else GLOVO, ax=ax)
        ax.axhline(0, color=MUTED, linewidth=1)
        ax.set_ylim(-3, 3)
        ax.tick_params(axis="x", rotation=30)
        _dark_axes(ax, title=f"UEQ benchmark - {app}", xlabel="Scala", ylabel="Media trasformata (-3..+3)")
        _savefig(CHARTS / f"ueq_benchmark_{app.lower()}.png")
    fig, ax = plt.subplots(figsize=(9, 4), facecolor=BACKGROUND)
    sns.barplot(data=desc, x="scale", y="mean", hue="app", palette=[DELIVEROO, GLOVO], ax=ax)
    ax.axhline(0, color=MUTED, linewidth=1)
    ax.set_ylim(-3, 3)
    ax.tick_params(axis="x", rotation=30)
    _dark_axes(ax, title="UEQ benchmark - confronto", xlabel="Scala", ylabel="Media trasformata (-3..+3)")
    _style_legend(ax)
    _savefig(CHARTS / "ueq_benchmark_comparison.png")


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
            pivot_rows.append({"scale": _display_scale(scale), "subgroup": _display_subgroup(variable, level), "delta": float(wide.loc[scale, SYSTEMS[1]] - wide.loc[scale, SYSTEMS[0]])})
    data = pd.DataFrame(pivot_rows)
    if data.empty:
        return
    matrix = data.pivot_table(index="scale", columns="subgroup", values="delta")
    fig, ax = plt.subplots(figsize=(max(9, 0.8 * len(matrix.columns)), 5.2), facecolor=BACKGROUND)
    heatmap = sns.heatmap(matrix, center=0, cmap="vlag", annot=True, fmt=".2f", linewidths=0.5, linecolor=GRID, ax=ax)
    _dark_axes(ax, title="Sottogruppi UEQ: differenza Glovo - Deliveroo", xlabel="Sottogruppo", ylabel="Scala UEQ")
    ax.grid(False)
    ax.tick_params(axis="x", rotation=35)
    for text in ax.texts:
        text.set_color("#111827")
    cbar = heatmap.collections[0].colorbar
    cbar.ax.tick_params(colors=MUTED)
    cbar.outline.set_edgecolor(GRID)
    _savefig(CHARTS / "subgroup_ueq_heatmap.png")


def _display_scale(value: object) -> str:
    mapping = {
        "Attractiveness": "Attrattivita",
        "Perspicuity": "Chiarezza",
        "Efficiency": "Efficienza",
        "Dependability": "Affidabilita",
        "Stimulation": "Stimolazione",
        "Novelty": "Novita",
    }
    return mapping.get(str(value), str(value))


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
    for scale, row in pivot.iterrows():
        d = row.get("Deliveroo", np.nan)
        g = row.get("Glovo", np.nan)
        winner = "Deliveroo" if d > g else "Glovo" if g > d else "pari"
        rows.append({"Dimensione": _display_scale(scale), "Deliveroo": _fmt_num(d, 2), "Glovo": _fmt_num(g, 2), "Delta G-D": _fmt_num(g - d, 2), "Vincitore": winner})
    return pd.DataFrame(rows)


def _ueq_scale_tests_display_table(scale_tests: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in scale_tests.itertuples(index=False):
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
    for scale in wide_mean.index:
        d = wide_mean.loc[scale].get("Deliveroo", np.nan)
        g = wide_mean.loc[scale].get("Glovo", np.nan)
        rows.append(
            {
                "Dimensione": _display_scale(scale),
                "Deliveroo": _fmt_num(d, 2),
                "Glovo": _fmt_num(g, 2),
                "Migliore": "Deliveroo" if d > g else "Glovo" if g > d else "pari",
                "Cat. D": wide_cat.loc[scale].get("Deliveroo", "n.d."),
                "Cat. G": wide_cat.loc[scale].get("Glovo", "n.d."),
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
            "- UEQ raw 1..7 e trasformato -3..+3, item 1-26, scale e benchmark configurabile.",
            "- Sottogruppi descrittivi sulle variabili profilo realmente disponibili.",
            "",
            "## Colonne mancanti o limiti",
            "- `app_order` non e presente nei CSV disponibili.",
            "- I benchmark UEQ sono soglie configurabili locali, non percentili ufficiali da dataset esterno.",
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
            "Le categorie benchmark sono configurate in `config/ueq_benchmark_thresholds.yml`.",
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
