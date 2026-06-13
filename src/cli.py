from __future__ import annotations

import argparse
import shutil
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
    analyze_final_heuristics_dataset,
    import_severity_formbricks,
    import_heuristics_raw_survey,
    join_clean_problems_with_ratings,
    parse_severity_ratings,
    run_severity_pipeline,
    validate_clean_problems,
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
from .real_inputs import prepare_real_inputs
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
from .slide_export.pdf_export import PdfExportError, export_pptx_to_pdf
from .user_tests import analyze_user_testing_observations, compute_effectiveness, compute_efficiency, compute_user_test_statistics
from .users_time import analyze_users_time, users_time_enabled, users_time_file, validate_users_time_file
from .validation import (
    format_validation,
    validate_heuristics_csv,
    validate_questionnaire_csv,
    validate_users_time_csv,
)

GENERATED_OUTPUT_PATHS = [
    "outputs/figures",
    "outputs/reports",
    "outputs/slides",
    "outputs/slide_assets",
    "outputs/tables",
    "outputs/texts",
    "outputs/texts/snippets",
    "outputs/texts/analysis",
    "outputs/import_report.md",
    "outputs/reference_model_pages.txt",
    "outputs/slide_manifest.json",
    "outputs/slide_manifest.md",
    # Legacy output layout, kept here so one clean run removes old clutter.
    "outputs/generated_report_sections",
    "outputs/slide_pack",
    "outputs/tables_md",
    "outputs/text",
    "outputs/text_snippets",
    "reports",
]

OUTPUT_KEEP_FILES = [
    "outputs/.gitkeep",
    "outputs/reports/.gitkeep",
    "outputs/tables/markdown/.gitkeep",
    "outputs/texts/analysis/.gitkeep",
    "outputs/texts/snippets/.gitkeep",
    "reports/.gitkeep",
]


def _existing(path: str | Path | None) -> Path | None:
    if not path:
        return None
    target = resolve_path(path)
    return target if target.exists() else None


def clean_generated_outputs(config: dict) -> list[Path]:
    root = resolve_path(".").resolve()
    removed: list[Path] = []
    for raw_path in GENERATED_OUTPUT_PATHS:
        target = resolve_path(raw_path).resolve()
        if not target.exists():
            continue
        if target == root or root not in target.parents:
            raise RuntimeError(f"Refusing to remove outside project root: {target}")
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        removed.append(target)
    ensure_output_dirs(config)
    for keep in OUTPUT_KEEP_FILES:
        keep_path = resolve_path(keep)
        keep_path.parent.mkdir(parents=True, exist_ok=True)
        keep_path.touch()
    return removed


def import_formbricks_available(config: dict, include_unfinished: bool = False) -> bool:
    paths = config.get("paths", {})
    q_path = _existing(paths.get("questionnaire_raw")) or _existing(config.get("formbricks", {}).get("questionnaire", {}).get("export_path"))
    h_path = _existing(paths.get("heuristics_raw"))
    ratings_path = _existing(paths.get("heuristics_ratings"))
    if q_path:
        convert_questionnaire_export(q_path, config, include_unfinished=include_unfinished)
        print(f"OK: questionario importato da {q_path}")
    else:
        print("WARNING: CSV questionario Formbricks non trovato, uso eventuali file data/raw esistenti.")
    if h_path:
        import_heuristics_raw_survey(h_path, config=config)
        print(f"OK: survey euristica raw importata da {h_path}. Completa data/processed/heuristics/consolidated_problems.csv prima della survey severità.")
    else:
        print("WARNING: CSV euristiche raw Formbricks non trovato, uso eventuali file euristiche gia consolidati.")
    return False


def full_pipeline(config: dict, include_unfinished: bool = False) -> None:
    print("HCI Toolkit - Full Pipeline")
    clean_generated_outputs(config)
    ensure_output_dirs(config)
    print("\n[1/7] Import Formbricks CSV...")
    import_formbricks_available(config, include_unfinished)
    print("\n[2/7] Validazione dati...")
    data = load_all(config)
    print(validate(config, data))
    print("\n[3/7] Analisi, grafici e tabelle...")
    analyze(config, data)
    sync_clean_figure_alias()
    print("OK: analisi completata")
    print("\n[4/8] Asset finali granulari...")
    data = load_all(config)
    generate_final_assets(config, data)
    analyze_ueq_benchmark(config)
    print("OK: asset finali generati")
    run_optional_final_heuristics(strict=False)
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
    print(resolve_path("outputs/slide_assets/pack/00_index.md"))


