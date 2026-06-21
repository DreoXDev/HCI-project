from __future__ import annotations

import math
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
from .plots import save_figure
from .tables import export_table
from .visualization.theme import get_brand_palette, style_axis


WIDE_TIMES = [
    ("U1", "Valentina", "01:41.07", "01:40.27", "02:53.90", "00:32.82", "01:02.96", "01:26.15"),
    ("U2", "Valentina", "01:14.47", "00:57.22", "01:09.89", "00:37.21", "00:05.53", "01:01.28"),
    ("U3", "Valentina", "01:47.86", "02:02.90", "01:10.27", "02:39.61", "01:20.50", "01:53.31"),
    ("U4", "Valentina", "00:42.15", "00:49.50", "00:52.30", "00:26.45", "00:31.60", "00:45.12"),
    ("U5", "Valentina", "01:05.32", "01:08.14", "01:15.45", "00:41.18", "00:48.92", "01:06.50"),
    ("U6", "Valentina", "00:35.88", "00:41.12", "00:58.19", "00:22.10", "00:28.40", "00:39.55"),
    ("U7", "Jacopo", "01:56.40", "01:41.53", "02:15.37", "00:45.26", "01:10.58", "00:52.64"),
    ("U8", "Jacopo", "00:22.26", "00:59.24", "01:13.87", "00:17.83", "01:24.48", "00:40.59"),
    ("U9", "Jacopo", "00:39.92", "01:10.44", "01:09.61", "00:34.71", "02:41.54", "00:33.75"),
    ("U10", "Jacopo", "00:47.46", "01:47.65", "02:28.23", "00:41.13", "01:56.89", "02:00.50"),
    ("U11", "Jacopo", "00:40.41", "00:49.31", "00:23.08", "00:18.24", "01:01.73", "00:36.25"),
    ("U12", "Jacopo", "00:32.49", "00:40.92", "00:56.24", "00:24.91", "00:36.67", "00:42.84"),
    ("U13", "Samuele", "00:31.93", "00:28.28", "00:31.98", "00:32.82", "00:17.69", "00:38.52"),
    ("U14", "Samuele", "00:34.48", "00:29.91", "01:32.78", "00:22.74", "02:41.22", "00:13.30"),
    ("U15", "Samuele", "00:18.32", "00:29.53", "01:03.63", "00:21.07", "01:02.99", "00:15.94"),
    ("U16", "Samuele", "01:09.97", "01:21.09", "02:50.02", "00:42.52", "01:10.00", "00:26.05"),
    ("U17", "Samuele", "00:43.56", "00:33.86", "00:50.64", "00:25.30", "00:55.29", "00:14.51"),
    ("U18", "Samuele", "00:26.88", "00:29.37", "00:44.42", "00:19.08", "00:41.17", "00:16.33"),
    ("U19", "Riccardo", "00:23.39", "00:46.28", "02:09.59", "00:32.04", "00:59.48", "01:16.87"),
    ("U20", "Riccardo", "00:22.26", "00:59.24", "01:13.87", "00:17.83", "01:24.48", "00:40.59"),
    ("U21", "Riccardo", "00:19.02", "01:10.65", "01:27.24", "00:29.16", "00:47.01", "00:36.20"),
    ("U22", "Riccardo", "01:29.82", "01:18.83", "02:46.98", "00:25.13", "00:32.57", "00:40.49"),
    ("U23", "Riccardo", "01:01.00", "01:23.01", "00:49.66", "00:24.27", "00:31.92", "00:37.52"),
    ("U24", "Riccardo", "01:59.20", "00:40.55", "01:09.02", "01:15.87", "00:37.69", "00:14.22"),
]

