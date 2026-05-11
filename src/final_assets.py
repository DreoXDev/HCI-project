from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy import stats

from .config import resolve_path
from .heuristics import clean_heuristics
from .plots import save_figure
from .questionnaire import dynamic_demographic_rows, numeric_items, nps_summary
from .tables import export_table
from .users_time import users_time_file, validate_users_time_file
from .visualization.theme import get_brand_palette, style_axis


def oet_by_task(config: dict) -> dict[str, float]:
    return {str(task.get("id")): float(task["oet_seconds"]) for task in config.get("users_time", {}).get("tasks", []) if task.get("oet_seconds")}


def generate_final_assets(config: dict, data: dict[str, pd.DataFrame]) -> None:
    generate_problem_evaluator_outputs(config, data)
    generate_questionnaire_item_outputs(config, data)
    generate_nps_breakdown(config, data)
    generate_users_time_task_assets(config)
    generate_sample_assets(config, data)
    generate_subgroup_assets(config, data)


def _problem_id_column(df: pd.DataFrame) -> str:
    for column in ["Problem ID", "Codice problema", df.columns[0] if len(df.columns) else "Problem ID"]:
        if column in df.columns:
            return column
    return df.columns[0]


def _ids(value: object) -> list[str]:
    return [part.strip() for part in str(value).split("-") if part and part.strip() and part.strip().lower() != "nan"]


