from __future__ import annotations

from pathlib import Path
import re
import shutil

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
import yaml

from .config import resolve_path
from .heuristics import clean_heuristics
from .plots import save_figure
from .questionnaire import dynamic_demographic_rows, numeric_items, nps_summary
from .tables import export_table
from .users_time import users_time_file, validate_users_time_file
from .visualization.theme import BRAND_COLORS, get_brand_palette, style_axis


ORDINAL_1_3_LABELS = {1: "Bassa", 2: "Media", 3: "Alta", "1": "Bassa", "2": "Media", "3": "Alta", "1.0": "Bassa", "2.0": "Media", "3.0": "Alta"}


def oet_by_task(config: dict) -> dict[str, float]:
    return {str(task.get("id")): float(task["oet_seconds"]) for task in config.get("users_time", {}).get("tasks", []) if task.get("oet_seconds")}


def generate_final_assets(config: dict, data: dict[str, pd.DataFrame]) -> None:
    generate_problem_evaluator_outputs(config, data)
    generate_expertise_matrix_assets(config)
    generate_questionnaire_item_outputs(config, data)
    generate_nps_breakdown(config, data)
    generate_users_time_task_assets(config)
    generate_sample_assets(config, data)
    generate_expert_demographics(config)
    generate_subgroup_assets(config, data)
    export_questionnaire_final_aliases()


def _problem_id_column(df: pd.DataFrame) -> str:
    for column in ["Problem ID", "Codice problema", df.columns[0] if len(df.columns) else "Problem ID"]:
        if column in df.columns:
            return column
    return df.columns[0]


def _ids(value: object) -> list[str]:
    return [part.strip() for part in str(value).split("-") if part and part.strip() and part.strip().lower() != "nan"]


def _evaluator_ids(value: object) -> list[str]:
    return list(dict.fromkeys(re.findall(r"\bE[DU]\d+\b", str(value).upper())))


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


def _problem_evaluator_matrix_mode(config: dict) -> str:
    mode = (
        config.get("heuristics", {})
        .get("problem_evaluator_matrix", {})
        .get("mode")
    )
    slide_config_path = resolve_path("slides/config/slide_deck.yml")
    if slide_config_path.exists():
        try:
            with slide_config_path.open("r", encoding="utf-8") as fh:
                slide_config = yaml.safe_load(fh) or {}
            mode = (
                slide_config.get("heuristics", {})
                .get("problem_evaluator_matrix", {})
                .get("mode", mode)
            )
        except Exception:
            pass
    normalized = str(mode or "presence").strip().casefold()
    return "severity" if normalized == "severity" else "presence"


def _plot_problem_evaluator_matrix(
    heat: pd.DataFrame,
    *,
    system: str,
    config: dict,
    mode: str,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(max(9, heat.shape[1] * 0.45), max(4.2, heat.shape[0] * 0.38)))
    if mode == "severity":
        sns.heatmap(
            heat,
            cmap="YlOrRd",
            vmin=0,
            vmax=4,
            cbar_kws={"label": "Severita 0-4"},
            linewidths=0.4,
            linecolor="#E5E7EB",
            ax=ax,
        )
    else:
        present = heat.apply(pd.to_numeric, errors="coerce").fillna(0).gt(0).astype(int)
        app_color = get_brand_palette(config).get(system, "#60A5FA")
        cmap = ListedColormap([BRAND_COLORS["dark_background"], app_color])
        sns.heatmap(
            present,
            cmap=cmap,
            vmin=0,
            vmax=1,
            cbar=False,
            linewidths=0.4,
            linecolor="#334155",
            ax=ax,
        )
    style_axis(ax, f"Matrice problemi-valutatori {system}", "Problemi finali", "Valutatori")
    return fig


def _problem_finder_matrix(subset: pd.DataFrame, expert_cols: list[str], problem_ids: list[str]) -> pd.DataFrame:
    presence = pd.DataFrame(0, index=expert_cols, columns=problem_ids, dtype=int)
    for row in subset.itertuples(index=False):
        problem_id = str(getattr(row, "problem_id", ""))
        if problem_id not in presence.columns:
            continue
        for evaluator_id in _evaluator_ids(getattr(row, "notes", "")):
            if evaluator_id in presence.index:
                presence.loc[evaluator_id, problem_id] = 1
    return presence