ISSUES = {
    ("U1", "Deliveroo", 3): ("assisted_success", "verbal_help", True, "Task completata con aiuto durante il test"),
    ("U1", "Glovo", 3): ("assisted_success", "verbal_help", True, "Task completata con aiuto durante il test"),
    ("U2", "Deliveroo", 3): ("assisted_success", "verbal_help", True, "Task completata con aiuto durante il test"),
    ("U3", "Deliveroo", 2): ("assisted_success", "verbal_help", True, "Task completata con aiuto durante il test"),
    ("U5", "Deliveroo", 3): ("assisted_success", "verbal_help", True, "Task completata con aiuto durante il test"),
    ("U5", "Glovo", 3): ("assisted_success", "verbal_help", True, "Task completata con aiuto durante il test; problema carrello/ordini senza login gia annotato"),
    ("U6", "Deliveroo", 1): ("success_with_issue", "workaround", True, "App non accetta l'indirizzo inserito e lo sostituisce con una strada adiacente"),
    ("U10", "Deliveroo", 1): ("success_with_issue", "unknown", True, "Problemi a impostare l'indirizzo indicato come predefinito"),
    ("U14", "Deliveroo", 3): ("assisted_success", "verbal_help", True, "Errore durante task 3 Deliveroo; completata con aiuto"),
    ("U15", "Deliveroo", 3): ("assisted_success", "verbal_help", True, "Errore durante task 3 Deliveroo; completata con aiuto"),
    ("U16", "Deliveroo", 3): ("assisted_success", "verbal_help", True, "Errore durante task 3 Deliveroo; completata con aiuto"),
    ("U22", "Deliveroo", 3): ("assisted_success", "verbal_help", True, "Task 3 Deliveroo completata con assistenza"),
    ("U24", "Deliveroo", 3): ("assisted_success", "verbal_help", True, "Task 3 Deliveroo completata con assistenza"),
}

QUALITATIVE_NOTES = [
    ("Deliveroo", "Geolocalizzazione", "Anomalie indirizzo/geolocalizzazione: in alcuni casi l'app modifica o rifiuta l'indirizzo previsto dal task."),
    ("Deliveroo", "Carrello", "Carrello difficile da trovare o controllare durante la modifica dell'ordine."),
    ("Deliveroo", "Modifica ordine", "Modifica ordine controintuitiva, soprattutto su prodotti duplicati e attributi non modificabili singolarmente."),
    ("Deliveroo", "Sovraccarico GUI", "GUI percepita come sovraccarica e disturbata da annunci pop-up."),
    ("Glovo", "Carrello", "Poca reattivita nella modifica delle quantita dal carrello."),
    ("Glovo", "Checkout", "Bug o frizioni nell'area checkout."),
    ("Glovo", "Home", "Home page percepita come controintuitiva da alcuni utenti."),
    ("Glovo", "Login/carrello", "In almeno un caso il carrello non era accessibile da ordini senza login e l'utente e risalito dalla pagina ristorante."),
    ("Entrambe", "Assistenze Valentina", "Nel gruppo raccolto da Valentina, alcuni utenti hanno completato determinate task solo dopo assistenza. Le assistenze si concentrano soprattutto sulla task 3 di Deliveroo, con ulteriori casi nella task 3 di Glovo; questo riduce l'efficacia stretta e mostra che completare un task non coincide sempre con un flusso autonomo."),
]