def run_optional_final_heuristics(strict: bool = False) -> None:
    problems = resolve_path("data/processed/heuristics/clean_problems.csv")
    ratings = resolve_path("data/formbricks_raw/heuristics/severity_ratings_export.csv")
    if problems.exists() and ratings.exists():
        result = run_severity_pipeline(problems_path=problems, ratings_export_path=ratings, strict=strict)
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        print("OK: pipeline euristiche finale inclusa.")
        return
    message = "Pipeline euristiche finale saltata: servono data/processed/heuristics/clean_problems.csv e data/formbricks_raw/heuristics/severity_ratings_export.csv."
    if strict:
        raise SystemExit(message)
    print(f"WARNING: {message}")


def generate_report(config: dict) -> None:
    """Generate normalized report assets without assembling the PPTX deck."""
    clean_generated_outputs(config)
    ensure_output_dirs(config)
    data = load_all(config)
    print(validate(config, data))
    analyze(config, data)
    sync_clean_figure_alias()
    generate_final_assets(config, data)
    analyze_ueq_benchmark(config)
    generate_text_outputs(config)
    generate_slide_manifest()
    build_slide_pack(config)
    print("Report assets generati in outputs/.")


def heuristics_cli(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description="HCI heuristics pipeline")
    sub = parser.add_subparsers(dest="phase", required=True)

    raw = sub.add_parser("raw", help="Importa survey Formbricks grezza degli esperti")
    raw.add_argument("--input", default="data/raw/formbricks/heuristics_experts_raw.csv")
    raw.add_argument("--config", default="config.yaml")
    raw.add_argument("--mapping", default="config/heuristics_raw_mapping.yml")

    severity = sub.add_parser("severity", help="Importa survey severità sui problemi consolidati")
    severity.add_argument("--ratings", default="data/raw/formbricks/heuristics_severity_ratings.csv")
    severity.add_argument("--problems", default="data/processed/heuristics/consolidated_problems.csv")

    all_cmd = sub.add_parser("all", help="Esegue raw e, se disponibile, severity")
    all_cmd.add_argument("--input", default="data/raw/formbricks/heuristics_experts_raw.csv")
    all_cmd.add_argument("--ratings", default="data/raw/formbricks/heuristics_severity_ratings.csv")
    all_cmd.add_argument("--problems", default="data/processed/heuristics/consolidated_problems.csv")
    all_cmd.add_argument("--config", default="config.yaml")
    all_cmd.add_argument("--mapping", default="config/heuristics_raw_mapping.yml")

    validate_clean = sub.add_parser("validate-clean", help="Valida data/processed/heuristics/clean_problems.csv")
    validate_clean.add_argument("--problems", default="data/processed/heuristics/clean_problems.csv")

    import_severity = sub.add_parser("import-severity-formbricks", help="Importa export wide Formbricks in formato long")
    import_severity.add_argument("--input", default="data/formbricks_raw/heuristics/severity_ratings_export.csv")
    import_severity.add_argument("--output", default="data/processed/heuristics/problem_ratings_long.csv")
    import_severity.add_argument("--problems", default=None)
    import_severity.add_argument("--strict", action="store_true")

    join_severity = sub.add_parser("join-severity", help="Unisce clean_problems.csv e problem_ratings_long.csv")
    join_severity.add_argument("--problems", default="data/processed/heuristics/clean_problems.csv")
    join_severity.add_argument("--ratings", default="data/processed/heuristics/problem_ratings_long.csv")
    join_severity.add_argument("--output", default="data/processed/heuristics/heuristic_final_dataset.csv")
    join_severity.add_argument("--strict", action="store_true")

    analyze_final_cmd = sub.add_parser("analyze-final", help="Genera output finali dalla tabella joined")
    analyze_final_cmd.add_argument("--dataset", default="data/processed/heuristics/heuristic_final_dataset.csv")
    analyze_final_cmd.add_argument("--out", default="outputs/heuristics")

    severity_pipeline = sub.add_parser("severity-pipeline", help="Esegue validazione, import Formbricks, join e output finali")
    severity_pipeline.add_argument("--problems", default="data/processed/heuristics/clean_problems.csv")
    severity_pipeline.add_argument("--ratings-export", default="data/formbricks_raw/heuristics/severity_ratings_export.csv")
    severity_pipeline.add_argument("--out", default="outputs/heuristics")
    severity_pipeline.add_argument("--strict", action="store_true")

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
        print("Pipeline severità euristiche completata.")
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
            print("Pipeline raw completata. Fase 2 saltata: serve il CSV severità e `data/processed/heuristics/consolidated_problems.csv`.")
        return
    if args.phase == "validate-clean":
        result = validate_clean_problems(args.problems)
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        if result.errors:
            for error in result.errors:
                print(f"ERROR: {error}")
            raise SystemExit(1)
        print("OK: clean_problems.csv valido.")
        return
    if args.phase == "import-severity-formbricks":
        ratings, warnings = import_severity_formbricks(args.input, output_path=args.output, problems_path=args.problems, strict=args.strict)
        for warning in warnings:
            print(f"WARNING: {warning}" if not warning.startswith("File generato") else warning)
        print(f"OK: importate {len(ratings)} valutazioni.")
        return
    if args.phase == "join-severity":
        final, warnings = join_clean_problems_with_ratings(args.problems, args.ratings, output_path=args.output, strict=args.strict)
        for warning in warnings:
            print(f"WARNING: {warning}" if not warning.startswith("File generato") else warning)
        print(f"OK: dataset finale generato con {len(final)} righe.")
        return
    if args.phase == "analyze-final":
        result = analyze_final_heuristics_dataset(args.dataset, out_dir=args.out)
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        print("OK: output finali euristiche generati.")
        print(resolve_path(args.out))
        return
    if args.phase == "severity-pipeline":
        result = run_severity_pipeline(problems_path=args.problems, ratings_export_path=args.ratings_export, out_dir=args.out, strict=args.strict)
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        print("OK: pipeline severità euristiche completata.")
        print(resolve_path(args.out))
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
        f"Pipeline completata per {systems[0]} vs {systems[1]}. Consultare outputs/figures e outputs/tables/markdown.",
        encoding="utf-8",
    )
    if users_time_enabled(config):
        users_time_path = users_time_file(config)
        if users_time_path.exists():
            analyze_users_time(config, users_time_path)
            analyze_user_testing_observations()
            print("OK: analisi users_time completata")
        else:
            print(f"[users-time] File non trovato: {users_time_path}")
            print("[users-time] Analisi saltata. Usa create-templates per generare un template.")