def _final_problem_evaluator_outputs(config: dict) -> bool:
    problems_path = resolve_path("data/processed/heuristics/clean_problems.csv")
    matrix_path = resolve_path("data/processed/heuristics/expert_problem_matrix.csv")
    if not problems_path.exists() or not matrix_path.exists():
        return False

    problems = pd.read_csv(problems_path, encoding="utf-8-sig")
    ratings = pd.read_csv(matrix_path, encoding="utf-8-sig")
    if problems.empty or ratings.empty or "problem_id" not in problems.columns or "problem_id" not in ratings.columns:
        return False

    expert_cols = [column for column in ratings.columns if re.fullmatch(r"E[DU]\d+", str(column))]
    if not expert_cols:
        return False

    problem_columns = ["problem_id", "app", "notes"]
    for column in problem_columns:
        if column not in problems.columns:
            problems[column] = ""
    merged = problems[problem_columns].merge(ratings[["problem_id", *expert_cols]], on="problem_id", how="left")
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    matrix_mode = _problem_evaluator_matrix_mode(config)
    coverage_rows = []
    text_lines = ["# Copertura problemi euristici", ""]
    for system in systems:
        slug = system.lower()
        subset = merged[merged["app"].astype(str).str.casefold() == system.casefold()].copy()
        if subset.empty:
            continue

        subset["problem_order"] = subset["problem_id"].astype(str).str.extract(r"(\d+)").astype(int)
        subset = subset.sort_values("problem_order")
        problem_ids = subset["problem_id"].astype(str).tolist()
        heat = subset.set_index("problem_id")[expert_cols].T.apply(pd.to_numeric, errors="coerce")
        heat = heat.reindex(columns=problem_ids)
        finder_heat = _problem_finder_matrix(subset, expert_cols, problem_ids)

        matrix = finder_heat.copy() if matrix_mode == "presence" else heat.copy()
        if matrix_mode == "presence":
            matrix["total_by_evaluator"] = matrix.sum(axis=1)
        else:
            matrix["mean_by_evaluator"] = matrix.mean(axis=1).round(2)
        export_table(matrix.reset_index(names="evaluator"), f"outputs/tables/problem_evaluator_matrix_{slug}.csv", 2)

        fig = _plot_problem_evaluator_matrix(finder_heat if matrix_mode == "presence" else heat, system=system, config=config, mode=matrix_mode)
        save_figure(fig, f"outputs/figures/heuristics/problem_evaluator_matrix_{slug}.png", config)

        problem_means = heat.mean(axis=0).sort_values(ascending=False)
        evaluator_means = heat.mean(axis=1).sort_values(ascending=False)
        top_problem = str(problem_means.index[0]) if not problem_means.empty else "n.d."
        top_mean = float(problem_means.iloc[0]) if not problem_means.empty else 0.0
        finder_counts = finder_heat.sum(axis=1).sort_values(ascending=False)
        top_evaluators = ", ".join(finder_counts.head(2).index.astype(str)) if matrix_mode == "presence" and not finder_counts.empty else ", ".join(evaluator_means.head(2).index.astype(str)) if not evaluator_means.empty else "n.d."
        resolve_path(f"outputs/texts/snippets/problem_evaluator_matrix_{slug}.md").write_text(
            f"# Matrice problemi-valutatori {system}\n\n"
            f"La matrice usa i {len(problem_ids)} problemi finali e gli {len(expert_cols)} valutatori ufficiali. "
            f"Modalita visuale: {'presenza del ritrovamento' if matrix_mode == 'presence' else 'severita 0-4'}. "
            f"Il problema con severita media piu alta e `{top_problem}` ({top_mean:.2f}/4). "
            f"{'I valutatori con piu ritrovamenti sono' if matrix_mode == 'presence' else 'I valutatori con media piu alta sono'} {top_evaluators}.\n",
            encoding="utf-8",
        )

        coverage_rows.append(
            {
                "system": system,
                "problem_count": len(problem_ids),
                "evaluator_count": len(expert_cols),
                "rating_cells": int(heat.notna().sum().sum()),
                "finder_cells": int(finder_heat.sum().sum()),
                "matrix_mode": matrix_mode,
                "top_mean_problem": top_problem,
                "top_mean_severity": round(top_mean, 2),
            }
        )
        if matrix_mode == "presence":
            text_lines.append(f"- {system}: {len(problem_ids)} problemi finali x {len(expert_cols)} valutatori = {int(finder_heat.sum().sum())} ritrovamenti. Modalita matrice: {matrix_mode}.")
        else:
            text_lines.append(f"- {system}: {len(problem_ids)} problemi finali x {len(expert_cols)} valutatori = {int(heat.notna().sum().sum())} valutazioni di severita. Modalita matrice: {matrix_mode}.")

    if not coverage_rows:
        return False
    export_table(pd.DataFrame(coverage_rows), "outputs/tables/heuristics_problem_coverage.csv", 2)
    resolve_path("outputs/texts/snippets/heuristics_problem_coverage.md").write_text("\n".join(text_lines) + "\n", encoding="utf-8")
    return True