def generate_real_user_testing_outputs(config: dict) -> dict[str, Path]:
    times = _build_times()
    _write_csv(times, "data/user_testing_times.csv")
    _write_csv(_long_users_time(times, config), "data/raw/users_time.csv")
    trials = _trials_from_times(times, config)
    _write_csv(trials, "data/processed/user_task_trials_normalized.csv")
    _write_csv(trials, "outputs/tables/user_task_trials_full.csv")
    resolve_path("outputs/tables/user_task_trials_full.xlsx").parent.mkdir(parents=True, exist_ok=True)
    trials.to_excel(resolve_path("outputs/tables/user_task_trials_full.xlsx"), index=False)

    profiles = _build_user_profiles(config)
    _write_csv(profiles, "data/user_profiles.csv")
    _write_csv(_profile_slide_table(profiles), "outputs/tables/user_profiles_slide.csv")
    _write_profile_method()

    efficiency = _efficiency_by_task(times)
    comparison = _efficiency_comparison(times)
    effectiveness = _effectiveness_by_task(times)
    assistance = _assistance_errors(times)
    wide = _wide_times(times)
    qualitative = pd.DataFrame(QUALITATIVE_NOTES, columns=["app", "theme", "note"])
    expertise_group = _testing_by_expertise_group(times, profiles)

    _write_csv(wide, "outputs/tables/user_testing_times_wide.csv")
    _write_csv(efficiency, "outputs/tables/user_test_efficiency_by_task.csv")
    _write_csv(comparison, "outputs/tables/user_test_efficiency_comparison.csv")
    _write_csv(_efficiency_comparison_slide(comparison), "outputs/tables/user_test_efficiency_comparison_slide.csv")
    _write_csv(effectiveness, "outputs/tables/user_test_effectiveness_by_task.csv")
    _write_csv(assistance, "outputs/tables/user_test_assistance_errors.csv")
    _write_csv(_assistance_events_slide(times), "outputs/tables/user_test_assistance_events_slide.csv")
    _write_csv(qualitative, "outputs/tables/user_test_qualitative_notes.csv")
    _write_csv(expertise_group, "outputs/tables/user_testing_by_expertise_group.csv")

    _plot_efficiency(times, config)
    _plot_effectiveness(effectiveness, config)
    _plot_profiles(profiles, config)
    return {"times": resolve_path("data/user_testing_times.csv"), "profiles": resolve_path("data/user_profiles.csv")}


def _build_times() -> pd.DataFrame:
    rows = []
    columns = [("Deliveroo", 1), ("Deliveroo", 2), ("Deliveroo", 3), ("Glovo", 1), ("Glovo", 2), ("Glovo", 3)]
    for user_id, collector, *times in WIDE_TIMES:
        for (app, task), raw in zip(columns, times):
            outcome, assistance, error_flag, note = ISSUES.get((user_id, app, task), ("success", "none", False, ""))
            rows.append(
                {
                    "user_id": user_id,
                    "collector": collector,
                    "app": app,
                    "task": task,
                    "time_raw": raw,
                    "time_seconds": _seconds(raw),
                    "outcome": outcome,
                    "assistance": assistance,
                    "error_flag": str(error_flag).lower(),
                    "issue_note": note,
                }
            )
    return pd.DataFrame(rows)


def _trials_from_times(times: pd.DataFrame, config: dict) -> pd.DataFrame:
    task_names = {index + 1: task.get("name", f"Task {index + 1}") for index, task in enumerate(config.get("users_time", {}).get("tasks", [])[:3])}
    rows = []
    for row in times.itertuples(index=False):
        normalized_outcome = "partial_success" if row.outcome == "success_with_issue" else row.outcome
        rows.append(
            {
                "participant_id": row.user_id,
                "app": row.app,
                "task_id": f"T{int(row.task):02d}",
                "task_label": task_names.get(int(row.task), f"Task {row.task}"),
                "time_seconds": row.time_seconds,
                "outcome": normalized_outcome,
                "completed": normalized_outcome in {"success", "assisted_success", "partial_success"},
                "correct": normalized_outcome in {"success", "assisted_success", "partial_success"},
                "assisted": row.assistance in {"verbal_help", "workaround"} or normalized_outcome == "assisted_success",
                "error_count": 1 if str(row.error_flag).casefold() == "true" else 0,
                "critical_error_count": 0,
                "help_count": 1 if row.assistance == "verbal_help" or normalized_outcome == "assisted_success" else 0,
                "notes": row.issue_note,
            }
        )
    return pd.DataFrame(rows)