def sync_clean_figure_alias() -> None:
    dark_root = resolve_path("outputs/figures/dark")
    clean_root = resolve_path("outputs/figures/clean")
    if not dark_root.exists():
        return
    clean_root.mkdir(parents=True, exist_ok=True)
    for source in dark_root.rglob("*"):
        if not source.is_file():
            continue
        target = clean_root / source.relative_to(dark_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def export_pdf_or_exit(pptx_path: str | Path) -> None:
    try:
        result = export_pptx_to_pdf(pptx_path)
    except PdfExportError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"PDF generato: {result.pdf_path}")


FULL_PIPELINE_SLIDE_CONFIGS = [
    "slides/config/slide_deck.yml",
    "slides/config/user_task_deck.yml",
]


def generate_full_pipeline_slide_decks(*, overwrite: bool = False, timestamp: bool = False) -> list[SlideGenerationResult]:
    results = []
    for slide_config in FULL_PIPELINE_SLIDE_CONFIGS:
        results.append(generate_slides(slide_config, overwrite=overwrite, timestamp=timestamp))
    return results


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
            "clean-outputs",
            "generate-slides",
            "validate-slide-template",
            "validate-slide-assets",
            "create-templates",
            "all",
            "full-pipeline",
            "import-formbricks",
            "import-formbricks-questionnaire",
            "import-formbricks-heuristics",
            "import-formbricks-heuristics-discovery",
            "import-formbricks-heuristics-ratings",
            "build-heuristics-review",
            "build-heuristics-from-review",
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
            "prepare-real-inputs",
        ],
    )
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--input", help="Path CSV Formbricks da importare")
    parser.add_argument("--output", help="Path CSV normalizzato da generare")
    parser.add_argument("--template", help="Template PPTX da usare per generate-slides")
    parser.add_argument("--output-dir", help="Cartella output per i CSV finali")
    parser.add_argument("--source-dir", default="data/inbox", help="Cartella sorgente per prepare-real-inputs")
    parser.add_argument("--mapping", default="config/heuristics_raw_mapping.yml", help="Mapping colonne per import euristiche raw Formbricks")
    parser.add_argument("--plot-style", choices=["dark", "presentation", "both"], help="Stile grafici da esportare")
    parser.add_argument("--overwrite", action="store_true", help="Sovrascrive template esistenti quando supportato")
    parser.add_argument("--strict", action="store_true", help="Per generate-slides: fallisce se mancano asset richiesti")
    parser.add_argument("--auto", action="store_true", help="Per generate-slides: genera prima gli asset report se mancano")
    parser.add_argument("--timestamp", action="store_true", help="Per generate-slides: aggiunge timestamp al nome output")
    parser.add_argument("--generate-slides", action="store_true", help="Per full-pipeline: genera anche il PPTX finale")
    parser.add_argument("--export-pdf", action="store_true", help="Esporta anche il PDF della presentazione finale")
    parser.add_argument("--no-export-pdf", action="store_true", help="Salta esplicitamente l'export PDF")
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
    if args.command == "prepare-real-inputs":
        status = prepare_real_inputs(args.source_dir, config, overwrite=args.overwrite)
        for warning in status.warnings:
            print(f"WARNING: {warning}")
        for error in status.errors:
            print(f"ERROR: {error}")
        print(resolve_path("outputs/reports/real_input_status.md"))
        print(f"STATUS: {status.data_status}")
        if status.errors:
            raise SystemExit(1)
        return
    if args.command == "validate-users-time":
        path = resolve_path(args.input) if args.input else users_time_file(config)
        result = validate_users_time_file(
            path,
            required_columns=config.get("users_time", {}).get("required_columns"),
            tasks=config.get("users_time", {}).get("tasks", []),
        )
        print("\n".join(result.messages))
        print(resolve_path("outputs/reports/users_time_validation_report.md"))
        return
    if args.command == "validate-slide-template":
        target = args.template or "slides/templates/Deliveroo_vs_Glovo_clean_python_ready_template.pptx"
        messages = validate_template_structure(target)
        if messages:
            print("\n".join(messages))
            raise SystemExit(1)
        print(f"OK: template slide valido: {resolve_path(target)}")
        return
    if args.command == "validate-slide-assets":
        messages = validate_slide_assets("slides/config/slide_deck.yml", template_path=args.template)
        if messages:
            print("\n".join(messages))
            raise SystemExit(1)
        print("OK: asset slide validi")
        return
    if args.command == "clean-outputs":
        removed = clean_generated_outputs(config)
        print("Output generati rimossi:")
        for path in removed:
            print(path)
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
        if args.export_pdf and not args.no_export_pdf:
            export_pdf_or_exit(result.output)
        return
    if args.command == "analyze-users-time":
        path = resolve_path(args.input) if args.input else users_time_file(config)
        if not path.exists():
            print(f"[users-time] File non trovato: {path}")
            print("[users-time] Analisi saltata. Usa create-templates per generare un template.")
            validate_users_time_file(
                path,
                required_columns=config.get("users_time", {}).get("required_columns"),
                tasks=config.get("users_time", {}).get("tasks", []),
            )
            return
        analyze_users_time(config, path)
        print("Analisi users_time completata.")
        return
    if args.command == "full-pipeline":
        full_pipeline(config, include_unfinished=args.include_unfinished)
        if args.generate_slides or args.export_pdf:
            try:
                results = generate_full_pipeline_slide_decks(overwrite=args.overwrite, timestamp=args.timestamp)
            except SlideGenerationError as exc:
                raise SystemExit(str(exc)) from exc
            for result in results:
                print(format_slide_generation_summary(result))
                if args.export_pdf and not args.no_export_pdf:
                    export_pdf_or_exit(result.output)
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
        print("Slide pack generato in outputs/slide_assets/pack/.")
        if args.export_pdf and not args.no_export_pdf:
            try:
                result = generate_slides(overwrite=True, timestamp=args.timestamp)
            except SlideGenerationError as exc:
                raise SystemExit(str(exc)) from exc
            print(format_slide_generation_summary(result))
            export_pdf_or_exit(result.output)
        return
    if args.command == "quality-check":
        ready = run_quality_check(config)
        report_path = resolve_path("outputs/reports/final_quality_check.md")
        status_line = "STATUS: NEEDS_FIXES"
        if report_path.exists():
            for line in report_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("STATUS:"):
                    status_line = line
        print(report_path)
        print(status_line)
        return
    if args.command == "import-formbricks":
        import_formbricks_available(config, include_unfinished=args.include_unfinished)
        return
    if args.command in {"import-formbricks-heuristics", "import-formbricks-heuristics-discovery"}:
        source = args.input or config.get("paths", {}).get("heuristics_raw") or "data/formbricks_raw/heuristics_discovery/formbricks_heuristics_discovery_demo_6_experts.csv"
        result = import_heuristics_raw_survey(source, config=config, mapping_path=args.mapping)
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        print("Survey euristica discovery importata.")
        print(resolve_path("data/processed/heuristics_candidates.csv"))
        print(resolve_path("data/processed/heuristics_review.csv"))
        return
    if args.command in {"build-heuristics-review", "build-heuristics-from-review"}:
        review_path = resolve_path(args.input or "data/processed/heuristics_review.csv")
        if not review_path.exists():
            raise SystemExit(f"File review non trovato: {review_path}. Lancia prima import-formbricks-heuristics-discovery.")
        review = pd.read_csv(review_path)
        if "problem_group_id" not in review.columns:
            raise SystemExit("Il file review deve contenere la colonna problem_group_id.")
        print("Review euristiche pronta per la survey ratings.")
        print(review_path)
        return
    if args.command == "import-formbricks-heuristics-ratings":
        ratings = args.input or config.get("paths", {}).get("heuristics_ratings") or "data/formbricks_raw/heuristics_ratings/formbricks_heuristics_ratings_demo_6_experts.csv"
        demo_problems = resolve_path("data/templates/heuristics_consolidated_problems_demo.csv")
        problems = args.output or (demo_problems if demo_problems.exists() else "data/templates/heuristics_consolidated_problems_template.csv")
        result = parse_severity_ratings(ratings, problems)
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        print("Survey euristica ratings importata.")
        print(resolve_path("data/processed/heuristics/final_problem_summary.csv"))
        return
    if args.command == "import-any-form":
        if not args.input:
            raise SystemExit("import-any-form richiede --input per rilevare il tipo di form.")
        preview = load_formbricks_export(args.input)
        column_text = " ".join(comparable(column) for column in preview.columns)
        if "heuristic" in column_text or "euristic" in column_text or "severità" in column_text or "severity" in column_text:
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
        sync_clean_figure_alias()
        if args.command in {"all", "all-from-formbricks"}:
            run_optional_final_heuristics(strict=args.strict)
        print("Analisi completata. Output salvati in outputs/.")
    if args.command in {"all", "all-from-formbricks", "export-text"}:
        generate_text_outputs(config)
        print("Testi generati in outputs/texts/snippets.")
    if args.command in {"all", "all-from-formbricks", "export-slide-assets"}:
        data = load_all(config)
        generate_final_assets(config, data)
        analyze_ueq_benchmark(config)
        generate_slide_manifest()
        build_slide_pack(config)
        print("Manifest e slide pack generati.")


if __name__ == "__main__":
    main()