def generate_problem_evaluator_outputs(config: dict, data: dict[str, pd.DataFrame]) -> None:
    if _final_problem_evaluator_outputs(config):
        return

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
        resolve_path(f"outputs/texts/snippets/problem_evaluator_matrix_{slug}.md").write_text(
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
    resolve_path("outputs/texts/snippets/heuristics_problem_coverage.md").write_text("\n".join(text_lines) + "\n", encoding="utf-8")


def generate_expertise_matrix_assets(config: dict) -> None:
    profiles = _load_final_expert_profiles()
    if profiles.empty:
        return
    required = {"evaluator_id", "expert_group", "usability_experience", "domain_experience"}
    if profiles.empty or not required.issubset(profiles.columns):
        return

    slide_columns = [
        "evaluator_id",
        "expert_group",
        "gender",
        "age_group",
        "occupation",
        "familiarity",
        "usability_experience",
        "domain_experience",
    ]
    slide_table = profiles[[column for column in slide_columns if column in profiles.columns]].copy()
    export_table(slide_table, "outputs/tables/heuristics_expert_profiles.csv", 2)
    export_table(slide_table, "data/processed/heuristics/expert_profiles.csv", 2)
    evaluators_slide = slide_table.rename(
        columns={
            "evaluator_id": "Valutatore",
            "expert_group": "Gruppo",
            "gender": "Genere",
            "age_group": "Eta",
            "occupation": "Occupazione",
            "familiarity": "Familiarita",
            "usability_experience": "Esperienza usabilita",
            "domain_experience": "Esperienza dominio",
        }
    )
    export_table(evaluators_slide, "outputs/tables/heuristics_evaluators_slide.csv", 2)

    plot_df = profiles.copy()
    plot_df["usability_score"] = plot_df["usability_experience"].map(_experience_score)
    plot_df["domain_score"] = plot_df["domain_experience"].map(_experience_score)
    plot_df = plot_df[(plot_df["usability_score"] > 0) & (plot_df["domain_score"] > 0)]
    if plot_df.empty:
        return

    fig, ax = plt.subplots(figsize=(8.8, 6.2))
    fig.patch.set_facecolor("#111827")
    ax.set_facecolor("#F2F4F6")
    ax.set_xlim(0, 10.8)
    ax.set_ylim(0, 10.8)
    ax.axvline(5, color="#CBD5E1", linestyle=":", linewidth=2.2, alpha=0.85)
    ax.axhline(5, color="#CBD5E1", linestyle=":", linewidth=2.2, alpha=0.85)
    arrow_style = dict(arrowstyle="-|>", color="#020617", linewidth=4, mutation_scale=24, shrinkA=0, shrinkB=0)
    ax.add_patch(FancyArrowPatch((0.65, 0.65), (10.35, 0.65), **arrow_style))
    ax.add_patch(FancyArrowPatch((0.65, 0.65), (0.65, 10.35), **arrow_style))
    ax.set_xticks([0, 5, 10], ["0", "5", "10"])
    ax.set_yticks([0, 5, 10], ["0", "5", "10"])
    ax.tick_params(axis="both", colors="#111827", labelsize=10, length=0)

    palette = {"EU": "#75A9FF", "ED": "#F2A7D9"}
    for _, row in plot_df.sort_values("evaluator_id").iterrows():
        evaluator = str(row["evaluator_id"])
        group = str(row.get("expert_group") or evaluator[:2]).upper()
        color = palette.get(group, "#CBD5E1")
        jitter_x, jitter_y = _expertise_marker_offset(evaluator)
        x = float(row["domain_score"]) + jitter_x
        y = float(row["usability_score"]) + jitter_y
        _draw_person_marker(ax, x, y, color)
        label_x, label_y = _expertise_label_position(evaluator, x, y)
        ax.text(
            label_x,
            label_y,
            evaluator,
            ha="center",
            va="top",
            fontsize=12,
            fontweight="bold",
            color="#F8FAFC",
            bbox={"boxstyle": "round,pad=0.15", "facecolor": "#111827", "edgecolor": "none", "alpha": 0.72},
            zorder=6,
        )

    ax.text(5.5, -0.18, "ESPERIENZA DI DOMINIO", ha="center", va="top", fontsize=16, fontweight="bold", color="#F8FAFC", transform=ax.get_xaxis_transform())
    ax.text(-0.06, 0.52, "ESPERIENZA DI USABILITA", ha="right", va="center", rotation=90, fontsize=16, fontweight="bold", color="#F8FAFC", transform=ax.transAxes)
    ax.set_title("Matrice di expertise dei valutatori", fontsize=18, fontweight="bold", color="#F8FAFC", pad=16)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(False)
    save_figure(fig, "outputs/figures/heuristics/expertise_matrix.png", config)

    counts = profiles["expert_group"].fillna("n.d.").value_counts().to_dict()
    resolve_path("outputs/texts/snippets/heuristics_expertise_matrix.md").write_text(
        "# Matrice di expertise\n\n"
        f"La matrice posiziona {len(plot_df)} valutatori rispetto a esperienza di usabilita ed esperienza di dominio. "
        f"Distribuzione gruppi: {counts}.\n",
        encoding="utf-8",
    )


def _load_final_expert_profiles() -> pd.DataFrame:
    ratings_path = resolve_path("data/formbricks_raw/heuristics/severity_ratings_export.csv")
    rows: list[dict[str, object]] = []
    if ratings_path.exists():
        ratings = pd.read_csv(ratings_path, encoding="utf-8-sig")
        columns = list(ratings.columns)
        id_col = _find_profile_column(columns, ["id esperto", "evaluator"])
        gender_col = _find_profile_column(columns, ["genere"])
        age_col = _find_profile_column(columns, ["eta", "età"])
        occupation_col = _find_profile_column(columns, ["professione", "occupazione"])
        familiarity_col = _find_profile_column(columns, ["familiarita", "familiarità"])
        usability_col = _find_profile_column(columns, ["usabilita", "usabilità"])
        domain_col = _find_profile_column(columns, ["dominio"])
        for _, row in ratings.iterrows():
            evaluator_id = str(row.get(id_col, "")).strip() if id_col else ""
            if not evaluator_id:
                continue
            rows.append(
                {
                    "evaluator_id": evaluator_id,
                    "expert_group": re.match(r"^[A-Za-z]+", evaluator_id).group(0).upper() if re.match(r"^[A-Za-z]+", evaluator_id) else "",
                    "gender": row.get(gender_col, "") if gender_col else "",
                    "age_group": row.get(age_col, "") if age_col else "",
                    "occupation": row.get(occupation_col, "") if occupation_col else "",
                    "familiarity": row.get(familiarity_col, "") if familiarity_col else "",
                    "usability_experience": row.get(usability_col, "") if usability_col else "",
                    "domain_experience": row.get(domain_col, "") if domain_col else "",
                }
            )
    profiles = pd.DataFrame(rows).drop_duplicates("evaluator_id") if rows else pd.DataFrame()
    if len(profiles) >= 8:
        return profiles.sort_values("evaluator_id", key=lambda s: s.map(_expertise_sort_key)).reset_index(drop=True)

    profiles_path = resolve_path("data/processed/heuristics/expert_profiles.csv")
    if profiles_path.exists():
        fallback = pd.read_csv(profiles_path)
        if "expert_group" not in fallback.columns and "evaluator_id" in fallback.columns:
            fallback["expert_group"] = fallback["evaluator_id"].astype(str).str.extract(r"^([A-Za-z]+)", expand=False).str.upper()
        return fallback
    return profiles


def _find_profile_column(columns: list[str], aliases: list[str]) -> str:
    for column in columns:
        normalized = _normalize_profile_text(column)
        if any(_normalize_profile_text(alias) in normalized for alias in aliases):
            return column
    return ""


def _normalize_profile_text(value: object) -> str:
    text = str(value).casefold()
    replacements = {"à": "a", "è": "e", "é": "e", "ì": "i", "ò": "o", "ù": "u"}
    for source, target in replacements.items():
        text = text.replace(source, target)
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _experience_score(value: object) -> float:
    text = str(value).strip().casefold()
    levels = {"bassa": 2.5, "media": 5.0, "alta": 8.0}
    if text in levels:
        return levels[text]
    match = re.search(r"\d+(?:[.,]\d+)?", text)
    return float(match.group(0).replace(",", ".")) if match else 0.0


def _draw_person_marker(ax, x: float, y: float, color: str) -> None:
    ax.add_patch(Ellipse((x, y - 0.06), width=0.78, height=0.52, facecolor=color, edgecolor="none", alpha=0.94, zorder=3))
    ax.add_patch(Circle((x, y + 0.34), radius=0.25, facecolor=color, edgecolor="#F8FAFC", linewidth=1.8, zorder=4))


def _expertise_label_position(evaluator_id: str, x: float, y: float) -> tuple[float, float]:
    positions = {
        "ED1": (8.65, 7.00),
        "ED2": (6.80, 5.88),
        "ED3": (6.24, 7.22),
        "ED4": (9.44, 8.28),
        "EU1": (6.34, 8.58),
        "EU2": (7.42, 7.10),
        "EU3": (5.00, 6.98),
        "EU4": (7.12, 8.92),
    }
    return positions.get(evaluator_id, (x, y - 0.62))


def _expertise_marker_offset(evaluator_id: str) -> tuple[float, float]:
    offsets = {
        "ED1": (0.65, -0.08),
        "ED2": (-0.20, -0.28),
        "ED3": (-0.58, -0.10),
        "ED4": (0.18, 0.06),
        "EU1": (-0.58, 0.14),
        "EU2": (0.34, -0.15),
        "EU3": (0.00, 0.00),
        "EU4": (0.05, 0.48),
    }
    return offsets.get(evaluator_id, (0.0, 0.0))


def _expertise_sort_key(value: object) -> tuple[str, int, str]:
    text = str(value)
    match = re.match(r"^([A-Za-z]+)(\d+)$", text)
    if not match:
        return (text, 0, text)
    prefix, number = match.groups()
    return (prefix.upper(), int(number), text)


def generate_questionnaire_item_outputs(config: dict, data: dict[str, pd.DataFrame]) -> None:
    systems = [(config["project"]["system_1"], data.get("questionnaire_system_1", pd.DataFrame())), (config["project"]["system_2"], data.get("questionnaire_system_2", pd.DataFrame()))]
    item_frames = {system: numeric_items(df, config) for system, df in systems if not df.empty}
    if len(item_frames) < 2:
        return
    names = list(item_frames)
    common_items = [item for item in item_frames[names[0]].index if item in item_frames[names[1]].index]
    rows = []
    descriptive_rows = []
    interpretation_rows = []
    for idx, item in enumerate(common_items, start=1):
        left_raw = pd.to_numeric(item_frames[names[0]].loc[item], errors="coerce")
        right_raw = pd.to_numeric(item_frames[names[1]].loc[item], errors="coerce")
        left = left_raw.dropna()
        right = right_raw.dropna()
        paired = _paired_questionnaire_values(item_frames[names[0]], item_frames[names[1]], item, names[0], names[1])
        if len(paired) >= 2 and not np.allclose(paired[names[0]], paired[names[1]], equal_nan=True):
            p_value = float(stats.wilcoxon(paired[names[0]], paired[names[1]]).pvalue)
        elif len(paired):
            p_value = 1.0
        else:
            p_value = pd.NA
        test_name = "Wilcoxon signed-rank"
        left_desc = _item_desc_row(idx, item, names[0], left)
        right_desc = _item_desc_row(idx, item, names[1], right)
        descriptive_rows.extend([left_desc, right_desc])
        interpretation_rows.append(_item_interpretation_row(idx, item, names[0], names[1], left_desc, right_desc))
        row = {
            "item_number": idx,
            "item": item,
            f"{names[0]}_mean": left.mean(),
            f"{names[1]}_mean": right.mean(),
            f"{names[0]}_median": left.median(),
            f"{names[1]}_median": right.median(),
            "mean_difference_abs": abs(left.mean() - right.mean()),
            "median_difference_abs": abs(left.median() - right.median()),
            "test_name": test_name,
            "paired_n": int(len(paired)),
            "p_value": p_value,
        }
        rows.append(row)
        plot_df = pd.DataFrame({"system": [names[0]] * len(left) + [names[1]] * len(right), "score": list(left) + list(right)})
        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        sns.boxplot(data=plot_df, x="system", y="score", hue="system", palette=get_brand_palette(config), legend=False, ax=ax)
        ax.set_ylim(config["analysis"]["ueq_scale_min"], config["analysis"]["ueq_scale_max"])
        style_axis(ax, f"Item {idx:02d}: {item}", "", "Valutazione")
        save_figure(fig, f"outputs/figures/questionnaire/items/item_{idx:02d}_boxplot.png", config)
        _copy_questionnaire_chart_alias(
            f"outputs/figures/questionnaire/items/item_{idx:02d}_boxplot.png",
            f"outputs/charts/questionnaire_item_{idx:02d}_boxplot.png",
        )
        slide_table = _questionnaire_item_slide_table(left_desc, right_desc, test_name, len(paired), p_value)
        export_table(slide_table, f"outputs/tables/questionnaire_item_{idx:02d}_descriptives.csv", 2)
        _plot_questionnaire_item_table(slide_table, f"outputs/charts/questionnaire_item_{idx:02d}_table.png")
    summary = pd.DataFrame(rows)
    if summary.empty:
        return
    descriptives = pd.DataFrame(descriptive_rows)
    interpretations = pd.DataFrame(interpretation_rows)
    summary["rank_score"] = summary["p_value"].fillna(1).rank(method="first") + summary["median_difference_abs"].rank(ascending=False) * 0.01
    relevant = summary.sort_values(["p_value", "median_difference_abs", "mean_difference_abs"], ascending=[True, False, False]).head(8)
    export_table(summary.drop(columns=["rank_score"]), "outputs/tables/questionnaire_items_summary.csv", 2)
    export_table(summary.drop(columns=["rank_score"]), "outputs/tables/markdown/questionnaire_items_summary.md", 2)
    export_table(relevant.drop(columns=["rank_score"]), "outputs/tables/questionnaire_most_relevant_items.csv", 2)
    export_table(descriptives, "outputs/tables/questionnaire_item_descriptives.csv", 2)
    export_table(interpretations, "outputs/tables/questionnaire_item_interpretations.csv", 2)
    _write_profile_effectiveness_questionnaire_report(descriptives, interpretations)
    lines = ["# Item UEQ più rilevanti", ""]
    for row in relevant.itertuples():
        significance = "significativa" if pd.notna(row.p_value) and row.p_value < 0.05 else "non significativa"
        lines.append(f"- Item {row.item_number:02d} `{row.item}`: differenza media assoluta {row.mean_difference_abs:.2f}, p={row.p_value:.4f}; differenza {significance}.")
    resolve_path("outputs/texts/snippets/questionnaire_selected_items.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _paired_questionnaire_values(left_items: pd.DataFrame, right_items: pd.DataFrame, item: str, left_name: str, right_name: str) -> pd.DataFrame:
    common_columns = [column for column in left_items.columns if column in right_items.columns]
    if common_columns:
        left = pd.to_numeric(left_items.loc[item, common_columns], errors="coerce")
        right = pd.to_numeric(right_items.loc[item, common_columns], errors="coerce")
    else:
        left = pd.to_numeric(left_items.loc[item], errors="coerce")
        right = pd.to_numeric(right_items.loc[item], errors="coerce")
    return pd.DataFrame({left_name: left, right_name: right}).dropna()


def _questionnaire_item_slide_table(left_desc: dict[str, object], right_desc: dict[str, object], test_name: str, paired_n: int, p_value: object) -> pd.DataFrame:
    def value(row: dict[str, object], key: str) -> object:
        item = row.get(key)
        return round(float(item), 2) if pd.notna(item) and isinstance(item, (int, float, np.integer, np.floating)) else item

    rows = [
        {
            "App": str(row["app"]),
            "Min": value(row, "min"),
            "Q1": value(row, "q1"),
            "Media": value(row, "mean"),
            "Mediana": value(row, "median"),
            "Q3": value(row, "q3"),
            "Max": value(row, "max"),
        }
        for row in [left_desc, right_desc]
    ]
    return pd.DataFrame(rows)


def _plot_questionnaire_item_table(table: pd.DataFrame, target: str | Path) -> Path:
    path = resolve_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.4, 5.15))
    fig.patch.set_facecolor("#111827")
    ax.set_facecolor("#111827")
    ax.axis("off")
    display = table.astype(str).values.tolist()
    table_artist = ax.table(
        cellText=display,
        colLabels=list(table.columns),
        loc="center",
        cellLoc="center",
        colLoc="center",
        colWidths=[0.22, *([0.13] * (len(table.columns) - 1))],
    )
    table_artist.auto_set_font_size(False)
    table_artist.set_fontsize(9.2)
    table_artist.scale(1, 1.33)
    for (row, _col), cell in table_artist.get_celld().items():
        cell.set_edgecolor("#334155")
        cell.set_linewidth(0.8)
        if row == 0:
            cell.set_facecolor("#0F172A")
            cell.get_text().set_color("#F8FAFC")
            cell.get_text().set_weight("bold")
        else:
            cell.set_facecolor("#111827" if row % 2 else "#172033")
            cell.get_text().set_color("#E5E7EB")
    fig.tight_layout(pad=0.25)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="#111827")
    plt.close(fig)
    return path


