from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .config import ensure_output_dirs, load_config
from .data_loading import load_all
from .export import create_templates
from .heuristics import clean_heuristics, priority_table, summarize_heuristics
from .plots import (
    plot_distribution,
    plot_effectiveness,
    plot_effectiveness_ci,
    plot_efficiency_boxplot,
    plot_efficiency_violin,
    plot_nps,
    plot_ueq_summary,
)
from .questionnaire import item_summary, nps_summary, subgroup_summary, ueq_summary
from .tables import export_table
from .user_tests import compute_effectiveness, compute_efficiency, compute_user_test_statistics
from .validation import (
    format_validation,
    validate_heuristics_csv,
    validate_questionnaire_csv,
    validate_users_time_csv,
)


def validate(config: dict, data: dict[str, pd.DataFrame]) -> str:
    messages = []
    messages.extend(validate_users_time_csv(data["users_time"], config))
    messages.extend(validate_heuristics_csv(data["heuristics_system_1"]))
    messages.extend(validate_heuristics_csv(data["heuristics_system_2"]))
    messages.extend(validate_questionnaire_csv(data["questionnaire_system_1"], config))
    messages.extend(validate_questionnaire_csv(data["questionnaire_system_2"], config))
    return format_validation(messages)


def analyze(config: dict, data: dict[str, pd.DataFrame]) -> None:
    ensure_output_dirs(config)
    paths = config["paths"]
    decimals = config["analysis"]["round_decimals"]
    systems = [config["project"]["system_1"], config["project"]["system_2"]]

    effectiveness = compute_effectiveness(data["users_time"], config)
    efficiency_long, efficiency_summary = compute_efficiency(data["users_time"], config)
    export_table(effectiveness, Path(paths["output_tables"]) / "user_test_effectiveness.csv", decimals)
    export_table(effectiveness, Path(paths["output_tables_md"]) / "user_test_effectiveness.md", decimals)
    export_table(efficiency_summary, Path(paths["output_tables"]) / "user_test_efficiency.csv", decimals)
    export_table(efficiency_summary, Path(paths["output_tables_md"]) / "user_test_efficiency.md", decimals)
    plot_effectiveness(effectiveness, config, Path(paths["output_figures"]) / "user_tests/effectiveness_deliveroo_vs_glovo.png")
    plot_effectiveness_ci(effectiveness, config, Path(paths["output_figures"]) / "user_tests/effectiveness_confidence_interval.png")
    plot_efficiency_boxplot(efficiency_long, config, Path(paths["output_figures"]) / "user_tests/efficiency_boxplot.png")
    plot_efficiency_violin(efficiency_long, config, Path(paths["output_figures"]) / "user_tests/efficiency_violinplot.png")

    heur_summary, heuristic_dist, category_dist = summarize_heuristics(
        data["heuristics_system_1"], data["heuristics_system_2"], config
    )
    cleaned_heuristics = pd.concat(
        [
            clean_heuristics(data["heuristics_system_1"], systems[0]),
            clean_heuristics(data["heuristics_system_2"], systems[1]),
        ],
        ignore_index=True,
    )
    export_table(heur_summary, Path(paths["output_tables"]) / "heuristics_summary.csv", decimals)
    export_table(heur_summary, Path(paths["output_tables_md"]) / "heuristics_summary.md", decimals)
    export_table(priority_table(cleaned_heuristics), Path(paths["output_tables_md"]) / "problems_priority_table.md", decimals)
    plot_distribution(heuristic_dist, "heuristic", config, Path(paths["output_figures"]) / "heuristics/heuristics_distribution.png", "Distribuzione euristiche")
    plot_distribution(category_dist, "category", config, Path(paths["output_figures"]) / "heuristics/heuristics_by_category.png", "Euristiche per categoria")

    item_stats = pd.concat(
        [item_summary(data["questionnaire_system_1"], systems[0]), item_summary(data["questionnaire_system_2"], systems[1])],
        ignore_index=True,
    )
    ueq = pd.concat(
        [ueq_summary(data["questionnaire_system_1"], systems[0]), ueq_summary(data["questionnaire_system_2"], systems[1])],
        ignore_index=True,
    )
    nps = pd.concat(
        [nps_summary(data["questionnaire_system_1"], systems[0]), nps_summary(data["questionnaire_system_2"], systems[1])],
        ignore_index=True,
    )
    subgroup = pd.concat(
        [
            subgroup_summary(data["questionnaire_system_1"], systems[0]),
            subgroup_summary(data["questionnaire_system_2"], systems[1]),
        ],
        ignore_index=True,
    )
    export_table(item_stats, Path(paths["output_tables"]) / "questionnaire_item_summary.csv", decimals)
    export_table(ueq, Path(paths["output_tables"]) / "ueq_summary.csv", decimals)
    export_table(ueq, Path(paths["output_tables_md"]) / "ueq_summary.md", decimals)
    export_table(nps, Path(paths["output_tables"]) / "nps_summary.csv", decimals)
    export_table(nps, Path(paths["output_tables_md"]) / "nps_summary.md", decimals)
    if not subgroup.empty:
        export_table(subgroup, Path(paths["output_tables_md"]) / "subgroup_analysis.md", decimals)
    plot_ueq_summary(ueq, config, Path(paths["output_figures"]) / "questionnaire/ueq_scales.png")
    plot_nps(nps, config, Path(paths["output_figures"]) / "questionnaire/nps_comparison.png")

    snippets = compute_user_test_statistics(data["users_time"], config)
    Path(paths["output_text"]).mkdir(parents=True, exist_ok=True)
    Path(paths["output_text"], "user_test_summary.txt").write_text("\n".join(snippets), encoding="utf-8")
    Path(paths["output_text"], "final_comparison_summary.txt").write_text(
        f"Pipeline completata per {systems[0]} vs {systems[1]}. Consultare outputs/figures e outputs/tables_md.",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="HCI project analysis toolkit")
    parser.add_argument("command", choices=["validate", "analyze", "create-templates", "all"])
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    if args.command == "create-templates":
        create_templates()
        print("Template CSV creati in data/templates")
        return
    data = load_all(config)
    if args.command in {"validate", "all"}:
        print(validate(config, data))
    if args.command in {"analyze", "all"}:
        analyze(config, data)
        print("Analisi completata. Output salvati in outputs/.")


if __name__ == "__main__":
    main()
