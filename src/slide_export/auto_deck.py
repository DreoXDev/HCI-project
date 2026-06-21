from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from ..config import resolve_path
from .external_deck import user_task_deck_slide_specs
from .template_variants import infer_theme_from_app, resolve_template_id


SECTION_TITLES = {
    "sample": "Campione e partecipanti",
    "heuristics": "Valutazione euristica",
    "user_tests": "User test",
    "users_time": "Tempi, errori e successo",
    "questionnaire": "Questionario UEQ e NPS",
    "conclusions": "Sintesi e raccomandazioni",
    "tables": "Tabelle di supporto",
    "sources": "Mappa asset generati",
}

DEFAULT_AUTO_CONFIG = {
    "enabled": False,
    "mode": "append",
    "figure_style": "dark",
    "include_figures": True,
    "include_tables": True,
    "include_text_findings": True,
    "include_text_slides": True,
    "include_slide_pack_text": False,
    "include_sources": True,
    "reference_texts": "slides/content/reference_static_texts.md",
    "table_rows_per_slide": 12,
    "task_count": 5,
    "appendix_assets_root": "slides/assets/appendices",
    "include_empty_appendices": False,
    "include_asset_manifest": False,
    "final_delivery": False,
    "max_slides": None,
    "exclude": [],
}

APPENDIX_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def expand_auto_slides(deck_config: dict[str, Any], available_templates: set[str]) -> dict[str, Any]:
    """Expand compact auto-generation rules into concrete slide specs.

    The existing generator intentionally works with explicit slide specs. This
    adapter keeps that contract intact while allowing the YAML to request broad
    coverage of all report assets that already exist on disk.
    """

    auto = _auto_config(deck_config.get("auto_slides"))
    if not auto["enabled"]:
        return deck_config
    if deck_config.get("final_delivery"):
        auto["final_delivery"] = True
        auto["skip_missing_content"] = True

    manual_slides = list(deck_config.get("slides") or [])
    used_assets = _assets_in_specs(manual_slides)
    excludes = [str(item).replace("\\", "/").lower() for item in auto.get("exclude") or []]
    if auto.get("mode") == "reference_order":
        generated = _reference_order_specs(auto, available_templates, used_assets, excludes, deck_config)
    elif auto.get("mode") == "user_tasks":
        generated = _user_task_specs(auto, available_templates, deck_config)
    else:
        generated = _build_auto_specs(auto, available_templates, used_assets, excludes)
    max_slides = auto.get("max_slides")
    if isinstance(max_slides, int) and max_slides > 0:
        generated = generated[:max_slides]

    expanded = dict(deck_config)
    if auto.get("mode", "append") in {"replace", "reference_order"}:
        expanded["slides"] = generated
    else:
        expanded["slides"] = manual_slides + generated
    return expanded


def _auto_config(raw: Any) -> dict[str, Any]:
    if raw is True:
        return {**DEFAULT_AUTO_CONFIG, "enabled": True}
    if not isinstance(raw, dict):
        return DEFAULT_AUTO_CONFIG.copy()
    return {**DEFAULT_AUTO_CONFIG, **raw}


def _build_auto_specs(
    auto: dict[str, Any],
    available_templates: set[str],
    used_assets: set[str],
    excludes: list[str],
) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []

    def add(items: list[dict[str, Any]]) -> None:
        specs.extend(items)

    if auto.get("include_figures"):
        add(_figure_specs(auto, available_templates, used_assets, excludes))
    if auto.get("include_tables"):
        add(_table_specs(auto, available_templates, used_assets, excludes))
    if auto.get("include_text_findings"):
        if auto.get("include_text_slides"):
            add(_text_slide_specs(available_templates, excludes))
        add(_finding_specs(auto, available_templates, excludes))
    if auto.get("include_sources"):
        add(_source_specs(available_templates, specs))
    return specs