def _write_profile_effectiveness_questionnaire_report(descriptives: pd.DataFrame, interpretations: pd.DataFrame) -> Path:
    target = resolve_path("outputs/reports/final_report_user_profile_effectiveness_questionnaire_fix.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    profiles_path = resolve_path("data/user_profiles.csv")
    profiles = pd.read_csv(profiles_path, encoding="utf-8-sig") if profiles_path.exists() else pd.DataFrame()
    mcnemar_path = resolve_path("outputs/tables/user_test_effectiveness_mcnemar.csv")
    mcnemar = pd.read_csv(mcnemar_path, encoding="utf-8-sig") if mcnemar_path.exists() else pd.DataFrame()
    item_ids = sorted(descriptives["item_id"].dropna().astype(int).unique()) if "item_id" in descriptives else []
    missing_items = [item for item in range(1, 27) if item not in item_ids]
    profile_slides = [f"Profilo degli utenti coinvolti - {index}/4" for index in range(1, 5)]
    lines = [
        "# Controllo fix profilo utenti, efficacia e questionario",
        "",
        f"- Numero utenti caricati nel profilo utenti: {profiles['user_id'].nunique() if 'user_id' in profiles else 0}",
        "- Slide profilo utenti generate:",
        *[f"  - {slide}" for slide in profile_slides],
        "- Matrice expertise utenti rimossa: si",
        "- Definizione efficacia: task completati / task totali, includendo successi con aiuto o criticita.",
        "- Definizione efficacia assoluta: solo successi pieni senza aiuto o criticita / task totali.",
        "",
        "## P-value efficacia",
        mcnemar.to_markdown(index=False) if not mcnemar.empty else "Nessun p-value disponibile.",
        "",
        "## Questionario",
        f"- Numero domande questionario generate: {len(item_ids)}",
        f"- Item mancanti: {', '.join(map(str, missing_items)) if missing_items else 'nessuno'}",
        "- Statistiche min/q1/media/mediana/q3/max presenti per ogni item: "
        + ("si" if {"min", "q1", "mean", "median", "q3", "max"}.issubset(descriptives.columns) and not missing_items else "no"),
        f"- Interpretazioni generate: {len(interpretations)}",
        "",
        "## Warning",
        "Nessun warning rilevante." if not missing_items else f"Item mancanti: {', '.join(map(str, missing_items))}",
        "",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def _item_desc_row(item_id: int, item_label: str, app: str, values: pd.Series) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "item_label": item_label,
        "app": app,
        "min": values.min(),
        "q1": values.quantile(0.25),
        "mean": values.mean(),
        "median": values.median(),
        "q3": values.quantile(0.75),
        "max": values.max(),
        "variance": values.var(ddof=1),
        "std": values.std(ddof=1),
        "n": int(values.count()),
    }


def _item_interpretation_row(item_id: int, item_label: str, left_app: str, right_app: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_mean = float(left.get("mean", pd.NA))
    right_mean = float(right.get("mean", pd.NA))
    winner = left_app if left_mean > right_mean else right_app if right_mean > left_mean else "parita"
    diff = left_mean - right_mean
    if winner == "parita":
        text = f"Per l'item {item_label} le medie sono allineate; la lettura va fatta sulla dispersione e sulle mediane."
    else:
        text = (
            f"Per l'item {item_label}, {winner} mostra un punteggio piu alto "
            f"({left_mean:.2f} vs {right_mean:.2f}), con differenza media pari a {diff:.2f}. "
            "L'interpretazione resta sulla scala originale dell'item e non assume automaticamente che il valore piu alto sia migliore."
        )
    return {
        "item_id": item_id,
        "item_label": item_label,
        "mean_deliveroo": left_mean if left_app == "Deliveroo" else right_mean,
        "mean_glovo": right_mean if right_app == "Glovo" else left_mean,
        "mean_diff": diff,
        "winner_raw": winner,
        "interpretation_text": text,
    }


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
        resolve_path(f"outputs/texts/snippets/user_tests_{slug}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_sample_assets(config: dict, data: dict[str, pd.DataFrame]) -> None:
    df1 = data.get("questionnaire_system_1", pd.DataFrame())
    df2 = data.get("questionnaire_system_2", pd.DataFrame())
    df = df1 if not df1.empty else df2
    if df.empty:
        return
    user_cols = [c for c in df.columns if c != "item"]
    assert len(user_cols) == 24, f"Expected 24 unique users, found {len(user_cols)}"

    sample_rows = []
    fields = ["genere", "eta", "familiarita delivery", "familiarita con app di delivery", "situazione lavorativa", "istruzione"]
    for field in fields:
        if field in df.index:
            counts = df.loc[field].astype(str).value_counts().reset_index()
            counts.columns = ["value", "count"]
            counts["field"] = field
            assert counts["count"].sum() == 24, f"Expected total count of 24, but got {counts['count'].sum()} for field {field}"
            sample_rows.append(counts)
    if not sample_rows:
        return
    all_counts = pd.concat(sample_rows, ignore_index=True)
    export_table(all_counts, "outputs/tables/sample_composition.csv", 2)
    field_map = {
        "genere": ("gender_distribution", "Genere utenti (n = 24)"),
        "eta": ("age_distribution", "Fascia d'eta utenti (n = 24)"),
        "familiarita delivery": ("familiarity_distribution", "Familiarita food delivery (n = 24)"),
        "familiarita con app di delivery": ("familiarity_distribution", "Familiarita food delivery (n = 24)"),
        "situazione lavorativa": ("occupation_distribution", "Occupazione utenti (n = 24)"),
    }
    done = set()
    for field, (filename, title) in field_map.items():
        subset = all_counts[all_counts["field"] == field]
        if subset.empty or filename in done:
            continue
        done.add(filename)
        fig, ax = plt.subplots(figsize=(7.5, 5.4))
        _draw_demographic_pie(ax, subset, title)
        save_figure(fig, f"outputs/figures/sample/{filename}.png", config)
    resolve_path("outputs/texts/snippets/sample_description.md").write_text(
        "# Composizione campione\n\nIl campione dei partecipanti è composto da 24 utenti che hanno valutato entrambi i sistemi.\n",
        encoding="utf-8",
    )


def generate_expert_demographics(config: dict) -> None:
    profiles = _load_final_expert_profiles()
    if profiles.empty:
        return
    assert profiles["evaluator_id"].nunique() == 8, f"Expected 8 unique experts, found {profiles['evaluator_id'].nunique()}"

    field_map = {
        "gender": ("expert_gender_distribution", "Genere valutatori (n = 8)", "outputs/charts/experts_gender_pie.png"),
        "age_group": ("expert_age_distribution", "Fascia d'eta valutatori (n = 8)", "outputs/charts/experts_age_pie.png"),
        "occupation": ("expert_occupation_distribution", "Occupazione valutatori (n = 8)", "outputs/charts/experts_occupation_pie.png"),
        "familiarity": ("expert_familiarity_distribution", "Familiarita delivery valutatori (n = 8)", "outputs/charts/experts_delivery_familiarity_pie.png"),
    }

    expert_rows = []
    for field, (filename, title, chart_alias) in field_map.items():
        if field in profiles.columns:
            counts = profiles[field].replace("", pd.NA).dropna().astype(str).value_counts().reset_index()
            counts.columns = ["value", "count"]
            counts["field"] = field
            assert counts["count"].sum() == 8, f"Expected count of 8 for expert field {field}, got {counts['count'].sum()}"
            expert_rows.append(counts)

            fig, ax = plt.subplots(figsize=(7.5, 5.4))
            _draw_demographic_pie(ax, counts, title)
            save_figure(fig, f"outputs/figures/heuristics/{filename}.png", config)
            fig, ax = plt.subplots(figsize=(7.5, 5.4))
            _draw_demographic_pie(ax, counts, title)
            save_figure(fig, chart_alias, config)
            _copy_dark_variant_to_root(chart_alias)

    if expert_rows:
        all_expert_counts = pd.concat(expert_rows, ignore_index=True)
        export_table(all_expert_counts, "outputs/tables/expert_composition.csv", 2)


def _draw_demographic_pie(ax: plt.Axes, counts: pd.DataFrame, title: str) -> None:
    counts = counts.copy()
    counts["value"] = counts["value"].map(_ordinal_label)
    counts = counts.groupby("value", as_index=False)["count"].sum()
    values = pd.to_numeric(counts["count"], errors="coerce").fillna(0)
    labels = counts["value"].astype(str).tolist()
    total = int(values.sum())
    colors = sns.color_palette("Set2", n_colors=max(3, len(labels)))
    wedges, _, autotexts = ax.pie(
        values,
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


def _ordinal_label(value: object) -> str:
    return ORDINAL_1_3_LABELS.get(value, ORDINAL_1_3_LABELS.get(str(value).strip(), str(value)))


def _copy_dark_variant_to_root(path: str | Path) -> None:
    target = resolve_path(path)
    dark = target.parent / "dark" / target.name
    if dark.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dark, target)


def _copy_questionnaire_chart_alias(source: str | Path, target: str | Path) -> None:
    source_path = resolve_path(source)
    target_path = resolve_path(target)
    figures_root = resolve_path("outputs/figures")
    try:
        relative = source_path.relative_to(figures_root)
    except ValueError:
        relative = Path(source_path.name)

    dark_source = figures_root / "dark" / relative
    presentation_source = figures_root / "presentation" / relative
    root_source = source_path if source_path.exists() else dark_source
    variants = [
        (root_source, target_path),
        (dark_source, target_path.parent / "dark" / target_path.name),
        (presentation_source, target_path.parent / "presentation" / target_path.name),
    ]
    for src, dst in variants:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def generate_subgroup_assets(config: dict, data: dict[str, pd.DataFrame]) -> None:
    subgroup_path = resolve_path("outputs/tables/markdown/subgroup_analysis.md")
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
    resolve_path("outputs/texts/snippets/subgroup_conclusions.md").write_text(f"# Analisi sottogruppi\n\n{warning}\n", encoding="utf-8")


def export_questionnaire_final_aliases() -> None:
    aliases = {
        "outputs/figures/dark/sample/gender_distribution.png": "outputs/plots/questionnaire/demographics_gender.png",
        "outputs/figures/dark/sample/age_distribution.png": "outputs/plots/questionnaire/demographics_age.png",
        "outputs/figures/dark/sample/occupation_distribution.png": "outputs/plots/questionnaire/demographics_profession.png",
        "outputs/figures/dark/sample/familiarity_distribution.png": "outputs/plots/questionnaire/familiarity_delivery.png",
        "outputs/figures/dark/questionnaire/ueq_scales.png": "outputs/plots/questionnaire/ueq_dimensions_by_app.png",
        "outputs/figures/dark/questionnaire/nps_comparison.png": "outputs/plots/questionnaire/nps_by_app.png",
    }
    for source_raw, target_raw in aliases.items():
        source = resolve_path(source_raw)
        if not source.exists():
            continue
        target = resolve_path(target_raw)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    summary = resolve_path("data/processed/questionnaire/questionnaire_ueq_summary.csv")
    nps = resolve_path("data/processed/questionnaire/questionnaire_nps_summary.csv")
    lines = ["# Questionnaire summary", ""]
    if summary.exists():
        df = pd.read_csv(summary)
        for row in df.itertuples(index=False):
            app = getattr(row, "app", "")
            dimension = getattr(row, "dimension", "")
            mean = getattr(row, "mean_score_minus3_plus3", "")
            lines.append(f"- {app} - {dimension}: media UEQ normalizzata {mean}.")
    if nps.exists():
        df = pd.read_csv(nps)
        for row in df.itertuples(index=False):
            lines.append(f"- {row.app}: NPS {row.nps} su {row.n_responses} risposte.")
    target = resolve_path("outputs/texts/questionnaire_summary.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
