from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from .config import ensure_output_dirs, load_config, resolve_path
from .asset_manifest import build_assets_manifest
from .benchmark import analyze_ueq_benchmark
from .data_loading import load_all
from .export import create_templates
from .final_assets import generate_final_assets
from .formbricks_adapter import comparable, convert_questionnaire_export, load_formbricks_export
from .formbricks_heuristics_pipeline import (
    import_heuristics_raw_survey,
    parse_severity_ratings,
    write_consolidated_problems_template,
)
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
from .quality_check import run_quality_check
from .slide_pack import build_slide_pack
from .tables import export_table
from .text_generation.final_summary_text import generate_text_outputs
from .slide_export.slide_manifest import generate_slide_manifest
from .slide_export.pptx_generator import (
    SlideGenerationError,
    format_slide_generation_summary,
    generate_slides,
    validate_slide_assets,
    validate_template_structure,
)
from .user_tests import compute_effectiveness, compute_efficiency, compute_user_test_statistics
from .users_time import analyze_users_time, users_time_enabled, users_time_file, validate_users_time_file
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


def import_formbricks_available(config: dict, include_unfinished: bool = False) -> bool:
    paths = config.get("paths", {})
    q_path = _existing(paths.get("questionnaire_raw")) or _existing(config.get("formbricks", {}).get("questionnaire", {}).get("export_path"))
    h_path = _existing("data/raw/formbricks/heuristics_experts_raw.csv")
    if q_path:
        convert_questionnaire_export(q_path, config, include_unfinished=include_unfinished)
        print(f"OK: questionario importato da {q_path}")
    else:
        print("WARNING: CSV questionario Formbricks non trovato, uso eventuali file data/raw esistenti.")
    if h_path:
        import_heuristics_raw_survey(h_path, config=config)
        print(f"OK: survey euristica raw importata da {h_path}. Completa data/processed/heuristics/consolidated_problems.csv prima della survey severita.")
    else:
        print("WARNING: CSV euristiche raw Formbricks non trovato, uso eventuali file euristiche gia consolidati.")
    return False


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
    print("\n[4/8] Asset finali granulari...")
    data = load_all(config)
    generate_final_assets(config, data)
    analyze_ueq_benchmark(config)
    print("OK: asset finali generati")
    print("\n[5/8] Testi slide/report...")
    generate_text_outputs(config)
    print("OK: testi generati")
    print("\n[6/8] Slide pack...")
    generate_slide_manifest()
    build_slide_pack(config)
    print("OK: slide pack generato")
    print("\n[7/8] Report import...")
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
    print("\n[8/8] Quality check...")
    run_quality_check(config)
    print(resolve_path("outputs/reports/final_quality_check.md"))
    print("\nOutput principale:")
    print(resolve_path("outputs/slide_pack/00_index.md"))


def generate_report(config: dict) -> None:
    """Generate normalized report assets without assembling the PPTX deck."""
    ensure_output_dirs(config)
    data = load_all(config)
    print(validate(config, data))
    analyze(config, data)
    generate_final_assets(config, data)
    analyze_ueq_benchmark(config)
    generate_text_outputs(config)
    generate_slide_manifest()
    build_slide_pack(config)
    print("Report assets generati in outputs/.")


def generate_demo_assets() -> None:
    import matplotlib.pyplot as plt

    graph_dir = resolve_path("outputs/demo/graphs")
    table_dir = resolve_path("outputs/demo/tables")
    text_dir = resolve_path("outputs/demo/text")
    graph_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(["Deliveroo", "Glovo"], [82, 76], color=["#00CCBC", "#FFC244"])
    ax.set_ylabel("Score")
    ax.set_title("Demo comparison")
    ax.set_ylim(0, 100)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(graph_dir / "demo_graph.png", dpi=180)
    plt.close(fig)

    pd.DataFrame(
        [
            {"Metric": "Task Success Rate", "Deliveroo": "92%", "Glovo": "85%", "p-value": "0.042", "Significance": "Significant"},
            {"Metric": "Time on Task", "Deliveroo": "45.2", "Glovo": "58.1", "p-value": "0.001", "Significance": "High"},
        ]
    ).to_csv(table_dir / "demo_stats.csv", index=False)
    (text_dir / "demo_findings.md").write_text(
        "Il deck demo conferma che il generatore legge testo, grafici e tabelle da asset gia prodotti.",
        encoding="utf-8",
    )
    print("Demo assets generati in outputs/demo/.")