def problem_evaluator_matrix(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Id valutatori" not in df.columns:
        return pd.DataFrame()
    problem_col = _problem_id_column(df)
    evaluators = sorted({item for ids in df["Id valutatori"].fillna("") for item in _ids(ids)})
    problems = [str(value) for value in df[problem_col]]
    matrix = pd.DataFrame(0, index=evaluators, columns=problems, dtype=int)
    for _, row in df.iterrows():
        problem = str(row[problem_col])
        for evaluator in _ids(row.get("Id valutatori", "")):
            if evaluator in matrix.index:
                matrix.loc[evaluator, problem] = 1
    matrix["total_by_evaluator"] = matrix.sum(axis=1)
    totals = matrix.drop(columns=["total_by_evaluator"]).sum(axis=0)
    total_row = pd.DataFrame([list(totals) + [totals.sum()]], columns=matrix.columns, index=["total_by_problem"])
    return pd.concat([matrix, total_row])


def generate_problem_evaluator_outputs(config: dict, data: dict[str, pd.DataFrame]) -> None:
    systems = [(config["project"]["system_1"], data.get("heuristics_system_1", pd.DataFrame())), (config["project"]["system_2"], data.get("heuristics_system_2", pd.DataFrame()))]
    coverage_rows = []
    text_lines = ["# Copertura problemi euristici", ""]
    for system, df in systems:
        slug = system.lower()
        matrix = problem_evaluator_matrix(df)
        if matrix.empty:
            continue
        export_table(matrix.reset_index(names="evaluator"), f"outputs/tables/problem_evaluator_matrix_{slug}.csv", 2)
        fig, ax = plt.subplots(figsize=(max(8, matrix.shape[1] * 0.6), max(4, matrix.shape[0] * 0.35)))
        heat = matrix.drop(index=["total_by_problem"], errors="ignore").drop(columns=["total_by_evaluator"], errors="ignore")
        sns.heatmap(heat, cmap="YlGnBu", cbar=False, linewidths=0.4, linecolor="#E5E7EB", ax=ax)
        style_axis(ax, f"Matrice problemi-valutatori {system}", "Problemi", "Valutatori")
        save_figure(fig, f"outputs/figures/heuristics/problem_evaluator_matrix_{slug}.png", config)

        evaluator_counts = heat.sum(axis=1).sort_values(ascending=False)
        problem_counts = heat.sum(axis=0).sort_values(ascending=False)
        top_problem = problem_counts.index[0] if not problem_counts.empty else "n.d."
        top_count = int(problem_counts.iloc[0]) if not problem_counts.empty else 0
        top_evaluators = ", ".join(evaluator_counts.head(2).index.astype(str)) if not evaluator_counts.empty else "n.d."
        resolve_path(f"outputs/text_snippets/problem_evaluator_matrix_{slug}.md").write_text(
            f"# Matrice problemi-valutatori {system}\n\nIl problema più ricorrente e `{top_problem}`, segnalato da {top_count} valutatori. I valutatori più produttivi sono {top_evaluators}.\n",
            encoding="utf-8",
        )

        best_pair = None
        evaluators = list(heat.index)
        for i, first in enumerate(evaluators):
            for second in evaluators[i + 1 :]:
                a = int(heat.loc[first].sum())
                b = int(heat.loc[second].sum())
                common = int(((heat.loc[first] > 0) & (heat.loc[second] > 0)).sum())
                if common:
                    estimate = a * b / common
                    score = common
                    if best_pair is None or score > best_pair["common"]:
                        best_pair = {"system": system, "evaluator_a": first, "evaluator_b": second, "problems_a": a, "problems_b": b, "common": common, "estimated_total": round(estimate, 2)}
        if best_pair:
            coverage_rows.append(best_pair)
            text_lines.append(f"- {system}: stima grezza Nielsen con {best_pair['evaluator_a']} e {best_pair['evaluator_b']} = {best_pair['estimated_total']} problemi totali. Interpretare come indicazione euristica, non come verita assoluta.")
    coverage = pd.DataFrame(coverage_rows)
    if not coverage.empty:
        export_table(coverage, "outputs/tables/heuristics_problem_coverage.csv", 2)
    resolve_path("outputs/text_snippets/heuristics_problem_coverage.md").write_text("\n".join(text_lines) + "\n", encoding="utf-8")


def generate_questionnaire_item_outputs(config: dict, data: dict[str, pd.DataFrame]) -> None:
    systems = [(config["project"]["system_1"], data.get("questionnaire_system_1", pd.DataFrame())), (config["project"]["system_2"], data.get("questionnaire_system_2", pd.DataFrame()))]
    item_frames = {system: numeric_items(df, config) for system, df in systems if not df.empty}
    if len(item_frames) < 2:
        return
    names = list(item_frames)
    common_items = [item for item in item_frames[names[0]].index if item in item_frames[names[1]].index]
    rows = []
    for idx, item in enumerate(common_items, start=1):
        left = pd.to_numeric(item_frames[names[0]].loc[item], errors="coerce").dropna()
        right = pd.to_numeric(item_frames[names[1]].loc[item], errors="coerce").dropna()
        p_value = stats.mannwhitneyu(left, right, alternative="two-sided").pvalue if len(left) and len(right) else pd.NA
        row = {
            "item_number": idx,
            "item": item,
            f"{names[0]}_mean": left.mean(),
            f"{names[1]}_mean": right.mean(),
            f"{names[0]}_median": left.median(),
            f"{names[1]}_median": right.median(),
            "mean_difference_abs": abs(left.mean() - right.mean()),
            "median_difference_abs": abs(left.median() - right.median()),
            "p_value": p_value,
        }
        rows.append(row)
        plot_df = pd.DataFrame({"system": [names[0]] * len(left) + [names[1]] * len(right), "score": list(left) + list(right)})
        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        sns.boxplot(data=plot_df, x="system", y="score", hue="system", palette=get_brand_palette(config), legend=False, ax=ax)
        ax.set_ylim(config["analysis"]["ueq_scale_min"], config["analysis"]["ueq_scale_max"])
        style_axis(ax, f"Item {idx:02d}: {item}", "", "Valutazione")
        save_figure(fig, f"outputs/figures/questionnaire/items/item_{idx:02d}_boxplot.png", config)
    summary = pd.DataFrame(rows)
    if summary.empty:
        return
    summary["rank_score"] = summary["p_value"].fillna(1).rank(method="first") + summary["median_difference_abs"].rank(ascending=False) * 0.01
    relevant = summary.sort_values(["p_value", "median_difference_abs", "mean_difference_abs"], ascending=[True, False, False]).head(8)
    export_table(summary.drop(columns=["rank_score"]), "outputs/tables/questionnaire_items_summary.csv", 2)
    export_table(summary.drop(columns=["rank_score"]), "outputs/tables_md/questionnaire_items_summary.md", 2)
    export_table(relevant.drop(columns=["rank_score"]), "outputs/tables/questionnaire_most_relevant_items.csv", 2)
    lines = ["# Item UEQ più rilevanti", ""]
    for row in relevant.itertuples():
        significance = "significativa" if pd.notna(row.p_value) and row.p_value < 0.05 else "non significativa"
        lines.append(f"- Item {row.item_number:02d} `{row.item}`: differenza media assoluta {row.mean_difference_abs:.2f}, p={row.p_value:.4f}; differenza {significance}.")
    resolve_path("outputs/text_snippets/questionnaire_selected_items.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_nps_breakdown(config: dict, data: dict[str, pd.DataFrame]) -> None:
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    frames = [nps_summary(data.get("questionnaire_system_1", pd.DataFrame()), systems[0]), nps_summary(data.get("questionnaire_system_2", pd.DataFrame()), systems[1])]
    nps = pd.concat(frames, ignore_index=True)
    export_table(nps, "outputs/tables/nps_breakdown.csv", 2)
    if nps["total"].fillna(0).sum() <= 0:
        return
    plot_rows = []
    for row in nps.itertuples():
        total = row.total or 1
        for col, label in [("detractors", "Detrattori"), ("passives", "Passivi"), ("promoters", "Promotori")]:
            plot_rows.append({"system": row.system, "category": label, "percent": getattr(row, col) / total * 100})
    plot_df = pd.DataFrame(plot_rows)
    pivot = plot_df.pivot(index="system", columns="category", values="percent").fillna(0)
    fig, ax = plt.subplots(figsize=(7.5, 5))
    colors = {"Detrattori": "#EF4444", "Passivi": "#9CA3AF", "Promotori": "#10B981"}
    bottom = None
    for category in ["Detrattori", "Passivi", "Promotori"]:
        values = pivot.get(category, pd.Series(0, index=pivot.index))
        ax.bar(pivot.index, values, bottom=bottom, label=category, color=colors[category])
        bottom = values if bottom is None else bottom + values
    ax.legend(frameon=False)
    ax.set_ylim(0, 100)
    style_axis(ax, "Composizione NPS", "", "% rispondenti")
    save_figure(fig, "outputs/figures/questionnaire/nps_stacked_bar.png", config)


def generate_users_time_task_assets(config: dict) -> None:
    validation = validate_users_time_file(users_time_file(config), required_columns=config.get("users_time", {}).get("required_columns"))
    if not validation.is_valid:
        return
    df = validation.normalized
    oets = oet_by_task(config)
    stats_path = resolve_path("outputs/tables/users_time_stat_tests.csv")
    stat_tests = pd.read_csv(stats_path) if stats_path.exists() else pd.DataFrame()
    for task_id, task_group in df.groupby("task_id", sort=True):
        task_name = str(task_group["task_name"].dropna().iloc[0]) if task_group["task_name"].notna().any() else str(task_id)
        slug = str(task_id).lower().replace(" ", "_")
        summary = task_group.groupby("app").agg(
            n=("user_id", "nunique"),
            success_rate=("success", "mean"),
            mean_errors=("errors_count", "mean"),
            mean_time_sec=("completion_time_sec", "mean"),
            median_time_sec=("completion_time_sec", "median"),
            mean_help_requests=("help_requests", "mean"),
        ).reset_index()
        summary["failure_rate"] = 1 - summary["success_rate"]
        summary["assisted_rate"] = summary["mean_help_requests"].clip(lower=0).apply(lambda x: min(x, 1))
        if str(task_id) in oets:
            summary["oet_seconds"] = oets[str(task_id)]
            summary["mean_over_oet_sec"] = summary["mean_time_sec"] - oets[str(task_id)]
        export_table(summary, f"outputs/tables/user_tests_{slug}_summary.csv", 2)
        for metric, filename, ylabel in [
            ("success_rate", "effectiveness", "Success rate"),
            ("mean_time_sec", "efficiency", "Secondi"),
            ("mean_errors", "error_breakdown", "Errori medi"),
        ]:
            fig, ax = plt.subplots(figsize=(6.5, 4.5))
            sns.barplot(data=summary, x="app", y=metric, hue="app", palette=get_brand_palette(config), legend=False, ax=ax)
            if metric == "success_rate":
                ax.set_ylim(0, 1)
            style_axis(ax, f"{task_id} - {filename.replace('_', ' ')}", "", ylabel)
            save_figure(fig, f"outputs/figures/user_tests/tasks/{slug}_{filename}.png", config)
        p_text = "n.d."
        if not stat_tests.empty and "task_id" in stat_tests:
            matched = stat_tests[stat_tests["task_id"].astype(str) == str(task_id)]
            if not matched.empty:
                p_text = str(matched.iloc[0].get("p_value", "n.d."))
        lines = [f"# User test {task_id} - {task_name}", ""]
        for row in summary.itertuples():
            oet_text = f" Con OET={getattr(row, 'oet_seconds', 'n.d.')}s, scostamento medio={getattr(row, 'mean_over_oet_sec', 'n.d.')}s." if "oet_seconds" in summary.columns else " OET non configurato per questa task."
            lines.append(f"- {row.app}: successo {row.success_rate:.0%}, tempo medio {row.mean_time_sec:.2f}s, mediana {row.median_time_sec:.2f}s, errori medi {row.mean_errors:.2f}.{oet_text}")
        lines.append(f"- Test statistico sui tempi: p={p_text}.")
        resolve_path(f"outputs/text_snippets/user_tests_{slug}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_sample_assets(config: dict, data: dict[str, pd.DataFrame]) -> None:
    systems = [(config["project"]["system_1"], data.get("questionnaire_system_1", pd.DataFrame())), (config["project"]["system_2"], data.get("questionnaire_system_2", pd.DataFrame()))]
    sample_rows = []
    fields = ["genere", "eta", "familiarita delivery", "familiarita con app di delivery", "situazione lavorativa", "istruzione"]
    for system, df in systems:
        for field in fields:
            if field in df.index:
                counts = df.loc[field].astype(str).value_counts().reset_index()
                counts.columns = ["value", "count"]
                counts["system"] = system
                counts["field"] = field
                sample_rows.append(counts)
    if not sample_rows:
        return
    all_counts = pd.concat(sample_rows, ignore_index=True)
    export_table(all_counts, "outputs/tables/sample_composition.csv", 2)
    field_map = {"genere": "gender_distribution", "eta": "age_distribution", "familiarita delivery": "familiarity_distribution", "familiarita con app di delivery": "familiarity_distribution", "situazione lavorativa": "occupation_distribution"}
    done = set()
    for field, filename in field_map.items():
        subset = all_counts[all_counts["field"] == field]
        if subset.empty or filename in done:
            continue
        done.add(filename)
        fig, ax = plt.subplots(figsize=(8, 4.5))
        sns.barplot(data=subset, x="value", y="count", hue="system", palette=get_brand_palette(config), ax=ax)
        ax.tick_params(axis="x", rotation=25)
        style_axis(ax, field, "", "Rispondenti")
        save_figure(fig, f"outputs/figures/sample/{filename}.png", config)
    resolve_path("outputs/text_snippets/sample_description.md").write_text(
        "# Composizione campione\n\nGli asset distinguono il campione questionario per sistema. Integrare manualmente campione user test e valutatori euristici quando serve dettaglio qualitativo.\n",
        encoding="utf-8",
    )


def generate_subgroup_assets(config: dict, data: dict[str, pd.DataFrame]) -> None:
    subgroup_path = resolve_path("outputs/tables_md/subgroup_analysis.md")
    csv_path = resolve_path("outputs/tables/subgroup_analysis.csv")
    if subgroup_path.exists() and not csv_path.exists():
        # Il markdown e gia esportato dalla pipeline; il CSV viene creato qui se possibile dai questionari.
        pass
    systems = [(config["project"]["system_1"], data.get("questionnaire_system_1", pd.DataFrame())), (config["project"]["system_2"], data.get("questionnaire_system_2", pd.DataFrame()))]
    rows = []
    preferred = ["genere", "eta", "familiarita delivery", "familiarita con app di delivery", "situazione lavorativa", "preferred_app"]
    for system, df in systems:
        if df.empty:
            continue
        items = numeric_items(df, config)
        user_mean = items.mean(axis=0)
        demographics = dynamic_demographic_rows(df, config)
        for field in preferred:
            if field in df.index and field in demographics:
                tmp = pd.DataFrame({"group_value": df.loc[field], "ueq_mean": user_mean})
                grouped = tmp.groupby("group_value")["ueq_mean"].agg(["count", "mean", "median", "std"]).reset_index()
                grouped["system"] = system
                grouped["group_field"] = field
                grouped["robustness"] = grouped["count"].apply(lambda n: "descrittivo_non_robusto" if n < 5 else "descrittivo")
                rows.append(grouped)
    if not rows:
        return
    result = pd.concat(rows, ignore_index=True)
    export_table(result, "outputs/tables/subgroup_analysis.csv", 2)
    fam = result[result["group_field"].isin(["familiarita delivery", "familiarita con app di delivery"])]
    if not fam.empty:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        sns.barplot(data=fam, x="group_value", y="mean", hue="system", palette=get_brand_palette(config), ax=ax)
        ax.tick_params(axis="x", rotation=25)
        style_axis(ax, "UEQ per familiarita", "Familiarita", "Media UEQ")
        save_figure(fig, "outputs/figures/questionnaire/subgroups/ueq_by_familiarity.png", config)
    warning = "I sottogruppi con meno di 5 partecipanti sono descrittivi e non robusti."
    resolve_path("outputs/text_snippets/subgroup_conclusions.md").write_text(f"# Analisi sottogruppi\n\n{warning}\n", encoding="utf-8")
