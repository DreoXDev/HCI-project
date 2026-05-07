from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .config import ensure_output_dirs, load_config, resolve_path
from .data_loading import load_all
from .export import create_templates
from .formbricks_adapter import comparable, convert_heuristics_export, convert_questionnaire_export, load_formbricks_export
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
from .questionnaire import item_summary, nps_summary, subgroup_summaries, ueq_summary
from .tables import export_table
from .text_generation.final_summary_text import generate_text_outputs
from .slide_export.slide_manifest import generate_slide_manifest
from .user_tests import compute_effectiveness, compute_efficiency, compute_user_test_statistics
from .validation import (
    format_validation,
    validate_heuristics_csv,
    validate_questionnaire_csv,
    validate_users_time_csv,
)


def _existing(path: str | Path | None) -> Path | None:
    if not path:
        return None
    target = resolve_path(path)
    return target if target.exists() else None


def import_formbricks_available(config: dict, include_unfinished: bool = False) -> None:
    paths = config.get("paths", {})
    q_path = _existing(paths.get("questionnaire_raw")) or _existing(config.get("formbricks", {}).get("questionnaire", {}).get("export_path"))
    h_path = _existing(paths.get("heuristics_raw")) or _existing(config.get("formbricks", {}).get("heuristics", {}).get("export_path"))
    if q_path:
        convert_questionnaire_export(q_path, config, include_unfinished=include_unfinished)
        print(f"OK: questionario importato da {q_path}")
    else:
        print("WARNING: CSV questionario Formbricks non trovato, uso eventuali file data/raw esistenti.")
    if h_path:
        convert_heuristics_export(h_path, config, include_unfinished=include_unfinished)
        print(f"OK: euristiche importate da {h_path}")
    else:
        print("WARNING: CSV euristiche Formbricks non trovato, uso eventuali file data/raw esistenti.")


def build_heuristics_from_consolidation(config: dict) -> None:
    source = resolve_path("data/processed/heuristics_consolidation_template.csv")
    if not source.exists():
        print("WARNING: file di consolidamento non trovato. Importa prima le euristiche da Formbricks.")
        return
    df = pd.read_csv(source)
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    outputs = [resolve_path(config["paths"]["heuristics_system_1"]), resolve_path(config["paths"]["heuristics_system_2"])]
    metadata = {"canonical_problem_id", "system", "canonical_title", "canonical_description", "heuristics", "linked_submission_ids", "notes"}
    evaluator_columns = [column for column in df.columns if column not in metadata]
    for system, output in zip(systems, outputs):
        subset = df[df["system"].astype(str).map(comparable).str.contains(comparable(system), na=False)]
        rows = []
        for _, row in subset.iterrows():
            out = {
                "Problem ID": row["canonical_problem_id"],
                "Problema": row["canonical_title"],
                "Euristiche": row["heuristics"],
                "Id valutatori": "-".join([col for col in evaluator_columns if pd.to_numeric(pd.Series([row[col]]), errors="coerce").fillna(0).iloc[0] > 0]),
            }
            for index, evaluator in enumerate(evaluator_columns, start=1):
                out[f"Expert {index}"] = row[evaluator]
            rows.append(out)
        output.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(output, index=False)
    print("OK: file euristiche toolkit generati dal consolidamento.")