def _reference_order_specs(
    auto: dict[str, Any],
    available_templates: set[str],
    used_assets: set[str],
    excludes: list[str],
    deck_config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build a deck that follows the supplied reference presentation order.

    The reference PDF is organized as: cover, index, introduction, heuristic
    evaluation, user test, questionnaire, conclusions and appendices. This
    builder keeps that order stable and fills each slot with the best available
    project asset; missing project-specific evidence becomes an intentionally
    blank slide for manual completion.
    """

    texts = _reference_texts(auto)
    metadata = deck_config.get("metadata") or {}
    final_delivery = bool(deck_config.get("final_delivery") or auto.get("final_delivery"))
    systems = _systems_from_metadata(metadata)
    task_count = _task_count(auto)
    authors = metadata.get("authors") or texts.get("components", "Gruppo HCI")
    date = metadata.get("date") or texts.get("academic_year", "")
    specs: list[dict[str, Any]] = []

    def add(spec: dict[str, Any] | None) -> None:
        if spec is not None:
            specs.append(spec)

    add(
        {
            "template_id": "cover",
            "fields": {
                "PROJECT_TITLE": metadata.get("project_title", f"{systems[0]} vs {systems[1]}"),
                "PROJECT_SUBTITLE": metadata.get("subtitle", "Analisi trasversale di usabilità"),
                "AUTHORS": authors,
                "YEAR/DATE": date,
                "AUTHORS_DATE": f"{authors} - {date}".strip(" -"),
            },
        }
    )
    add(_text_spec("Indice", texts, "index", available_templates))

    add(_section_slide("Introduzione"))
    add(_text_spec("Descrizione del problema", texts, "problem_description", available_templates))
    add(_text_spec("Ambiente di valutazione", texts, "evaluation_environment", available_templates))
    add(_text_spec(systems[0], texts, "app_deliveroo", available_templates, theme="deliveroo"))
    add(_text_spec(systems[1], texts, "app_glovo", available_templates, theme="glovo"))

    add(_section_slide("Valutazione euristica"))
    add(_text_spec("Obiettivo", texts, "heuristic_objective", available_templates))
    add(_heuristics_set_spec(texts, available_templates))
    add(_text_spec("Valutatori", texts, "heuristic_evaluators", available_templates))
    add(_table_or_blank("Tabella dei valutatori", "outputs/tables/heuristics_evaluators_slide.csv", texts, "manual_evaluator_table", available_templates))
    add(_comparison_or_blank(
        "Composizione valutatori - dati demografici",
        "outputs/charts/experts_age_pie.png",
        "outputs/charts/experts_gender_pie.png",
        texts,
        "expert_demographics",
        available_templates,
    ))
    add(_comparison_or_blank(
        "Composizione valutatori - profilo ed esperienza",
        "outputs/charts/experts_occupation_pie.png",
        "outputs/charts/experts_delivery_familiarity_pie.png",
        texts,
        "expert_profile_experience",
        available_templates,
    ))
    add(_graph_or_blank("Matrice di expertise", "outputs/figures/dark/heuristics/expertise_matrix.png", texts, "manual_expertise_matrix", available_templates))
    add(_text_spec("Problemi riscontrati", texts, "heuristic_problems_intro", available_templates))
    add(_text_spec("Criteri di prioritizzazione", texts, "priority_criteria", available_templates))
    add(_text_spec("Classificazione in fasce di priorità", texts, "priority_bands", available_templates))
    problem_tables = _problem_table_specs(auto, texts, available_templates)
    if problem_tables:
        for spec in problem_tables:
            add(spec)
    else:
        add(_table_or_blank("Problemi rilevati", "outputs/tables/heuristics_problems_slide.csv", texts, "manual_problem_list", available_templates))
    add(_graph_or_blank("Problemi rilevanti - Deliveroo", "outputs/assets/final_report/dark/top_problems_deliveroo.png", texts, "deliveroo_relevant_problems", available_templates, theme="deliveroo"))
    add(_graph_or_blank("Problemi rilevanti - Glovo", "outputs/assets/final_report/dark/top_problems_glovo.png", texts, "glovo_relevant_problems", available_templates, theme="glovo"))
    add(_table_or_blank("Criticita trasversali comuni", "data/processed/final_report/shared_problem_themes.csv", texts, "shared_criticalities", available_templates))
    add(_graph_or_blank(
        f"Matrice problemi-valutatori {systems[0]}",
        "outputs/figures/dark/heuristics/problem_evaluator_matrix_deliveroo.png",
        texts,
        "matrix_explanation",
        available_templates,
        theme="deliveroo",
    ))
    add(_graph_or_blank(
        f"Matrice problemi-valutatori {systems[1]}",
        "outputs/figures/dark/heuristics/problem_evaluator_matrix_glovo.png",
        texts,
        "matrix_explanation",
        available_templates,
        theme="glovo",
    ))
    add(_comparison_or_blank(
        "Distribuzione delle euristiche",
        "outputs/figures/dark/heuristics/heuristics_distribution.png",
        "outputs/figures/dark/heuristics/heuristics_by_category.png",
        texts,
        "heuristic_distribution",
        available_templates,
    ))
    add(_text_spec("Valutazione quantitativa", texts, "heuristic_quantitative_conclusion", available_templates))

    add(_text_spec("Dark pattern e frizioni persuasive", texts, "dark_patterns_intro", available_templates))
    add(_table_or_blank("Dark pattern osservati - Deliveroo", "data/processed/final_report/dark_patterns_deliveroo_slide.csv", texts, "dark_patterns_deliveroo", available_templates, theme="deliveroo"))
    add(_table_or_blank("Dark pattern osservati - Glovo", "data/processed/final_report/dark_patterns_glovo_slide.csv", texts, "dark_patterns_glovo", available_templates, theme="glovo"))
    add(_text_spec("Impatto dei dark pattern sul flusso d'ordine", texts, "dark_patterns_impact", available_templates))
    add(_comparison_or_blank(
        "Sintesi della valutazione euristica",
        "outputs/assets/final_report/dark/heuristic_priority_bands.png",
        "outputs/assets/final_report/dark/heuristic_frequency_comparison.png",
        texts,
        "heuristic_final_summary",
        available_templates,
    ))

    add(_section_slide("Test utente"))
    add(_text_spec("Obiettivo", texts, "user_test_objective", available_templates))
    imported_task_deck = user_task_deck_slide_specs(auto)
    if imported_task_deck:
        for spec in imported_task_deck:
            add(spec)
    else:
        add(_text_spec("I task", texts, "user_test_tasks", available_templates))
        for task_idx in range(1, task_count + 1):
            key = f"user_task_{task_idx}"
            add(_text_spec(f"Task {task_idx}", texts, key, available_templates))
            for app, theme in ((systems[0], "deliveroo"), (systems[1], "glovo")):
                add(_text_spec(f"{app} - Task {task_idx}", texts, f"{key}_{theme}", available_templates, theme=theme))
    add(_text_spec("Composizione del campione", texts, "user_test_sample", available_templates))
    add(_table_or_blank("Profilo degli utenti coinvolti", "outputs/tables/user_profiles_slide.csv", texts, "user_demographics", available_templates))
    add(_comparison_or_blank("Composizione del campione utenti", "outputs/charts/users_age_pie.png", "outputs/charts/users_gender_pie.png", texts, "user_demographics", available_templates))
    add(_comparison_or_blank("Composizione utenti - familiarita e profilo", "outputs/charts/users_occupation_pie.png", "outputs/charts/users_delivery_familiarity_pie.png", texts, "user_familiarity_profile", available_templates))
    add(_graph_or_blank("Matrice descrittiva del profilo utenti", "outputs/charts/user_expertise_matrix.png", texts, "user_expertise_matrix", available_templates))
    add(_table_or_blank("Tabella unitaria tempi user test", "outputs/tables/user_testing_times_wide.csv", texts, "users_time_summary", available_templates))
    add(_text_spec("Legenda efficacia", texts, "effectiveness_legend", available_templates))
    add(_graph_or_blank("Efficacia stretta per task", "outputs/charts/user_test_effectiveness_strict.png", texts, "effectiveness_intro", available_templates))
    add(_graph_or_blank("Efficacia estesa per task", "outputs/charts/user_test_effectiveness_extended.png", texts, "effectiveness_intro", available_templates))
    add(_table_or_blank("Task assistite e issue", "outputs/tables/user_test_assistance_events_slide.csv", texts, "effectiveness_intro", available_templates))
    for task_idx in range(1, task_count + 1):
        task = f"t{task_idx:02d}"
        add(_graph_or_blank(f"Efficacia - Task {task_idx}", f"outputs/figures/dark/user_tests/tasks/{task}_effectiveness.png", texts, "task_result_placeholder", available_templates))
        add(_graph_or_blank(f"Errori - Task {task_idx}", f"outputs/figures/dark/user_tests/tasks/{task}_error_breakdown.png", texts, "task_error_placeholder", available_templates))
    add(_graph_or_blank("Efficienza", "outputs/figures/dark/user_tests/efficiency_boxplot.png", texts, "efficiency_intro", available_templates))
    for task_idx in range(1, task_count + 1):
        task = f"t{task_idx:02d}"
        add(_graph_or_blank(f"Efficienza - Task {task_idx}", f"outputs/charts/user_test_efficiency_task_{task_idx}.png", texts, "task_result_placeholder", available_templates))
        add(_graph_or_blank(f"Efficienza statistica - Task {task_idx}", f"outputs/assets/final_report/dark/task_efficiency_{task}.png", texts, "user_test_statistical_significance", available_templates))
    add(_comparison_or_blank(
        "Successo e distribuzione tempi",
        "outputs/figures/dark/users_time_success_rate.png",
        "outputs/figures/dark/users_time_boxplot_by_task.png",
        texts,
        "users_time_summary",
        available_templates,
    ))
    add(_comparison_or_blank(
        "Tempi, successo ed errori",
        "outputs/figures/dark/users_time_mean_by_task.png",
        "outputs/figures/dark/users_time_errors_by_task.png",
        texts,
        "users_time_summary",
        available_templates,
    ))
    add(_graph_or_blank("Confronto statistico dei task", "outputs/assets/final_report/dark/user_test_time_diff_ci.png", texts, "user_test_statistical_significance", available_templates))
    add(_table_or_blank("Confronto statistico dei task - tabella", "outputs/tables/user_test_efficiency_comparison_slide.csv", texts, "user_test_statistical_significance", available_templates))
    add(_text_spec("Efficacia ed efficienza: lettura congiunta", texts, "effectiveness_efficiency_joint", available_templates))
    add(_table_or_blank("Osservazioni qualitative durante i test", "outputs/tables/user_test_qualitative_notes.csv", texts, "qualitative_observations", available_templates))

    add(_section_slide("Questionario"))
    add(_text_spec("Introduzione al questionario", texts, "questionnaire_intro", available_templates))
    add(_text_spec("Scala UEQ e metodo di scoring", texts, "ueq_scale", available_templates))
    False and add(_comparison_or_blank(
        "Composizione utenti - familiarità e profilo",
        "outputs/figures/dark/sample/occupation_distribution.png",
        "outputs/figures/dark/sample/familiarity_distribution.png",
        texts,
        "user_familiarity_profile",
        available_templates,
    ))
    for pair in _questionnaire_item_pairs():
        add(_questionnaire_pair_spec(pair, texts, available_templates))
    add(_text_spec("Confronto tra sistemi", texts, "questionnaire_comparison_intro", available_templates))
    for item_idx in [1, 4, 9, 13, 23]:
        add(_questionnaire_item_spec(
            f"Confronto statistico - Domanda {item_idx}",
            f"outputs/figures/dark/questionnaire/items/item_{item_idx:02d}_boxplot.png",
            texts,
            "questionnaire_stat_placeholder",
            available_templates,
            item_idx=item_idx,
            statistical=True,
        ))
    add(_graph_or_blank("Confronto statistico item chiave", "outputs/assets/final_report/dark/questionnaire_top_differences.png", texts, "questionnaire_statistical_comparison", available_templates))
    add(_table_or_blank("Sintesi descrittiva per item", "data/processed/final_report/questionnaire_item_descriptive_stats.csv", texts, "questionnaire_statistical_comparison", available_templates))
    add(_text_spec("Sintesi dei risultati del questionario", texts, "questionnaire_synthesis", available_templates))
    add(_graph_or_blank("Distribuzione risposte UEQ - Deliveroo", "slides/assets/generated/ueq/ueq_distribution_deliveroo.png", texts, "ueq_summary", available_templates, theme="deliveroo"))
    add(_graph_or_blank("Distribuzione risposte UEQ - Glovo", "slides/assets/generated/ueq/ueq_distribution_glovo.png", texts, "ueq_summary", available_templates, theme="glovo"))
    add(_table_or_blank("Analisi dei dati UEQ - Deliveroo", "data/processed/final_report/ueq_item_summary_deliveroo_slide.csv", texts, "ueq_table_placeholder", available_templates, theme="deliveroo"))
    add(_table_or_blank("Analisi dei dati UEQ - Glovo", "data/processed/final_report/ueq_item_summary_glovo_slide.csv", texts, "ueq_table_placeholder", available_templates, theme="glovo"))
    add(_graph_or_blank("Media risultati UEQ - Deliveroo", "slides/assets/generated/ueq/ueq_mean_results_deliveroo.png", texts, "ueq_summary", available_templates, theme="deliveroo"))
    add(_graph_or_blank("Media risultati UEQ - Glovo", "slides/assets/generated/ueq/ueq_mean_results_glovo.png", texts, "ueq_summary", available_templates, theme="glovo"))
    add(_graph_or_blank("Comparazione con benchmark - Deliveroo", "slides/assets/generated/ueq/ueq_benchmark_deliveroo.png", texts, "ueq_interpretation", available_templates, theme="deliveroo"))
    add(_table_or_blank("Benchmark UEQ - Deliveroo", "data/processed/final_report/ueq_benchmark_deliveroo_slide.csv", texts, "ueq_interpretation", available_templates, theme="deliveroo"))
    add(_graph_or_blank("Comparazione con benchmark - Glovo", "slides/assets/generated/ueq/ueq_benchmark_glovo.png", texts, "ueq_interpretation", available_templates, theme="glovo"))
    add(_table_or_blank("Benchmark UEQ - Glovo", "data/processed/final_report/ueq_benchmark_glovo_slide.csv", texts, "ueq_interpretation", available_templates, theme="glovo"))
    add(_graph_or_blank("Confronto scale UEQ Deliveroo vs Glovo", "slides/assets/generated/ueq/ueq_scale_comparison_deliveroo_vs_glovo.png", texts, "ueq_interpretation", available_templates))
    add(_text_spec("UEQ: conferme e contraddizioni rispetto ai test", texts, "ueq_confirmations_contradictions", available_templates))
    add(_graph_or_blank("Net Promoter Score: raccomandabilita percepita", "outputs/assets/final_report/dark/nps_breakdown.png", texts, "nps_interpreted", available_templates))

    add(_section_slide("Sintesi finale"))
    add(_text_spec("Conclusioni: confronto complessivo", texts, "conclusions_overall", available_templates))
    add(_text_spec("Evidenze integrate", texts, "integrated_evidence", available_templates))
    add(_text_spec("Raccomandazioni prioritarie", texts, "priority_recommendations", available_templates))
    add(_text_spec("Verdetto finale", texts, "final_verdict_argument", available_templates))
    appendix_specs = _appendix_specs(auto, systems, texts, available_templates, task_count)
    if final_delivery:
        add(_section_slide("Appendice"))
        for spec in _final_delivery_appendix_specs(texts, available_templates):
            add(spec)
    elif appendix_specs:
        add(_section_slide("Appendici"))
        for spec in appendix_specs:
            add(spec)
    if auto.get("include_sources") and not final_delivery:
        add(_text_spec("Fonti statiche", texts, "sources", available_templates))
        add(_source_specs(available_templates, specs)[0] if _source_specs(available_templates, specs) else None)

    return _dedupe_missing_assets(specs, used_assets, excludes)


def _problem_table_specs(auto: dict[str, Any], texts: dict[str, str], available_templates: set[str]) -> list[dict[str, Any]]:
    if not _has_template(available_templates, "table_large"):
        return []
    specs = []
    for app, theme, path in [
        ("Deliveroo", "deliveroo", "outputs/tables/final_problems_deliveroo_slide.csv"),
        ("Glovo", "glovo", "outputs/tables/final_problems_glovo_slide.csv"),
    ]:
        table_path = resolve_path(path)
        if not table_path.exists():
            continue
        specs.append(
            {
                "template": "table_large",
                "theme": theme,
                "fields": {
                    "TABLE_TITLE": f"Problemi {app}",
                    "TABLE_FOOTNOTE": texts.get("problem_table_footnote", "Ordinati per priorita e severita media."),
                },
                "table": {
                    "placeholder": "TABLE_MAIN",
                    "source": _rel(table_path),
                    "max_rows": int(auto.get("problem_tables", {}).get("max_rows_per_slide", 4)) if isinstance(auto.get("problem_tables"), dict) else 4,
                    "paginate": True,
                    "title_prefix": f"Problemi {app}",
                    "font_size": 6.1,
                    "header_font_size": 6.4,
                    "max_cell_chars": 220,
                    "column_widths": [0.07, 0.22, 0.44, 0.11, 0.08, 0.08],
                },
            }
        )
    return specs


def _user_task_specs(
    auto: dict[str, Any],
    available_templates: set[str],
    deck_config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build a participant-facing deck with only test instructions.

    This deck is intentionally separate from the analytical final report: it is
    meant to be shown to participants before/during the test session.
    """

    texts = _reference_texts(auto)
    metadata = deck_config.get("metadata") or {}
    systems = _systems_from_metadata(metadata)
    task_count = _task_count(auto)
    authors = metadata.get("authors") or texts.get("components", "Gruppo HCI")
    date = metadata.get("date") or texts.get("academic_year", "")
    specs: list[dict[str, Any]] = []

    def add(spec: dict[str, Any] | None) -> None:
        if spec is not None:
            specs.append(spec)

    add(
        {
            "template_id": "cover",
            "fields": {
                "PROJECT_TITLE": metadata.get("project_title", f"User test {systems[0]} vs {systems[1]}"),
                "PROJECT_SUBTITLE": metadata.get("subtitle", "Presentazione dei task per i partecipanti"),
                "AUTHORS": authors,
                "YEAR/DATE": date,
                "AUTHORS_DATE": f"{authors} - {date}".strip(" -"),
            },
        }
    )
    add(_text_spec("A cosa serve", texts, "task_deck_purpose", available_templates))
    add(_text_spec("Prima di iniziare", texts, "task_deck_before_start", available_templates))

    add(_section_slide(systems[0], theme="deliveroo"))
    for task_idx in range(1, task_count + 1):
        add(_text_spec(f"{systems[0]} - Task {task_idx}", texts, f"user_task_{task_idx}_deliveroo", available_templates, theme="deliveroo"))

    add(_section_slide(systems[1], theme="glovo"))
    for task_idx in range(1, task_count + 1):
        add(_text_spec(f"{systems[1]} - Task {task_idx}", texts, f"user_task_{task_idx}_glovo", available_templates, theme="glovo"))

    add(_text_spec("Conclusione e questionario", texts, "task_deck_survey", available_templates))
    return specs


def _figure_specs(
    auto: dict[str, Any],
    available_templates: set[str],
    used_assets: set[str],
    excludes: list[str],
) -> list[dict[str, Any]]:
    style = str(auto.get("figure_style") or "dark").strip("/") or "dark"
    root = resolve_path(f"outputs/figures/{style}")
    if not root.exists():
        root = resolve_path("outputs/figures/dark")
    figures = _existing_files(root, "*.png", used_assets, excludes)
    specs: list[dict[str, Any]] = []

    if _has_template(available_templates, "section_divider"):
        for section in _ordered_sections(figures):
            section_figures = [path for path in figures if _section_for_path(path) == section]
            specs.append(_section_slide(section))
            specs.extend(_specialized_figure_specs(section, section_figures, available_templates))
            specs.extend(_generic_graph_specs(section, section_figures, available_templates, used_assets))
    else:
        for section in _ordered_sections(figures):
            section_figures = [path for path in figures if _section_for_path(path) == section]
            specs.extend(_specialized_figure_specs(section, section_figures, available_templates))
            specs.extend(_generic_graph_specs(section, section_figures, available_templates, used_assets))
    return specs


def _specialized_figure_specs(section: str, figures: list[Path], available_templates: set[str]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    if section == "questionnaire" and _has_template(available_templates, "ueq_question"):
        item_rows = _read_dict_rows(resolve_path("outputs/tables/questionnaire_items_summary.csv"))
        by_item = {f"item_{_safe_int(row.get('item_number')):02d}_boxplot.png": row for row in item_rows if _safe_int(row.get("item_number"))}
        for figure in figures:
            if "/questionnaire/items/" not in _rel(figure):
                continue
            row = by_item.get(figure.name)
            specs.extend(_ueq_question_slides(figure, row))
    if section == "user_tests" and _has_template(available_templates, "task_results"):
        for figure in figures:
            rel = _rel(figure)
            if "/user_tests/tasks/" not in rel or not figure.name.endswith("_effectiveness.png"):
                continue
            specs.extend(_task_result_slides(figure))
    return specs


def _generic_graph_specs(
    section: str,
    figures: list[Path],
    available_templates: set[str],
    used_assets: set[str],
) -> list[dict[str, Any]]:
    if not _has_template(available_templates, "graph_full"):
        return []
    specs = []
    specialized = {spec["images"][next(iter(spec["images"]))] for spec in _specialized_figure_specs(section, figures, available_templates)}
    for figure in figures:
        rel = _rel(figure)
        if rel in used_assets or rel in specialized:
            continue
        specs.append(
            {
                "template": "graph_full",
                "theme": _theme_for_path(figure),
                "fields": {
                    "GRAPH_TITLE": _title_from_path(figure),
                    "INSIGHT_TEXT": _insight_for_figure(figure),
                },
                "images": {"GRAPH_MAIN": rel},
            }
        )
    return specs


def _table_specs(auto: dict[str, Any], available_templates: set[str], used_assets: set[str], excludes: list[str]) -> list[dict[str, Any]]:
    if not _has_template(available_templates, "table_large"):
        return []
    tables = _existing_files(resolve_path("outputs/tables"), "*.csv", used_assets, excludes)
    specs = []
    preferred_rows_per_slide = max(4, int(auto.get("table_rows_per_slide") or 12))
    for table in tables:
        rows = _read_csv_rows(table)
        rows_per_slide = _rows_per_slide_for_table(rows, preferred_rows_per_slide)
        table_options = _table_render_options(rows)
        data_rows = max(0, len(rows) - 1)
        pages = max(1, (data_rows + rows_per_slide - 1) // rows_per_slide)
        for page in range(pages):
            title = _title_from_path(table)
            if pages > 1:
                title = f"{title} ({page + 1}/{pages})"
            specs.append(
                {
                    "template": "table_large",
                    "theme": _theme_for_path(table),
                    "fields": {
                        "TABLE_TITLE": title,
                        "TABLE_FOOTNOTE": "Tabella generata automaticamente dalla pipeline; verificare le conclusioni narrative prima della consegna finale.",
                    },
                    "table": {
                        "placeholder": "TABLE_MAIN",
                        "source": _rel(table),
                        "start_row": page * rows_per_slide,
                        "max_rows": rows_per_slide,
                        **table_options,
                    },
                }
            )
    return specs


def _finding_specs(auto: dict[str, Any], available_templates: set[str], excludes: list[str]) -> list[dict[str, Any]]:
    if not _has_template(available_templates, "findings"):
        return []
    snippets = _existing_files(resolve_path("outputs/texts/snippets"), "*.md", set(), excludes)
    if auto.get("include_slide_pack_text"):
        snippets.extend(_existing_files(resolve_path("outputs/slide_assets/pack"), "*.md", set(), excludes))
    specs = []
    seen = set()
    for snippet in snippets:
        rel = _rel(snippet)
        if rel in seen:
            continue
        seen.add(rel)
        text = snippet.read_text(encoding="utf-8")
        if len(_markdown_body(text)) > 520:
            continue
        findings = _findings_from_markdown(text)
        if not findings:
            continue
        fields = {"FINDINGS_TITLE": _title_from_path(snippet), "MINI_GRAPH": ""}
        for idx in range(4):
            fields[f"FINDING_{idx + 1}"] = findings[idx] if idx < len(findings) else ""
        specs.append({"template": "findings", "theme": _theme_for_text(snippet, text), "fields": fields})
    return specs


def _text_slide_specs(available_templates: set[str], excludes: list[str]) -> list[dict[str, Any]]:
    if not _has_template(available_templates, "graph_full") and not _has_template(available_templates, "text_only"):
        return []
    template_id = "text_only" if _has_template(available_templates, "text_only") else "graph_full"
    files = []
    files.extend(_existing_files(resolve_path("outputs/slide_assets/pack"), "*.md", set(), excludes))
    files.extend(_existing_files(resolve_path("outputs/texts/snippets"), "*.md", set(), excludes))
    specs = []
    seen = set()
    for path in files:
        rel = _rel(path)
        if rel in seen or path.name == "00_index.md":
            continue
        seen.add(rel)
        text = _markdown_body(path.read_text(encoding="utf-8"))
        if len(text) < 120:
            continue
        theme = _theme_for_text(path, text)
        if template_id == "text_only":
            specs.append({"template": "text_only", "theme": theme, "fields": {"TEXT_TITLE": _title_from_path(path), "TEXT_BODY": text}})
        else:
            specs.append(
                {
                    "template": "graph_full",
                    "theme": theme,
                    "fields": {"GRAPH_TITLE": _title_from_path(path)},
                    "text_box": {"placeholder": "GRAPH_MAIN", "text": text},
                }
            )
    return specs


def _source_specs(available_templates: set[str], generated_specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not _has_template(available_templates, "sources") and not _has_template(available_templates, "text_only"):
        return []
    assets = sorted(_assets_in_specs(generated_specs))
    if not assets:
        return []
    specs = []
    chunk_size = 18 if _has_template(available_templates, "text_only") else 12
    for idx, chunk in enumerate(_chunks(assets, chunk_size), start=1):
        if _has_template(available_templates, "text_only"):
            specs.append(
                {
                    "template": "text_only",
                    "theme": "neutral",
                    "fields": {
                        "TEXT_TITLE": f"Asset generati ({idx})",
                        "TEXT_BODY": "\n".join(f"- {item}" for item in chunk),
                    },
                }
            )
        else:
            specs.append(
                {
                    "template": "sources",
                    "theme": "neutral",
                    "fields": {
                        "SOURCES_TITLE": f"Asset generati ({idx})",
                        "SOURCES_LIST": "\n".join(chunk),
                    },
                }
            )
    return specs


def _section_slide(section: str, *, theme: str = "neutral") -> dict[str, Any]:
    return {"template": "section_divider", "theme": theme, "fields": {"SECTION_NAME": SECTION_TITLES.get(section, _humanize(section))}}


def _text_spec(
    title: str,
    texts: dict[str, str],
    key: str,
    available_templates: set[str],
    *,
    theme: str = "neutral",
) -> dict[str, Any] | None:
    body = texts.get(key, texts.get("missing_text", ""))
    if _has_template(available_templates, "text_only"):
        return {"template": "text_only", "theme": theme, "fields": {"TEXT_TITLE": title, "TEXT_BODY": body}}
    if _has_template(available_templates, "graph_full"):
        return {
            "template": "graph_full",
            "theme": theme,
            "fields": {"GRAPH_TITLE": title, "INSIGHT_TEXT": ""},
            "text_box": {"placeholder": "GRAPH_MAIN", "text": body},
        }
    return None


def _blank_spec(title: str, texts: dict[str, str], key: str, available_templates: set[str], *, theme: str = "neutral") -> dict[str, Any] | None:
    if texts.get("__skip_missing_content") == "true":
        return None
    return _text_spec(title, texts, key, available_templates, theme=theme)


def _graph_or_blank(
    title: str,
    image: str,
    texts: dict[str, str],
    fallback_key: str,
    available_templates: set[str],
    *,
    theme: str = "neutral",
) -> dict[str, Any] | None:
    image_path = resolve_path(image)
    if image_path.exists() and _has_template(available_templates, "graph_full"):
        return {
            "template": "graph_full",
            "theme": theme,
            "fields": {"GRAPH_TITLE": title, "INSIGHT_TEXT": texts.get(fallback_key, "")},
            "images": {"GRAPH_MAIN": _rel(image_path)},
        }
    return _blank_spec(title, texts, fallback_key, available_templates, theme=theme)


def _heuristics_set_spec(texts: dict[str, str], available_templates: set[str]) -> dict[str, Any] | None:
    image = _first_existing_path(
        [
            "assets/manual/heuristics_table.png",
            "assets/manual/tabella_euristiche.png",
            "assets/heuristics/heuristics_table.png",
        ]
    )
    if image and _has_template(available_templates, "graph_full"):
        return {
            "template": "graph_full",
            "theme": "neutral",
            "fields": {
                "GRAPH_TITLE": "Set di euristiche",
                "INSIGHT_TEXT": "Tabella di riferimento delle 10 euristiche di Nielsen usata per classificare i problemi osservati.",
            },
            "images": {"GRAPH_MAIN": _rel(image)},
        }
    return _text_spec("Set di euristiche", texts, "nielsen_heuristics", available_templates)


def _questionnaire_item_spec(
    title: str,
    image: str,
    texts: dict[str, str],
    fallback_key: str,
    available_templates: set[str],
    *,
    item_idx: int,
    statistical: bool = False,
) -> dict[str, Any] | None:
    insight = _questionnaire_item_insight(item_idx, statistical=statistical) or texts.get(fallback_key, "")
    image_path = resolve_path(image)
    if image_path.exists() and _has_template(available_templates, "graph_full"):
        return {
            "template": "graph_full",
            "theme": "neutral",
            "fields": {"GRAPH_TITLE": title, "INSIGHT_TEXT": insight},
            "images": {"GRAPH_MAIN": _rel(image_path)},
        }
    return _blank_spec(title, {**texts, fallback_key: insight}, fallback_key, available_templates)


def _questionnaire_item_pairs() -> list[list[int]]:
    rows = _read_dict_rows(resolve_path("outputs/tables/questionnaire_items_summary.csv"))
    ids = sorted({_safe_int(row.get("item_number")) for row in rows if _safe_int(row.get("item_number"))})
    if not ids:
        item_dir = resolve_path("outputs/figures/dark/questionnaire/items")
        ids = sorted(_safe_int(match.group(1)) for path in item_dir.glob("item_*_boxplot.png") if (match := re.search(r"item_(\d+)_boxplot", path.name)))
    return _chunks([item for item in ids if item], 2)


def _questionnaire_pair_spec(pair: list[int], texts: dict[str, str], available_templates: set[str]) -> dict[str, Any] | None:
    if not pair:
        return None
    title = f"Distribuzione risposte - Domande {pair[0]}-{pair[-1]}" if len(pair) > 1 else f"Distribuzione risposte - Domanda {pair[0]}"
    insight = " ".join(_questionnaire_item_insight(item_idx) for item_idx in pair).strip() or texts.get("questionnaire_item_placeholder", "")
    images = [resolve_path(f"outputs/figures/dark/questionnaire/items/item_{item_idx:02d}_boxplot.png") for item_idx in pair]
    existing = [image for image in images if image.exists()]
    if len(existing) >= 2 and _has_template(available_templates, "comparison"):
        return {
            "template": "comparison",
            "theme": "neutral",
            "fields": {"COMPARISON_TITLE": title, "SUMMARY_TEXT": insight},
            "images": {"LEFT_GRAPH": _rel(existing[0]), "RIGHT_GRAPH": _rel(existing[1])},
        }
    if len(existing) == 1:
        return {
            "template": "graph_full",
            "theme": "neutral",
            "fields": {"GRAPH_TITLE": title, "INSIGHT_TEXT": insight},
            "images": {"GRAPH_MAIN": _rel(existing[0])},
        }
    return _blank_spec(title, {**texts, "questionnaire_item_placeholder": insight}, "questionnaire_item_placeholder", available_templates)


def _questionnaire_item_insight(item_idx: int, *, statistical: bool = False) -> str:
    rows = _read_dict_rows(resolve_path("outputs/tables/questionnaire_items_summary.csv"))
    row = next((item for item in rows if _safe_int(item.get("item_number")) == item_idx), None)
    if not row:
        return ""
    item_label = str(row.get("item") or f"item {item_idx}")
    deliveroo = _float_or_none(row.get("Deliveroo_mean"))
    glovo = _float_or_none(row.get("Glovo_mean"))
    delta_abs = _float_or_none(row.get("mean_difference_abs"))
    p_value = _float_or_none(row.get("p_value"))
    if deliveroo is None or glovo is None:
        return f"Item {item_idx} ({item_label}): dati medi non disponibili nel riepilogo questionario."
    leader = "Deliveroo" if deliveroo > glovo else "Glovo" if glovo > deliveroo else "nessuna app"
    diff = abs(deliveroo - glovo)
    significance = "differenza statisticamente significativa" if p_value is not None and p_value < 0.05 else "differenza non significativa"
    if statistical:
        return (
            f"Item {item_idx} ({item_label}): Deliveroo media {deliveroo:.2f}, Glovo {glovo:.2f}; "
            f"scarto {diff:.2f}, p={p_value:.3f} ({significance})."
        )
    return (
        f"Item {item_idx} ({item_label}): {leader} risulta piu alto nella media "
        f"({deliveroo:.2f} vs {glovo:.2f}); scarto medio {delta_abs if delta_abs is not None else diff:.2f}."
    )


def _comparison_or_blank(
    title: str,
    left_image: str,
    right_image: str,
    texts: dict[str, str],
    fallback_key: str,
    available_templates: set[str],
) -> dict[str, Any] | None:
    left = resolve_path(left_image)
    right = resolve_path(right_image)
    if left.exists() and right.exists() and _has_template(available_templates, "comparison"):
        return {
            "template": "comparison",
            "theme": "neutral",
            "fields": {"COMPARISON_TITLE": title, "SUMMARY_TEXT": texts.get(fallback_key, "")},
            "images": {"LEFT_GRAPH": _rel(left), "RIGHT_GRAPH": _rel(right)},
        }
    if left.exists():
        return _graph_or_blank(title, left_image, texts, fallback_key, available_templates)
    if right.exists():
        return _graph_or_blank(title, right_image, texts, fallback_key, available_templates)
    return _blank_spec(title, texts, fallback_key, available_templates)


def _table_or_blank(
    title: str,
    table: str,
    texts: dict[str, str],
    fallback_key: str,
    available_templates: set[str],
    *,
    theme: str = "neutral",
) -> dict[str, Any] | None:
    table_path = resolve_path(table)
    if table_path.exists() and _has_template(available_templates, "table_large"):
        rows = _read_csv_rows(table_path)
        is_evaluator_table = table_path.name == "heuristics_evaluators_slide.csv"
        return {
            "template": "table_large",
            "theme": theme,
            "fields": {
                "TABLE_TITLE": title,
                "TABLE_FOOTNOTE": texts.get("table_footnote", "Tabella generata dalla pipeline di analisi."),
            },
            "table": {
                "placeholder": "TABLE_MAIN",
                "source": _rel(table_path),
                "max_rows": max(8, len(rows) - 1) if is_evaluator_table else _rows_per_slide_for_table(rows, 5 if "problems_slide" in table_path.name else 10),
                "paginate": "problems_slide" in table_path.name,
                "title_prefix": title,
                **_table_render_options(rows),
            },
        }
    return _blank_spec(title, texts, fallback_key, available_templates, theme=theme)


def _final_or_text(texts: dict[str, str], available_templates: set[str]) -> dict[str, Any] | None:
    return _text_spec("Conclusioni", texts, "conclusions", available_templates)


def _reference_texts(auto: dict[str, Any]) -> dict[str, str]:
    path = resolve_path(auto.get("reference_texts") or "slides/content/reference_static_texts.md")
    if not path.exists():
        return _fallback_reference_texts()
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^##\s+([A-Za-z0-9_.-]+)\s*$", raw_line)
        if heading:
            current = heading.group(1).strip()
            sections[current] = []
            continue
        if current:
            sections[current].append(raw_line)
    parsed = {key: _clean_static_text("\n".join(lines)) for key, lines in sections.items()}
    if auto.get("skip_missing_content"):
        parsed["__skip_missing_content"] = "true"
    return {**_fallback_reference_texts(), **parsed}


def _clean_static_text(text: str) -> str:
    cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
    return cleaned


def _fallback_reference_texts() -> dict[str, str]:
    return {
        "missing_text": "Spazio lasciato intenzionalmente vuoto per completamento manuale.",
        "appendix_placeholder": "",
        "manual_problem_list": "",
        "manual_evaluator_table": "",
        "table_footnote": "Output generato dalla pipeline di analisi.",
        "heuristic_final_summary": "La valutazione euristica evidenzia che le criticita piu rilevanti non riguardano soltanto la quantita di problemi individuati, ma la loro collocazione nei momenti decisionali del flusso d'ordine: scelta del prodotto, configurazione del carrello, checkout, pagamento e controllo dello stato dell'ordine.",
        "deliveroo_relevant_problems": "In Deliveroo le criticita piu rilevanti si concentrano sulla trasparenza informativa, sulla gestione del flusso d'ordine e sul sovraccarico promozionale, con effetti diretti su controllo percepito e recupero degli errori.",
        "glovo_relevant_problems": "In Glovo emergono criticita legate alla coerenza del checkout, alla visibilita delle informazioni e alla presenza di elementi commerciali o accessori che competono con il task principale.",
        "shared_criticalities": "Il confronto mostra pattern ricorrenti del dominio food delivery: conferma dell'ordine, trasparenza informativa, controllo del carrello, annullamento e feedback post-ordine.",
        "dark_patterns_intro": "Oltre ai problemi di usabilita in senso stretto, alcune criticita osservate possono essere lette come frizioni persuasive o dark pattern: scelte di interfaccia che orientano l'attenzione, riducono la trasparenza o rendono meno immediata un'azione utile per l'utente.\n\nNel food delivery questi pattern sono particolarmente sensibili perche compaiono in fasi economicamente rilevanti: scelta dei prodotti, esposizione a contenuti sponsorizzati, modifica del carrello, conferma dell'ordine e gestione del post-acquisto.",
        "dark_patterns_deliveroo": "In Deliveroo i pattern piu evidenti riguardano la gestione dell'attenzione e la riduzione della trasparenza nei momenti di acquisto. I contenuti promozionali competono con le informazioni funzionali, mentre carrello e conferma dell'ordine non sempre rendono esplicito stato e conseguenze dell'azione.",
        "dark_patterns_glovo": "In Glovo i pattern piu critici emergono dall'integrazione di elementi commerciali o accessori in flussi operativi gia complessi: upselling nel carrello, contenuti sponsorizzati poco distinguibili e funzioni social non strettamente necessarie.",
        "dark_patterns_impact": "Queste scelte non impediscono il completamento del task, ma possono ridurre controllo percepito, fiducia e capacita di recupero in caso di errore. L'impatto diventa piu serio quando la frizione compare vicino a checkout, pagamento o tracking dell'ordine.",
        "user_test_statistical_significance": "I tempi dei task sono stati confrontati tra Deliveroo e Glovo considerando gli stessi utenti sulle due applicazioni. Il risultato distingue differenze descrittive da differenze statisticamente piu robuste.",
        "effectiveness_efficiency_joint": "La sola efficienza temporale non basta per valutare l'usabilita del flusso. Nei task di food delivery e necessario leggere insieme tempo, successo, errori e osservazioni qualitative.\n\nUn'interazione veloce puo risultare problematica se porta l'utente a perdere il controllo del carrello, a non comprendere lo stato dell'ordine o a confermare un pagamento senza verifica esplicita.",
        "qualitative_observations": "Le note qualitative collegano i dati numerici alle frizioni osservate: indirizzo, carrello, checkout, contenuti commerciali e tracking diventano punti in cui l'utente puo perdere orientamento o fiducia.",
        "user_expertise_matrix": "La matrice mostra la distribuzione dei partecipanti rispetto alla familiarita con servizi di food delivery e all'esperienza digitale dichiarata. Poiche il questionario non contiene una variabile digitale separata, la matrice va letta come rappresentazione descrittiva utile a contestualizzare tempi, errori e task assistiti.",
        "questionnaire_statistical_comparison": "Il confronto tra item del questionario evidenzia dove la percezione soggettiva separa maggiormente le due applicazioni e aiuta a collegare opinioni, prestazioni e problemi euristici.",
        "questionnaire_synthesis": "Il questionario mostra la percezione soggettiva degli utenti dopo l'interazione. I risultati vanno letti come complemento dei test: tempi ed errori descrivono la prestazione osservabile, mentre le risposte soggettive indicano fiducia, chiarezza, soddisfazione e disponibilita a riutilizzare o consigliare il servizio.",
        "ueq_interpretation": "Le scale UEQ distinguono qualita pragmatica dell'interazione, legata a chiarezza, efficienza e controllo, e qualita edonica, legata a stimolazione, attrattiva e originalita. Il punto centrale e capire quali dimensioni confermano le criticita osservate nei test.",
        "ueq_confirmations_contradictions": "Il confronto tra UEQ e test utente permette di individuare convergenze e contraddizioni. Quando una dimensione soggettiva conferma una criticita osservata, il problema diventa piu robusto; quando i dati divergono, l'app puo essere percepita positivamente pur introducendo frizioni operative specifiche.",
        "nps_interpreted": "Il Net Promoter Score sintetizza la disponibilita degli utenti a consigliare l'applicazione. Un NPS piu alto indica maggiore raccomandabilita percepita, ma non elimina eventuali criticita operative nei task o problemi euristici ad alta severita.",
        "conclusions_overall": "L'analisi mostra che Deliveroo e Glovo presentano entrambe un livello funzionale adeguato per completare i principali task di food delivery, ma introducono frizioni diverse lungo il percorso d'ordine.\n\nDeliveroo appare maggiormente critica nella gestione della trasparenza informativa, del carrello e del sovraccarico promozionale. Glovo presenta invece criticita piu evidenti nella coerenza del checkout, nella visibilita di alcune funzioni e nella distinzione tra contenuti funzionali, commerciali e accessori.",
        "integrated_evidence": "Le tre fonti di evidenza convergono su alcune aree critiche comuni. La valutazione euristica individua problemi legati a controllo, prevenzione dell'errore e trasparenza; i test utente mostrano frizioni pratiche in indirizzo, carrello e checkout; il questionario misura la percezione soggettiva di chiarezza, efficienza e fiducia.",
        "priority_recommendations": "Gli interventi prioritari dovrebbero concentrarsi sulle fasi ad alto rischio del flusso d'ordine: configurazione, carrello, checkout, pagamento e tracking.\n\nPer Deliveroo: rendere il carrello sempre visibile e recuperabile, migliorare la trasparenza informativa su prodotti e allergeni, ridurre il sovraccarico promozionale e introdurre conferme piu chiare prima delle azioni economicamente rilevanti.\n\nPer Glovo: rendere il checkout piu prevedibile, distinguere chiaramente contenuti sponsorizzati e organici, migliorare la visibilita delle funzioni utili e rafforzare i feedback sullo stato dell'ordine.",
        "final_verdict_argument": "Nel complesso, nessuna delle due applicazioni risulta priva di criticita. Entrambe permettono di completare i task principali, ma mostrano problemi ricorrenti nei momenti in cui l'utente dovrebbe percepire massimo controllo.\n\nLa differenza principale riguarda il tipo di frizione: Deliveroo tende a generare sovraccarico informativo e ambiguita nel recupero del carrello, mentre Glovo tende a distribuire le criticita tra checkout, funzioni accessorie e trasparenza dei contenuti commerciali.",
    }


def _systems_from_metadata(metadata: dict[str, Any]) -> tuple[str, str]:
    title = str(metadata.get("project_title") or "Deliveroo vs Glovo")
    if "glovo" in title.lower() and "deliveroo" in title.lower():
        return ("Deliveroo", "Glovo")
    return (str(metadata.get("system_1") or "Deliveroo"), str(metadata.get("system_2") or "Glovo"))


def _appendix_titles(systems: tuple[str, str]) -> list[str]:
    return [title for title, _folder, _theme in _appendix_entries(systems, int(DEFAULT_AUTO_CONFIG["task_count"]))]


def _task_count(auto: dict[str, Any]) -> int:
    try:
        return max(1, int(auto.get("task_count") or DEFAULT_AUTO_CONFIG["task_count"]))
    except (TypeError, ValueError):
        return int(DEFAULT_AUTO_CONFIG["task_count"])


def _appendix_specs(
    auto: dict[str, Any],
    systems: tuple[str, str],
    texts: dict[str, str],
    available_templates: set[str],
    task_count: int,
) -> list[dict[str, Any]]:
    root = resolve_path(auto.get("appendix_assets_root") or DEFAULT_AUTO_CONFIG["appendix_assets_root"])
    include_empty = bool(auto.get("include_empty_appendices"))
    specs = [
        _appendix_asset_or_blank(title, root / folder, texts, available_templates, theme=theme, include_empty=include_empty)
        for title, folder, theme in _appendix_entries(systems, task_count)
    ]
    return [spec for spec in specs if spec is not None]


def _guided_appendix_specs(texts: dict[str, str], available_templates: set[str]) -> list[dict[str, Any]]:
    entries = [
        ("Appendice A1 - Screenshot delle applicazioni", "Inserire screenshot rappresentativi di Deliveroo e Glovo nelle schermate principali: Home, ricerca, pagina ristorante, carrello, checkout e tracking ordine.\n\nChecklist: Home Deliveroo; Home Glovo; Ricerca/filtri; Pagina ristorante; Carrello; Checkout; Tracking ordine."),
        ("Appendice A2 - Evidenze visive problemi Deliveroo", "Inserire screenshot dei problemi Deliveroo piu rilevanti: carrello poco visibile, allergeni/informazioni incomplete, conferma pagamento, banner promozionali, gestione indirizzo."),
        ("Appendice A3 - Evidenze visive problemi Glovo", "Inserire screenshot dei problemi Glovo piu rilevanti: checkout, link account oscurato, sponsorizzati non marcati, preferiti non consultabili, tracking/accettazione ordine."),
        ("Appendice A4 - Evidenze visive dark pattern", "Inserire screenshot dei pattern persuasivi discussi nella sezione dark pattern: promozioni invasive, upselling, sponsorizzati poco marcati, conferma debole prima del pagamento."),
        ("Appendice A5 - Materiali dei test utente", "Inserire o linkare le slide/task consegnate agli utenti prima del test. Checklist: introduzione al test; task 1; task 2; task 3; istruzioni comuni; eventuale modulo consenso/privacy."),
        ("Appendice A6 - Tabelle complete tempi utente", "Inserire le tabelle complete dei tempi raccolti per tutti gli utenti, separate per componente o consolidate in una tabella unica."),
        ("Appendice A7 - Note qualitative dei test", "Inserire le note complete raccolte durante i test, mantenendo anonimato degli utenti e raggruppando le osservazioni per app e task."),
        ("Appendice A8 - Export valutazione problemi esperti", "Inserire screenshot o link all'export Formbricks usato per calcolare severita, priorita e valutazioni dei problemi euristici."),
        ("Appendice A9 - Export questionario utenti", "Inserire screenshot o link all'export Formbricks del questionario utenti, da cui derivano item, UEQ e NPS."),
        ("Appendice A10 - Tabelle dei calcoli statistici", "Inserire tabelle complete con test statistici: t-test/Wilcoxon sui tempi, Fisher/McNemar sull'efficacia, confronti item questionario, correzioni per confronti multipli e intervalli di confidenza."),
        ("Appendice A11 - Tabelle problemi complete", "Inserire o linkare le tabelle complete dei problemi euristici per Deliveroo e Glovo, incluse descrizioni estese, euristiche violate, valutatori e severita."),
        ("Appendice A12 - Repository e materiali finali", "Inserire link o QR code alla repository del progetto e alla cartella contenente dati, script, grafici, presentazione finale e report PDF esportato."),
    ]
    specs = []
    for title, body in entries:
        specs.append(_text_spec(title, {**texts, "__appendix_guided_body": f"INSERIRE SCREENSHOT QUI\n\n{body}\n\nNota: questa slide serve come prova documentale a supporto della discussione orale."}, "__appendix_guided_body", available_templates))
    return [spec for spec in specs if spec is not None]


def _final_delivery_appendix_specs(texts: dict[str, str], available_templates: set[str]) -> list[dict[str, Any]]:
    entries = [
        ("Appendice A6 - Tabelle complete tempi utente", "data/processed/final_report/user_test_times_unified.csv"),
        ("Appendice A7 - Note qualitative dei test", "data/processed/final_report/user_test_qualitative_observations.csv"),
        ("Appendice A8 - Export valutazione problemi", "data/processed/heuristics/problem_severity_summary.csv"),
        ("Appendice A9 - Descrittive questionario utenti", "data/processed/final_report/questionnaire_item_descriptive_stats.csv"),
        ("Appendice A10 - Calcoli statistici task", "data/processed/final_report/task_efficiency_stats.csv"),
        ("Appendice A11 - Problemi Deliveroo completi", "outputs/tables/final_problems_deliveroo.csv"),
        ("Appendice A11 - Problemi Glovo completi", "outputs/tables/final_problems_glovo.csv"),
        ("Appendice A12 - Log generazione finale", "outputs/final/final_report_generation_log.md"),
    ]
    specs: list[dict[str, Any]] = []
    for title, source in entries:
        path = resolve_path(source)
        if not path.exists() or path.suffix.lower() != ".csv":
            continue
        spec = _table_or_blank(title, source, texts, "appendix_placeholder", available_templates)
        if spec is not None:
            specs.append(spec)
    return specs


def _appendix_entries(systems: tuple[str, str], task_count: int) -> list[tuple[str, str, str]]:
    evaluators = _heuristic_evaluator_ids()
    entries: list[tuple[str, str, str]] = []
    for evaluator in evaluators:
        for app in systems:
            theme = infer_theme_from_app(app)
            entries.append(
                (
                    f"Appendice - Valutazione euristica {evaluator} - {app}",
                    f"heuristic_evaluations/{evaluator.lower()}/{_slug(app)}",
                    theme,
                )
            )
    entries.extend(
        [
            ("Appendice - Modulo autorizzazione foto e video", "consent_forms", "neutral"),
            (f"Appendice - Valutazione dei problemi di usabilità {systems[0]}", f"problem_ratings/{_slug(systems[0])}", infer_theme_from_app(systems[0])),
            (f"Appendice - Valutazione dei problemi di usabilità {systems[1]}", f"problem_ratings/{_slug(systems[1])}", infer_theme_from_app(systems[1])),
            (f"{systems[0]} vs {systems[1]}", "task_deck/title", "neutral"),
            ("Appendice - Presentazione task user test - Introduzione", "task_deck/intro", "neutral"),
            ("Appendice - Presentazione task user test - Come funziona", "task_deck/how_it_works", "neutral"),
            ("Appendice - Presentazione task user test - Le task", "task_deck/task_list", "neutral"),
        ]
    )
    for app in systems:
        theme = infer_theme_from_app(app)
        app_slug = _slug(app)
        entries.append((app, f"task_deck/{app_slug}/section", theme))
        entries.append((f"Prima di iniziare - {app}", f"task_deck/{app_slug}/before_start", theme))
        for task_idx in range(1, task_count + 1):
            entries.append((f"{app} - Task {task_idx}", f"task_deck/{app_slug}/task_{task_idx}", theme))
    entries.extend(
        [
            ("Attività conclusa", "task_deck/conclusion", "neutral"),
            ("Questionario", "questionnaire/form", "neutral"),
            ("Appendice - Risposte questionario", "questionnaire/responses", "neutral"),
            ("Appendice - Risultati questionario di usabilità", "questionnaire/results", "neutral"),
            ("Grazie", "closing", "neutral"),
        ]
    )
    return entries


def _heuristic_evaluator_ids() -> list[str]:
    for path in [
        resolve_path("outputs/tables/heuristics_evaluators_slide.csv"),
        resolve_path("data/formbricks_raw/heuristics/severity_ratings_export.csv"),
    ]:
        rows = _read_dict_rows(path)
        if not rows:
            continue
        ids: list[str] = []
        for row in rows:
            value = row.get("Valutatore") or row.get("1. Qual è il tuo id esperto?") or row.get("expert_id") or row.get("evaluator_id")
            value = str(value or "").strip()
            if value and value not in ids:
                ids.append(value)
        if ids:
            return sorted(ids, key=_evaluator_sort_key)
    return ["EU1", "EU2", "EU3", "EU4", "ED1", "ED2", "ED3", "ED4"]


def _evaluator_sort_key(value: str) -> tuple[str, int, str]:
    match = re.match(r"^([A-Za-z]+)(\d+)$", value.strip())
    if not match:
        return (value, 0, value)
    prefix, number = match.groups()
    return (prefix.upper(), int(number), value)


def _appendix_asset_or_blank(
    title: str,
    folder: Path,
    texts: dict[str, str],
    available_templates: set[str],
    *,
    theme: str = "neutral",
    include_empty: bool = False,
) -> dict[str, Any] | None:
    folder.mkdir(parents=True, exist_ok=True)
    image = _first_appendix_image(folder)
    if image and _has_template(available_templates, "graph_full"):
        return {
            "template": "graph_full",
            "theme": theme,
            "fields": {"GRAPH_TITLE": title, "INSIGHT_TEXT": texts.get("appendix_placeholder", "")},
            "images": {"GRAPH_MAIN": _rel(image)},
        }
    if not include_empty:
        return None
    body = texts.get("appendix_placeholder", "") or f"Placeholder appendice. Inserire asset in `{_rel(folder)}`."
    return _text_spec(title, {**texts, "__appendix_body": body}, "__appendix_body", available_templates, theme=theme)


def _first_appendix_image(folder: Path) -> Path | None:
    if not folder.exists():
        return None
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.suffix.lower() in APPENDIX_IMAGE_EXTENSIONS:
            return path
    return None


def _rows_per_slide_for_table(rows: list[list[str]], preferred: int) -> int:
    columns = len(rows[0]) if rows else 0
    if columns >= 9:
        return min(preferred, 4)
    if columns >= 7:
        return min(preferred, 5)
    if columns >= 5:
        return min(preferred, 7)
    return preferred


def _table_render_options(rows: list[list[str]]) -> dict[str, Any]:
    columns = len(rows[0]) if rows else 0
    if columns >= 9:
        return {"font_size": 6.2, "header_font_size": 6.5, "max_cell_chars": 36}
    if columns >= 7:
        return {"font_size": 6.6, "header_font_size": 6.9, "max_cell_chars": 44}
    if columns >= 5:
        return {"font_size": 7.2, "header_font_size": 7.5, "max_cell_chars": 58}
    return {"font_size": 7.8, "header_font_size": 8.1, "max_cell_chars": 74}


def _dedupe_missing_assets(specs: list[dict[str, Any]], used_assets: set[str], excludes: list[str]) -> list[dict[str, Any]]:
    filtered = []
    for spec in specs:
        assets = _assets_in_specs([spec])
        lower_assets = {asset.lower() for asset in assets}
        if any(any(exclude in asset for asset in lower_assets) for exclude in excludes):
            continue
        filtered.append(spec)
    return filtered


def _task_result_slides(effectiveness_figure: Path) -> list[dict[str, Any]]:
    task = effectiveness_figure.stem.split("_", 1)[0].upper()
    rows = _read_dict_rows(resolve_path(f"outputs/tables/user_tests_{task.lower()}_summary.csv"))
    text_path = resolve_path(f"outputs/texts/snippets/user_tests_{task.lower()}.md")
    description = _one_line_markdown(text_path.read_text(encoding="utf-8")) if text_path.exists() else "Risultati sintetici del task generati dalla pipeline."
    slides = []
    for row in rows:
        app = _app_from_row(row)
        theme = infer_theme_from_app(app)
        if theme == "neutral":
            continue
        slides.append(
            {
                "template": "task_results",
                "theme": theme,
                "fields": {
                    "TASK_TITLE": f"{task} - {app}",
                    "TASK_DESCRIPTION": description,
                    "SUCCESS_RATE": _format_value(row.get("success_rate"), percent=True),
                    "AVG_TIME": _format_value(row.get("mean_time_sec"), suffix="s"),
                },
                "images": {"TASK_SCREENSHOT": _rel(effectiveness_figure)},
            }
        )
    if slides:
        return slides
    return [
        {
            "template": "task_results",
            "theme": "neutral",
            "fields": {
                "TASK_TITLE": f"{task} - risultati del task",
                "TASK_DESCRIPTION": description,
                "SUCCESS_RATE": _format_average(rows, "success_rate", percent=True),
                "AVG_TIME": _format_average(rows, "mean_time_sec", suffix="s"),
            },
            "images": {"TASK_SCREENSHOT": _rel(effectiveness_figure)},
        }
    ]


def _ueq_question_slides(figure: Path, row: dict[str, str] | None) -> list[dict[str, Any]]:
    question = row.get("item") if row else _title_from_path(figure)
    slides = []
    if row:
        for key, value in row.items():
            if not key.endswith("_mean") or not value:
                continue
            app = key[:-5]
            theme = infer_theme_from_app(app)
            if theme == "neutral":
                continue
            median = row.get(f"{app}_median") or row.get(f"{app}_mediana")
            slides.append(
                {
                    "template": "ueq_question",
                    "theme": theme,
                    "fields": {
                        "QUESTION_TITLE": f"{question} - {app}",
                        "MEAN_VALUE": _format_value(value),
                        "STD_VALUE": _number_field(row, "mean_difference_abs", prefix="Delta "),
                        "MIN_VALUE": _number_field(row, "p_value", prefix="p="),
                        "MAX_VALUE": _format_value(median, prefix="Mediana "),
                    },
                    "images": {"BOXPLOT": _rel(figure)},
                }
            )
    if slides:
        return slides
    mean_values = []
    if row:
        for key, value in row.items():
            if key.endswith("_mean") and value:
                mean_values.append(f"{key[:-5]} {_format_value(value)}")
    return [
        {
            "template": "ueq_question",
            "theme": "neutral",
            "fields": {
                "QUESTION_TITLE": str(question),
                "MEAN_VALUE": " / ".join(mean_values) if mean_values else "n.d.",
                "STD_VALUE": _number_field(row, "mean_difference_abs", prefix="Delta "),
                "MIN_VALUE": _number_field(row, "p_value", prefix="p="),
                "MAX_VALUE": _number_field(row, "median_difference_abs", prefix="Mediana delta "),
            },
            "images": {"BOXPLOT": _rel(figure)},
        }
    ]


def _existing_files(root: Path, pattern: str, used_assets: set[str], excludes: list[str]) -> list[Path]:
    if not root.exists():
        return []
    files = []
    for path in sorted(root.rglob(pattern)):
        rel = _rel(path)
        rel_lower = rel.lower()
        if rel in used_assets:
            continue
        if any(exclude in rel_lower for exclude in excludes):
            continue
        files.append(path)
    return files


def _has_template(available_templates: set[str], base_template: str) -> bool:
    for theme in ["neutral", "deliveroo", "glovo"]:
        try:
            if resolve_template_id(base_template, theme) in available_templates:
                return True
        except ValueError:
            pass
    return base_template in available_templates


def _theme_for_path(path: Path) -> str:
    return infer_theme_from_app(_rel(path))


def _theme_for_text(path: Path, text: str) -> str:
    path_theme = _theme_for_path(path)
    if path_theme != "neutral":
        return path_theme
    lowered = text.lower()
    deliveroo_count = lowered.count("deliveroo")
    glovo_count = lowered.count("glovo")
    if deliveroo_count and not glovo_count:
        return "deliveroo"
    if glovo_count and not deliveroo_count:
        return "glovo"
    if deliveroo_count >= glovo_count + 2:
        return "deliveroo"
    if glovo_count >= deliveroo_count + 2:
        return "glovo"
    return "neutral"


def _ordered_sections(paths: list[Path]) -> list[str]:
    order = ["sample", "heuristics", "user_tests", "users_time", "questionnaire", "conclusions", "tables", "sources"]
    sections = {_section_for_path(path) for path in paths}
    return [section for section in order if section in sections] + sorted(sections - set(order))


def _section_for_path(path: Path) -> str:
    rel = _rel(path)
    if "/sample/" in rel:
        return "sample"
    if "/heuristics/" in rel:
        return "heuristics"
    if "/user_tests/" in rel:
        return "user_tests"
    if "users_time_" in rel:
        return "users_time"
    if "/questionnaire/" in rel:
        return "questionnaire"
    if "conclusion" in rel or "recommendation" in rel or "limitation" in rel:
        return "conclusions"
    return "general"


def _assets_in_specs(specs: list[dict[str, Any]]) -> set[str]:
    assets = set()
    for spec in specs:
        for path in (spec.get("images") or {}).values():
            assets.add(str(path).replace("\\", "/"))
        table = spec.get("table")
        if table and table.get("source"):
            assets.add(str(table["source"]).replace("\\", "/"))
    return assets


def _read_dict_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _read_csv_rows(path: Path) -> list[list[str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        sample = handle.read(2048)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;") if sample.strip() else csv.excel
        except csv.Error:
            dialect = csv.excel
        return [row for row in csv.reader(handle, dialect) if any(cell.strip() for cell in row)]


def _first_existing_path(paths: list[str]) -> Path | None:
    for path in paths:
        target = resolve_path(path)
        if target.exists():
            return target
    return None


def _app_from_row(row: dict[str, str]) -> str:
    for key in ("app", "application", "brand", "platform", "servizio"):
        value = row.get(key)
        if value and infer_theme_from_app(value) != "neutral":
            return value
    for value in row.values():
        if value and infer_theme_from_app(value) != "neutral":
            return value
    return ""


def _format_value(value: Any, *, percent: bool = False, prefix: str = "", suffix: str = "") -> str:
    if value in (None, ""):
        return "n.d."
    try:
        number = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return f"{prefix}{value}{suffix}"
    if percent:
        return f"{prefix}{number:.0%}{suffix}"
    formatted = f"{number:.2f}".rstrip("0").rstrip(".")
    return f"{prefix}{formatted}{suffix}"


def _format_average(rows: list[dict[str, str]], column: str, *, percent: bool = False, suffix: str = "") -> str:
    values = []
    for row in rows:
        try:
            values.append(float(row[column]))
        except (KeyError, TypeError, ValueError):
            pass
    if not values:
        return "n.d."
    value = sum(values) / len(values)
    if percent:
        return f"{value:.0%}"
    return f"{value:.1f}{suffix}"


def _number_field(row: dict[str, str] | None, key: str, prefix: str = "") -> str:
    if not row or not row.get(key):
        return "n.d."
    try:
        return f"{prefix}{float(row[key]):.2f}"
    except ValueError:
        return f"{prefix}{row[key]}"


def _safe_int(value: Any) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def _float_or_none(value: Any) -> float | None:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _findings_from_markdown(text: str) -> list[str]:
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    candidates = []
    for line in text.splitlines():
        line = re.sub(r"^\s*[-*]\s*", "", line).strip()
        line = re.sub(r"[*_`]+", "", line)
        if len(line) >= 24 and not line.lower().startswith(("asset consigliati", "testo suggerito")):
            candidates.append(_compact(line, 150))
    if candidates:
        return candidates[:4]
    paragraph = _compact(" ".join(text.split()), 150)
    return [paragraph] if paragraph else []


def _one_line_markdown(text: str) -> str:
    return _compact(_findings_from_markdown(text)[0] if _findings_from_markdown(text) else "Risultati generati dalla pipeline.", 220)


def _markdown_body(text: str) -> str:
    lines = []
    skip_section = False
    for line in text.splitlines():
        heading = re.match(r"^#{1,6}\s*(.+)\s*$", line)
        if heading:
            title = heading.group(1).strip().lower()
            skip_section = title in {"asset consigliati", "note da completare manualmente"}
            if title == "testo suggerito":
                skip_section = False
            continue
        if skip_section:
            continue
        lines.append(line)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"[*_`]+", "", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _insight_for_figure(path: Path) -> str:
    title = _title_from_path(path).lower()
    if "effectiveness" in path.name or "success" in path.name:
        return "Il grafico confronta il completamento dei task e mette in evidenza dove emergono frizioni operative tra le due app."
    if "efficiency" in path.name or "time" in path.name:
        return "Il grafico mostra le differenze nei tempi di completamento, utili per leggere l'efficienza percepita nei flussi principali."
    if "nps" in title:
        return "Il confronto NPS sintetizza la propensione degli utenti a consigliare le due applicazioni dopo il test."
    if "ueq" in title or "questionnaire" in _rel(path):
        return "I risultati UEQ aiutano a collegare prestazioni osservate e percezione soggettiva dell'esperienza d'uso."
    if "heuristic" in _rel(path):
        return "La visualizzazione supporta la lettura qualitativa delle criticita euristiche e della loro priorita di intervento."
    return "La figura sintetizza un'evidenza emersa dall'analisi e va letta insieme agli altri risultati del report."


def _title_from_path(path: Path) -> str:
    name = path.stem
    name = re.sub(r"^item_(\d+)_boxplot$", r"Item \1 - distribuzione risposte", name)
    name = re.sub(r"^t(\d+)_(.+)$", lambda m: f"Task {m.group(1)} - {_humanize(m.group(2))}", name)
    return _humanize(name)


def _humanize(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("_", " ").replace("-", " ")).strip().capitalize()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")
    return slug or "asset"


def _compact(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[: limit - 1].rstrip()


def _chunks(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(resolve_path(".").resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