def _build_user_profiles(config: dict) -> pd.DataFrame:
    source = resolve_path("data/raw/questionnaire_deliveroo.csv")
    if not source.exists():
        return pd.DataFrame(columns=["user_id", "age_group", "gender", "occupation", "delivery_familiarity", "digital_familiarity", "food_delivery_frequency", "notes"])
    df = pd.read_csv(source, encoding="utf-8-sig").set_index("item")
    rows = []
    for index in range(1, 25):
        col = f"Utente {index}"
        raw_fam = pd.to_numeric(df.loc["familiarita delivery", col], errors="coerce") if "familiarita delivery" in df.index else np.nan
        delivery = _score_familiarity(raw_fam)
        rows.append(
            {
                "user_id": f"U{index}",
                "age_group": df.loc["eta", col] if "eta" in df.index else "unknown",
                "gender": df.loc["genere", col] if "genere" in df.index else "unknown",
                "occupation": df.loc["situazione lavorativa", col] if "situazione lavorativa" in df.index else "unknown",
                "delivery_familiarity": delivery,
                "digital_familiarity": delivery,
                "food_delivery_frequency": raw_fam if pd.notna(raw_fam) else "unknown",
                "notes": "digital_familiarity riusa la familiarita delivery: il questionario non contiene una variabile digitale separata.",
            }
        )
    return pd.DataFrame(rows)


def _profile_slide_table(profiles: pd.DataFrame) -> pd.DataFrame:
    return profiles[["user_id", "age_group", "gender", "occupation", "delivery_familiarity", "digital_familiarity"]].copy()