def full_pipeline(config: dict, include_unfinished: bool = False) -> None:
    print("HCI Toolkit - Full Pipeline")
    ensure_output_dirs(config)
    print("\n[1/7] Import Formbricks CSV...")
    import_formbricks_available(config, include_unfinished)
    print("\n[2/7] Validazione dati...")
    data = load_all(config)
    print(validate(config, data))
    print("\n[3/7] Analisi, grafici e tabelle...")
    analyze(config, data)
    print("OK: analisi completata")
    print("\n[4/7] Testi slide/report...")
    generate_text_outputs(config)
    print("OK: testi generati")
    print("\n[5/7] Slide assets...")
    generate_slide_manifest()
    print("OK: slide manifest generato")
    print("\n[6/7] Report import...")
    report = resolve_path("outputs/import_report.md")
    if not report.exists():
        report.write_text(
            "\n".join(
                [
                    "# Import Report",
                    "",
                    "Nessun CSV Formbricks e stato importato in questa esecuzione.",
                    "",
                    "La pipeline ha usato i file gia presenti in `data/raw/`.",
                    "",
                    "Per usare Formbricks, salva i CSV in:",
                    "",
                    "- `data/formbricks_raw/questionnaire/export_questionario.csv`",
                    "- `data/formbricks_raw/heuristics/export_esperti.csv`",
                    "- `data/formbricks_raw/user_tests/user_tests.csv`",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    print(f"OK: {report}")
    print("\n[7/7] Output principale:")
    print(resolve_path("outputs/slide_manifest.md"))


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
        [item_summary(data["questionnaire_system_1"], systems[0], config), item_summary(data["questionnaire_system_2"], systems[1], config)],
        ignore_index=True,
    )
    ueq = pd.concat(
        [ueq_summary(data["questionnaire_system_1"], systems[0], config), ueq_summary(data["questionnaire_system_2"], systems[1], config)],
        ignore_index=True,
    )
    nps = pd.concat(
        [nps_summary(data["questionnaire_system_1"], systems[0]), nps_summary(data["questionnaire_system_2"], systems[1])],
        ignore_index=True,
    )
    subgroup = pd.concat(
        [
            subgroup_summaries(data["questionnaire_system_1"], systems[0], config),
            subgroup_summaries(data["questionnaire_system_2"], systems[1], config),
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
    if nps["total"].fillna(0).sum() > 0:
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
    parser.add_argument(
        "command",
        choices=[
            "validate",
            "analyze",
            "create-templates",
            "all",
            "full-pipeline",
            "import-formbricks",
            "import-formbricks-questionnaire",
            "import-formbricks-heuristics",
            "import-formbricks-all",
            "all-from-formbricks",
            "import-any-form",
            "export-text",
            "export-slide-assets",
            "export-tables",
            "export-figures",
            "analyze-user-tests",
            "analyze-heuristics",
            "analyze-questionnaire",
            "build-heuristics-from-consolidation",
            "suggest-heuristic-duplicates",
        ],
    )
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--input", help="Path CSV Formbricks da importare")
    parser.add_argument("--include-unfinished", action="store_true", help="Importa anche risposte non completate")
    args = parser.parse_args()
    config = load_config(args.config)
    if args.command == "create-templates":
        create_templates()
        print("Template CSV creati in data/templates")
        return
    if args.command == "full-pipeline":
        full_pipeline(config, include_unfinished=args.include_unfinished)
        return
    if args.command == "build-heuristics-from-consolidation":
        build_heuristics_from_consolidation(config)
        return
    if args.command == "suggest-heuristic-duplicates":
        print("Suggerimenti duplicati: controllare outputs/heuristic_review/possible_duplicates.md dopo import euristiche.")
        return
    if args.command == "import-formbricks":
        import_formbricks_available(config, include_unfinished=args.include_unfinished)
        return
    if args.command == "import-any-form":
        if not args.input:
            raise SystemExit("import-any-form richiede --input per rilevare il tipo di form.")
        preview = load_formbricks_export(args.input)
        column_text = " ".join(comparable(column) for column in preview.columns)
        if "heuristic" in column_text or "euristic" in column_text or "severita" in column_text or "severity" in column_text:
            convert_heuristics_export(args.input, config, include_unfinished=args.include_unfinished)
            print("Form rilevato come valutazione euristica e convertito.")
        else:
            convert_questionnaire_export(args.input, config, include_unfinished=args.include_unfinished)
            print("Form rilevato come questionario e convertito.")
        return
    if args.command == "all-from-formbricks":
        import_formbricks_available(config, include_unfinished=args.include_unfinished)
    if args.command in {"import-formbricks-questionnaire", "import-formbricks-all"}:
        convert_questionnaire_export(args.input, config, include_unfinished=args.include_unfinished)
        print("Questionario Formbricks convertito nei CSV del toolkit.")
    if args.command in {"import-formbricks-heuristics", "import-formbricks-all"}:
        convert_heuristics_export(args.input, config, include_unfinished=args.include_unfinished)
        print("Euristiche Formbricks convertite nei CSV del toolkit.")
    if args.command in {"import-formbricks-questionnaire", "import-formbricks-heuristics", "import-formbricks-all"}:
        return
    data = load_all(config)
    if args.command in {"validate", "all", "all-from-formbricks"}:
        print(validate(config, data))
    if args.command in {"analyze", "all", "all-from-formbricks", "analyze-user-tests", "analyze-heuristics", "analyze-questionnaire", "export-tables", "export-figures"}:
        analyze(config, data)
        print("Analisi completata. Output salvati in outputs/.")
    if args.command in {"all", "all-from-formbricks", "export-text"}:
        generate_text_outputs(config)
        print("Testi generati in outputs/text_snippets e outputs/generated_report_sections.")
    if args.command in {"all", "all-from-formbricks", "export-slide-assets"}:
        generate_slide_manifest()
        print("Slide assets e manifest generati.")


if __name__ == "__main__":
    main()