def heuristics_cli(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description="HCI heuristics pipeline")
    sub = parser.add_subparsers(dest="phase", required=True)

    raw = sub.add_parser("raw", help="Importa survey Formbricks grezza degli esperti")
    raw.add_argument("--input", default="data/raw/formbricks/heuristics_experts_raw.csv")
    raw.add_argument("--config", default="config.yaml")
    raw.add_argument("--mapping", default="config/heuristics_raw_mapping.yml")

    severity = sub.add_parser("severity", help="Importa survey severita sui problemi consolidati")
    severity.add_argument("--ratings", default="data/raw/formbricks/heuristics_severity_ratings.csv")
    severity.add_argument("--problems", default="data/processed/heuristics/consolidated_problems.csv")

    all_cmd = sub.add_parser("all", help="Esegue raw e, se disponibile, severity")
    all_cmd.add_argument("--input", default="data/raw/formbricks/heuristics_experts_raw.csv")
    all_cmd.add_argument("--ratings", default="data/raw/formbricks/heuristics_severity_ratings.csv")
    all_cmd.add_argument("--problems", default="data/processed/heuristics/consolidated_problems.csv")
    all_cmd.add_argument("--config", default="config.yaml")
    all_cmd.add_argument("--mapping", default="config/heuristics_raw_mapping.yml")

    args = parser.parse_args(argv)
    config = load_config(getattr(args, "config", "config.yaml"))
    if args.phase == "raw":
        result = import_heuristics_raw_survey(args.input, config=config, mapping_path=args.mapping)
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        print("Pipeline euristiche raw completata.")
        print(resolve_path("reports/heuristics_raw_report.md"))
        return
    if args.phase == "severity":
        result = parse_severity_ratings(args.ratings, args.problems)
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        print("Pipeline severita euristiche completata.")
        print(resolve_path("reports/heuristics_final_report.md"))
        return
    if args.phase == "all":
        raw_result = import_heuristics_raw_survey(args.input, config=config, mapping_path=args.mapping)
        for warning in raw_result.warnings:
            print(f"WARNING: {warning}")
        ratings = resolve_path(args.ratings)
        problems = resolve_path(args.problems)
        if ratings.exists() and problems.exists():
            severity_result = parse_severity_ratings(ratings, problems)
            for warning in severity_result.warnings:
                print(f"WARNING: {warning}")
            print("Pipeline euristiche completa.")
        else:
            write_consolidated_problems_template()
            print("Pipeline raw completata. Fase 2 saltata: serve il CSV severita e `data/processed/heuristics/consolidated_problems.csv`.")
        return


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
        export_table(subgroup, Path(paths["output_tables"]) / "subgroup_analysis.csv", decimals)
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
    if users_time_enabled(config):
        users_time_path = users_time_file(config)
        if users_time_path.exists():
            analyze_users_time(config, users_time_path)
            print("OK: analisi users_time completata")
        else:
            print(f"[users-time] File non trovato: {users_time_path}")
            print("[users-time] Analisi saltata. Usa create-templates per generare un template.")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "heuristics":
        heuristics_cli(sys.argv[2:])
        return
    parser = argparse.ArgumentParser(description="HCI project analysis toolkit")
    parser.add_argument(
        "command",
        choices=[
            "validate",
            "validate-users-time",
            "analyze",
            "generate-report",
            "generate-slides",
            "generate-demo-assets",
            "validate-slide-template",
            "create-templates",
            "all",
            "full-pipeline",
            "import-formbricks",
            "import-formbricks-questionnaire",
            "import-formbricks-all",
            "all-from-formbricks",
            "import-any-form",
            "export-text",
            "export-slide-assets",
            "export-tables",
            "export-figures",
            "analyze-user-tests",
            "analyze-users-time",
            "analyze-heuristics",
            "analyze-questionnaire",
            "build-slide-pack",
            "quality-check",
            "analyze-benchmark",
            "build-asset-manifest",
        ],
    )
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--input", help="Path CSV Formbricks da importare")
    parser.add_argument("--output", help="Path CSV normalizzato da generare")
    parser.add_argument("--template", help="Template PPTX da usare per generate-slides")
    parser.add_argument("--output-dir", help="Cartella output per i CSV finali")
    parser.add_argument("--mapping", default="config/heuristics_raw_mapping.yml", help="Mapping colonne per import euristiche raw Formbricks")
    parser.add_argument("--plot-style", choices=["dark", "presentation", "both"], help="Stile grafici da esportare")
    parser.add_argument("--overwrite", action="store_true", help="Sovrascrive template esistenti quando supportato")
    parser.add_argument("--strict", action="store_true", help="Per generate-slides: fallisce se mancano asset richiesti")
    parser.add_argument("--auto", action="store_true", help="Per generate-slides: genera prima gli asset report se mancano")
    parser.add_argument("--timestamp", action="store_true", help="Per generate-slides: aggiunge timestamp al nome output")
    parser.add_argument("--generate-slides", action="store_true", help="Per full-pipeline: genera anche il PPTX finale")
    parser.add_argument("--include-unfinished", action="store_true", help="Importa anche risposte non completate")
    args = parser.parse_args()
    app_config_path = "config.yaml" if args.command == "generate-slides" else args.config
    config = load_config(app_config_path)
    if args.plot_style:
        config.setdefault("visualization", {})["style"] = args.plot_style
    if args.command == "create-templates":
        created = create_templates(overwrite=args.overwrite)
        if created:
            print("Template creati/aggiornati:")
            for path in created:
                print(resolve_path(path))
        else:
            print("Nessun template sovrascritto. Usa --overwrite per rigenerare file esistenti.")
        return
    if args.command == "validate-users-time":
        path = resolve_path(args.input) if args.input else users_time_file(config)
        result = validate_users_time_file(path, required_columns=config.get("users_time", {}).get("required_columns"))
        print("\n".join(result.messages))
        print(resolve_path("outputs/reports/users_time_validation_report.md"))
        return
    if args.command == "generate-demo-assets":
        generate_demo_assets()
        return
    if args.command == "validate-slide-template":
        target = args.template or "slides/templates/Deliveroo_vs_Glovo_clean_python_ready_template.pptx"
        messages = validate_template_structure(target)
        if messages:
            print("\n".join(messages))
            raise SystemExit(1)
        print(f"OK: template slide valido: {resolve_path(target)}")
        return
    if args.command == "generate-report":
        generate_report(config)
        return
    if args.command == "generate-slides":
        slide_config_path = "slides/config/slide_deck.yml" if args.config == "config.yaml" else args.config
        missing = validate_slide_assets(slide_config_path, template_path=args.template)
        if missing and args.auto:
            print("Asset mancanti: genero prima il report.")
            generate_report(config)
            missing = validate_slide_assets(slide_config_path, template_path=args.template)
        if missing and (args.strict or not args.auto):
            raise SystemExit(
                "\n\n".join(missing)
                + "\n\nFix:\nRun `python main.py generate-report` first, or use `python main.py generate-slides --auto`."
            )
        try:
            result = generate_slides(
                slide_config_path,
                template_path=args.template,
                output_path=args.output,
                overwrite=args.overwrite,
                timestamp=args.timestamp,
            )
        except SlideGenerationError as exc:
            raise SystemExit(str(exc)) from exc
        print(format_slide_generation_summary(result))
        return
    if args.command == "analyze-users-time":
        path = resolve_path(args.input) if args.input else users_time_file(config)
        if not path.exists():
            print(f"[users-time] File non trovato: {path}")
            print("[users-time] Analisi saltata. Usa create-templates per generare un template.")
            validate_users_time_file(path, required_columns=config.get("users_time", {}).get("required_columns"))
            return
        analyze_users_time(config, path)
        print("Analisi users_time completata.")
        return
    if args.command == "full-pipeline":
        full_pipeline(config, include_unfinished=args.include_unfinished)
        if args.generate_slides:
            try:
                result = generate_slides(overwrite=args.overwrite, timestamp=args.timestamp)
            except SlideGenerationError as exc:
                raise SystemExit(str(exc)) from exc
            print(format_slide_generation_summary(result))
        return
    if args.command == "analyze-benchmark":
        analyze_ueq_benchmark(config, args.input or "data/raw/ueq_benchmark.csv")
        print("Benchmark UEQ analizzato o saltato con warning.")
        return
    if args.command == "build-asset-manifest":
        build_assets_manifest()
        print("Manifest asset generato.")
        return
    if args.command == "build-slide-pack":
        data = load_all(config)
        generate_final_assets(config, data)
        analyze_ueq_benchmark(config)
        generate_text_outputs(config)
        build_slide_pack(config)
        print("Slide pack generato in outputs/slide_pack/.")
        return
    if args.command == "quality-check":
        ready = run_quality_check(config)
        print(resolve_path("outputs/reports/final_quality_check.md"))
        print("STATUS: READY_FOR_SLIDES" if ready else "STATUS: NEEDS_FIXES")
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
            import_heuristics_raw_survey(args.input, config=config)
            print("Form rilevato come survey euristica raw e normalizzato.")
        else:
            convert_questionnaire_export(args.input, config, include_unfinished=args.include_unfinished)
            print("Form rilevato come questionario e convertito.")
        return
    if args.command == "all-from-formbricks":
        import_formbricks_available(config, include_unfinished=args.include_unfinished)
    if args.command in {"import-formbricks-questionnaire", "import-formbricks-all"}:
        convert_questionnaire_export(args.input, config, include_unfinished=args.include_unfinished)
        print("Questionario Formbricks convertito nei CSV del toolkit.")
    if args.command == "import-formbricks-all":
        source = args.input or "data/raw/formbricks/heuristics_experts_raw.csv"
        if resolve_path(source).exists():
            import_heuristics_raw_survey(source, config=config)
            print("Survey euristica raw normalizzata.")
        else:
            print("WARNING: survey euristica raw non trovata; saltata.")
    if args.command in {"import-formbricks-questionnaire", "import-formbricks-all"}:
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
        data = load_all(config)
        generate_final_assets(config, data)
        analyze_ueq_benchmark(config)
        generate_slide_manifest()
        build_slide_pack(config)
        print("Manifest e slide pack generati.")


if __name__ == "__main__":
    main()