def _write_profile_method() -> None:
    text = "\n".join(
        [
            "# Metodo ricodifica profili utenti",
            "",
            "- Gli ID sono anonimizzati come U1-U24 e allineati ai tempi user testing.",
            "- La familiarita delivery del questionario usa valori 1-3.",
            "- La matrice mantiene la scala originale 1-3: 1 = bassa, 2 = media, 3 = alta.",
            "- Non e presente una variabile separata di familiarita digitale generale; `digital_familiarity` riusa lo stesso valore dichiarato.",
            "- Eventuali piccoli spostamenti dei punti sono usati solo nel grafico per evitare sovrapposizioni e non modificano i dati.",
            "- La matrice e descrittiva e non va interpretata come misura psicometrica robusta o come expertise bidimensionale indipendente.",
            "",
        ]
    )
    target = resolve_path("outputs/tables/user_profile_scoring_method.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _efficiency_by_task(times: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (app, task), group in times.groupby(["app", "task"], sort=True):
        values = group["time_seconds"]
        ci_low, ci_high = _mean_ci(values)
        rows.append(
            {
                "app": app,
                "task": task,
                "n": len(values),
                "mean_seconds": values.mean(),
                "median_seconds": values.median(),
                "std_seconds": values.std(ddof=1),
                "min_seconds": values.min(),
                "q1_seconds": values.quantile(0.25),
                "q3_seconds": values.quantile(0.75),
                "max_seconds": values.max(),
                "ci95_low": ci_low,
                "ci95_high": ci_high,
            }
        )
    return pd.DataFrame(rows)


def _efficiency_comparison(times: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for task, group in times.groupby("task", sort=True):
        pivot = group.pivot(index="user_id", columns="app", values="time_seconds").dropna()
        diff = pivot["Deliveroo"] - pivot["Glovo"]
        normal = len(diff) >= 3 and stats.shapiro(diff).pvalue >= 0.05
        if normal:
            test = stats.ttest_rel(pivot["Deliveroo"], pivot["Glovo"])
            test_name = "paired t-test"
            statistic = float(test.statistic)
        else:
            test = stats.wilcoxon(pivot["Deliveroo"], pivot["Glovo"])
            test_name = "Wilcoxon signed-rank"
            statistic = float(test.statistic)
        ci_low, ci_high = _bootstrap_ci(diff)
        rows.append(
            {
                "task": task,
                "paired_n": len(pivot),
                "deliveroo_mean": pivot["Deliveroo"].mean(),
                "glovo_mean": pivot["Glovo"].mean(),
                "mean_diff_deliveroo_minus_glovo": diff.mean(),
                "test_name": test_name,
                "statistic": statistic,
                "p_value": float(test.pvalue),
                "ci95_diff_low": ci_low,
                "ci95_diff_high": ci_high,
                "interpretation": _task_interpretation(task, pivot["Deliveroo"].mean(), pivot["Glovo"].mean(), float(test.pvalue), ci_low, ci_high),
            }
        )
    return pd.DataFrame(rows)


def _efficiency_comparison_slide(comparison: pd.DataFrame) -> pd.DataFrame:
    if comparison.empty:
        return pd.DataFrame(columns=["Task", "N", "Media D", "Media G", "Diff. D-G", "Test", "p-value", "Interpretazione"])
    result = comparison.copy()
    return pd.DataFrame(
        {
            "Task": result["task"].map(lambda value: f"Task {int(value)}"),
            "N": result["paired_n"].astype(int),
            "Media D": result["deliveroo_mean"].map(_fmt_number),
            "Media G": result["glovo_mean"].map(_fmt_number),
            "Diff. D-G": result["mean_diff_deliveroo_minus_glovo"].map(_fmt_number),
            "Test": result["test_name"],
            "p-value": result["p_value"].map(_fmt_p_value),
            "Interpretazione": result["interpretation"],
        }
    )


def _effectiveness_by_task(times: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (app, task), group in times.groupby(["app", "task"], sort=True):
        strict = group["outcome"].isin(["success", "success_with_issue"])
        extended = group["outcome"].isin(["success", "success_with_issue", "assisted_success"])
        assisted = group["assistance"].isin(["verbal_help", "workaround"]) | group["outcome"].eq("assisted_success")
        issues = group["error_flag"].astype(str).str.casefold().eq("true")
        rows.append(
            {
                "app": app,
                "task": task,
                "n": len(group),
                "strict_success_count": int(strict.sum()),
                "strict_success_rate": strict.mean(),
                "extended_success_count": int(extended.sum()),
                "extended_success_rate": extended.mean(),
                "assisted_count": int(assisted.sum()),
                "assisted_rate": assisted.mean(),
                "issue_count": int(issues.sum()),
                "issue_rate": issues.mean(),
            }
        )
    return pd.DataFrame(rows)


def _assistance_errors(times: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for app, group in times.groupby("app", sort=True):
        issues = group["error_flag"].astype(str).str.casefold().eq("true")
        assisted = group["assistance"].isin(["verbal_help", "workaround"]) | group["outcome"].eq("assisted_success")
        rows.append(
            {
                "app": app,
                "task": "All",
                "total_trials": len(group),
                "issue_trials": int(issues.sum()),
                "issue_rate": issues.mean(),
                "assisted_trials": int(assisted.sum()),
                "assisted_rate": assisted.mean(),
            }
        )
    by_task = times.groupby(["app", "task"]).apply(
        lambda group: pd.Series(
            {
                "total_trials": len(group),
                "issue_trials": int(group["error_flag"].astype(str).str.casefold().eq("true").sum()),
                "assisted_trials": int((group["assistance"].isin(["verbal_help", "workaround"]) | group["outcome"].eq("assisted_success")).sum()),
                "issue_rate": group["error_flag"].astype(str).str.casefold().eq("true").mean(),
                "assisted_rate": (group["assistance"].isin(["verbal_help", "workaround"]) | group["outcome"].eq("assisted_success")).mean(),
            }
        ),
        include_groups=False,
    ).reset_index()
    result = pd.concat([pd.DataFrame(rows), by_task], ignore_index=True, sort=False)
    return result[["app", "task", "total_trials", "issue_trials", "issue_rate", "assisted_trials", "assisted_rate"]]


def _assistance_events_slide(times: pd.DataFrame) -> pd.DataFrame:
    assisted = times[
        times["assistance"].isin(["verbal_help", "workaround"]) | times["outcome"].eq("assisted_success") | times["error_flag"].astype(str).str.casefold().eq("true")
    ].copy()
    if assisted.empty:
        return pd.DataFrame(columns=["Utente", "App", "Task", "Tipo evento", "Nota"])
    assisted["Tipo evento"] = assisted.apply(_event_label, axis=1)
    result = assisted[["user_id", "app", "task", "Tipo evento", "issue_note"]].copy()
    result.columns = ["Utente", "App", "Task", "Tipo evento", "Nota"]
    return result.sort_values(["App", "Task", "Utente"])


def _event_label(row: pd.Series) -> str:
    if row.get("outcome") == "assisted_success" or row.get("assistance") == "verbal_help":
        return "Completata con aiuto"
    if row.get("assistance") == "workaround":
        return "Workaround"
    return "Issue"


def _wide_times(times: pd.DataFrame) -> pd.DataFrame:
    pivot = times.pivot_table(index="user_id", columns=["task", "app"], values="time_raw", aggfunc="first")
    result = pd.DataFrame({"user_id": sorted(times["user_id"].unique(), key=lambda value: int(value[1:]))})
    for task in [1, 2, 3]:
        for app, suffix in [("Deliveroo", "D"), ("Glovo", "G")]:
            result[f"Task {task} {suffix}"] = result["user_id"].map(lambda uid: pivot.loc[uid, (task, app)])
    return result


def _long_users_time(times: pd.DataFrame, config: dict) -> pd.DataFrame:
    task_names = {index + 1: task.get("name", f"Task {index + 1}") for index, task in enumerate(config.get("users_time", {}).get("tasks", [])[:3])}
    rows = []
    for row in times.itertuples(index=False):
        success = row.outcome in {"success", "success_with_issue", "assisted_success"}
        rows.append(
            {
                "user_id": row.user_id,
                "app": row.app,
                "task_id": f"T{int(row.task):02d}",
                "task_name": task_names.get(int(row.task), f"Task {row.task}"),
                "completion_time_sec": row.time_seconds,
                "success": success,
                "errors_count": 1 if str(row.error_flag).casefold() == "true" else 0,
                "help_requests": 1 if row.assistance == "verbal_help" or row.outcome == "assisted_success" else 0,
                "notes": row.issue_note,
                "completion_time_raw": row.time_raw,
                "observer": row.collector,
            }
        )
    return pd.DataFrame(rows)


def _testing_by_expertise_group(times: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    profiles = profiles.copy()
    profiles["expertise_score"] = profiles[["delivery_familiarity", "digital_familiarity"]].mean(axis=1)
    median = profiles["expertise_score"].median()
    profiles["expertise_group"] = np.where(profiles["expertise_score"] < median, "low_expertise", "high_expertise")
    merged = times.merge(profiles[["user_id", "expertise_group"]], on="user_id", how="left")
    rows = []
    for (group, app, task), subset in merged.groupby(["expertise_group", "app", "task"], dropna=False):
        strict = subset["outcome"].isin(["success", "success_with_issue"])
        extended = subset["outcome"].isin(["success", "success_with_issue", "assisted_success"])
        rows.append(
            {
                "expertise_group": group,
                "app": app,
                "task": task,
                "n": len(subset),
                "mean_time_seconds": subset["time_seconds"].mean(),
                "assisted_tasks": int((subset["assistance"].isin(["verbal_help", "workaround"]) | subset["outcome"].eq("assisted_success")).sum()),
                "issue_tasks": int(subset["error_flag"].astype(str).str.casefold().eq("true").sum()),
                "strict_effectiveness": strict.mean(),
                "extended_effectiveness": extended.mean(),
            }
        )
    return pd.DataFrame(rows)


def _plot_efficiency(times: pd.DataFrame, config: dict) -> None:
    charts = resolve_path("outputs/charts")
    charts.mkdir(parents=True, exist_ok=True)
    palette = get_brand_palette(config)
    for task in [1, 2, 3]:
        subset = times[times["task"] == task]
        fig, ax = plt.subplots(figsize=(8, 4.8))
        sns.boxplot(data=subset, x="app", y="time_seconds", hue="app", palette=palette, legend=False, ax=ax)
        sns.stripplot(data=subset, x="app", y="time_seconds", color="#F8FAFC", size=4, alpha=0.65, ax=ax)
        style_axis(ax, f"Efficienza Task {task}", "", "Secondi")
        save_figure(fig, charts / f"user_test_efficiency_task_{task}.png", config)
        _copy_root_png(charts / f"user_test_efficiency_task_{task}.png")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=times, x="task", y="time_seconds", hue="app", palette=palette, errorbar="ci", ax=ax)
    style_axis(ax, "Efficienza complessiva per task", "Task", "Secondi medi")
    save_figure(fig, charts / "user_test_efficiency_overall.png", config)
    _copy_root_png(charts / "user_test_efficiency_overall.png")


def _plot_effectiveness(effectiveness: pd.DataFrame, config: dict) -> None:
    charts = resolve_path("outputs/charts")
    palette = get_brand_palette(config)
    for metric, name, title in [
        ("strict_success_rate", "user_test_effectiveness_strict.png", "Efficacia stretta"),
        ("extended_success_rate", "user_test_effectiveness_extended.png", "Efficacia estesa"),
        ("assisted_rate", "user_test_assisted_tasks.png", "Task assistite"),
    ]:
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.barplot(data=effectiveness, x="task", y=metric, hue="app", palette=palette, ax=ax)
        ax.set_ylim(0, 1)
        style_axis(ax, title, "Task", "Quota")
        save_figure(fig, charts / name, config)
        _copy_root_png(charts / name)


def _plot_profiles(profiles: pd.DataFrame, config: dict) -> None:
    charts = resolve_path("outputs/charts")
    charts.mkdir(parents=True, exist_ok=True)
    _plot_demographic_pie_chart(profiles, "age_group", "Fascia d'eta utenti (n = 24)", charts / "users_age_pie.png", config)
    _plot_demographic_pie_chart(profiles, "gender", "Genere utenti (n = 24)", charts / "users_gender_pie.png", config)
    _plot_demographic_pie_chart(profiles, "occupation", "Occupazione utenti (n = 24)", charts / "users_occupation_pie.png", config)
    _plot_demographic_pie_chart(profiles, "food_delivery_frequency", "Familiarita food delivery (n = 24)", charts / "users_delivery_familiarity_pie.png", config)
    _copy_root_png(charts / "users_age_pie.png")
    _copy_root_png(charts / "users_gender_pie.png")
    _copy_root_png(charts / "users_occupation_pie.png")
    _copy_root_png(charts / "users_delivery_familiarity_pie.png")
    _plot_demographic_pair(
        profiles,
        ("age_group", "Fascia d'eta utenti (n = 24)"),
        ("gender", "Genere utenti (n = 24)"),
        charts / "user_demographics_age_gender.png",
        config,
    )
    _copy_root_png(charts / "user_demographics_age_gender.png")

    fig, ax = plt.subplots(figsize=(8, 4.8))
    sns.countplot(data=profiles, x="delivery_familiarity", color="#00CCBC", ax=ax)
    style_axis(ax, "Familiarita delivery", "Score 1-10", "Utenti")
    save_figure(fig, charts / "user_profile_delivery_familiarity.png", config)
    _copy_root_png(charts / "user_profile_delivery_familiarity.png")

    fig, ax = plt.subplots(figsize=(8.8, 6.2))
    rng = np.random.default_rng(42)
    jitter_x = rng.uniform(-0.05, 0.05, len(profiles))
    jitter_y = rng.uniform(-0.05, 0.05, len(profiles))
    x = profiles["delivery_familiarity"].astype(float)
    y = profiles["digital_familiarity"].astype(float)
    ax.scatter(x + jitter_x, y + jitter_y, s=120, c="#00CCBC", alpha=0.8, edgecolors="#F8FAFC", linewidths=1.2)
    for uid, px, py in zip(profiles["user_id"], x + jitter_x, y + jitter_y):
        ax.text(px + 0.08, py + 0.05, uid, color="#F8FAFC", fontsize=8)
    ax.axvline(2, color="#CBD5E1", linestyle="--", linewidth=1)
    ax.axhline(2, color="#CBD5E1", linestyle="--", linewidth=1)
    ax.set_xlim(0.5, 3.5)
    ax.set_ylim(0.5, 3.5)
    ax.set_xticks([1, 2, 3], ["1 - bassa", "2 - media", "3 - alta"])
    ax.set_yticks([1, 2, 3], ["1 - bassa", "2 - media", "3 - alta"])
    ax.text(
        0.02,
        -0.18,
        "Scala originale 1-3; piccoli spostamenti solo visuali. Matrice descrittiva: asse verticale non indipendente.",
        transform=ax.transAxes,
        color="#CBD5E1",
        fontsize=9,
    )
    style_axis(ax, "Matrice descrittiva del profilo utenti", "Familiarita food delivery (1-3)", "Familiarita / expertise dichiarata (1-3)")
    save_figure(fig, charts / "user_expertise_matrix.png", config)
    _copy_root_png(charts / "user_expertise_matrix.png")


def _plot_demographic_pair(
    df: pd.DataFrame,
    left: tuple[str, str],
    right: tuple[str, str],
    output_path: Path,
    config: dict,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for ax, (column, title) in zip(axes, [left, right]):
        _draw_pie(ax, df[column].dropna().astype(str), title)
    save_figure(fig, output_path, config)


def _plot_demographic_pie_chart(
    df: pd.DataFrame,
    column: str,
    title: str,
    output_path: Path,
    config: dict,
) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 5.4))
    _draw_pie(ax, df[column].dropna().astype(str), title)
    save_figure(fig, output_path, config)


def _draw_pie(ax: plt.Axes, values: pd.Series, title: str) -> None:
    counts = values.value_counts()
    labels = [str(label) for label in counts.index]
    total = int(counts.sum())
    colors = sns.color_palette("Set2", n_colors=max(3, len(counts)))
    wedges, _, autotexts = ax.pie(
        counts,
        startangle=90,
        colors=colors,
        autopct=lambda pct: f"{pct:.0f}%\n({int(round(pct * total / 100))})",
        pctdistance=0.72,
        textprops={"color": "#F8FAFC", "fontsize": 9},
    )
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False)
    for text in autotexts:
        text.set_weight("bold")
    ax.set_title(title, color="#F8FAFC", fontsize=14, pad=14)
    ax.axis("equal")


def _seconds(raw: str) -> float:
    minutes, rest = raw.split(":", 1)
    return int(minutes) * 60 + float(rest)


def _score_familiarity(value: Any) -> float:
    try:
        numeric = int(float(value))
        return float(numeric) if numeric in {1, 2, 3} else float(value)
    except (TypeError, ValueError):
        return np.nan


def _fmt_number(value: Any) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return "n.d." if pd.isna(numeric) else f"{float(numeric):.2f}"


def _fmt_p_value(value: Any) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return "n.d."
    return "p < 0.001" if float(numeric) < 0.001 else f"{float(numeric):.3f}"


def _mean_ci(values: pd.Series) -> tuple[float, float]:
    arr = pd.to_numeric(values, errors="coerce").dropna()
    if len(arr) < 2:
        mean = arr.mean() if len(arr) else np.nan
        return mean, mean
    sem = stats.sem(arr)
    margin = stats.t.ppf(0.975, len(arr) - 1) * sem
    return float(arr.mean() - margin), float(arr.mean() + margin)


def _bootstrap_ci(values: pd.Series, iterations: int = 2000) -> tuple[float, float]:
    arr = pd.to_numeric(values, errors="coerce").dropna().to_numpy()
    if len(arr) < 2:
        mean = float(arr.mean()) if len(arr) else np.nan
        return mean, mean
    rng = np.random.default_rng(42)
    means = [rng.choice(arr, len(arr), replace=True).mean() for _ in range(iterations)]
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _task_interpretation(task: int, deliveroo_mean: float, glovo_mean: float, p_value: float, ci_low: float, ci_high: float) -> str:
    faster = "Deliveroo" if deliveroo_mean < glovo_mean else "Glovo"
    significance = "indica" if p_value < 0.05 else "non indica"
    stability = "stabile" if ci_low * ci_high > 0 else "incerta"
    return f"Nel Task {task}, {faster} ha tempo medio inferiore; il p-value {significance} una differenza significativa e l'IC rende la stima {stability}."


def _write_csv(df: pd.DataFrame, path: str | Path) -> Path:
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target, index=False, encoding="utf-8-sig")
    return target


def _copy_root_png(path: Path) -> None:
    source = resolve_path(path)
    dark = source.parent / "dark" / source.name
    if dark.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        import shutil

        shutil.copy2(dark, source)
