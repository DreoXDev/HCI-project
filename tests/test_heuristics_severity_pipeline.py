from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.formbricks_heuristics_pipeline import (
    build_heuristic_category_counts,
    build_expert_problem_matrix,
    build_heuristic_final_dataset,
    build_heuristic_occurrence_counts,
    build_problem_severity_summary,
    build_problems_slide_table,
    build_profile_evaluators_slide_table,
    heuristic_category_mapping,
    normalize_formbricks_severity_export,
    normalize_problem_id_from_column,
    normalize_severity_strict,
    run_severity_pipeline,
    validate_clean_problems,
)


def _clean() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "problem_id": "PD01",
                "app": "Deliveroo",
                "screen": "Checkout",
                "heuristic": "H4",
                "title": "CTA checkout poco visibile",
                "description": "Il pulsante finale non risulta evidente.",
            },
            {
                "problem_id": "PG01",
                "app": "Glovo",
                "screen": "Home",
                "heuristic": "H8",
                "title": "Home troppo affollata",
                "description": "La schermata iniziale presenta troppi elementi.",
            },
        ]
    )


def _formbricks_export() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "No.": 1,
                "Response ID": "r1",
                "Timestamp": "2026-05-13",
                "Finished": True,
                "Survey ID": "s1",
                "1. Qual è il tuo id esperto": "E01",
                "2. [P001] CTA checkout poco visibile": "3 - Problema maggiore",
                "2. [P001] CTA checkout poco visibile - Option ID": "opt_3",
                "3. [P021] Home troppo affollata": "2",
                "3. [P021] Home troppo affollata - Option ID": "opt_2",
            },
            {
                "No.": 2,
                "Response ID": "r2",
                "Timestamp": "2026-05-13",
                "Finished": True,
                "Survey ID": "s1",
                "1. Qual è il tuo id esperto": "E02",
                "2. [P001] CTA checkout poco visibile": "4 - Problema critico",
                "2. [P001] CTA checkout poco visibile - Option ID": "opt_4",
                "3. [P021] Home troppo affollata": "",
                "3. [P021] Home troppo affollata - Option ID": "",
            },
        ]
    )


def test_validate_clean_problems_requires_columns_and_unique_ids() -> None:
    result = validate_clean_problems(_clean())
    assert result.valid

    invalid = _clean()
    invalid.loc[1, "problem_id"] = "PD01"
    result = validate_clean_problems(invalid)
    assert not result.valid
    assert any("duplicati" in error for error in result.errors)


def test_formbricks_wide_export_extracts_problem_ids_and_ignores_metadata() -> None:
    ratings, warnings = normalize_formbricks_severity_export(_formbricks_export(), problems=_clean())

    assert warnings == []
    assert ratings.to_dict("records") == [
        {"expert_id": "E01", "problem_id": "PD01", "severity": 3},
        {"expert_id": "E01", "problem_id": "PG01", "severity": 2},
        {"expert_id": "E02", "problem_id": "PD01", "severity": 4},
    ]
    assert "Option ID" not in set(ratings["problem_id"])


def test_problem_id_normalization_supports_app_qualified_columns() -> None:
    assert normalize_problem_id_from_column("PD01", "[PD01] Checkout - Deliveroo") == "PD01"
    assert normalize_problem_id_from_column("PG01", "[PG01] Checkout - Glovo") == "PG01"
    assert normalize_problem_id_from_column("P001", "[P001] Checkout - Deliveroo") == "PD01"
    assert normalize_problem_id_from_column("P001", "[P001] Checkout - Glovo") == "PG01"
    assert normalize_problem_id_from_column("P021", "[P021] Checkout - Glovo") == "PG01"


def test_severity_conversion_accepts_text_and_rejects_out_of_range() -> None:
    assert normalize_severity_strict("0 - Non è un problema") == 0
    assert normalize_severity_strict("4 - Problema critico") == 4
    assert normalize_severity_strict("5") is None
    assert normalize_severity_strict("non classificabile") is None


def test_unknown_and_missing_problem_warnings() -> None:
    export = _formbricks_export().rename(columns={"3. [P021] Home troppo affollata": "3. [P022] Problema non clean"})
    ratings, warnings = normalize_formbricks_severity_export(export, problems=_clean(), strict=False)

    assert "PG02" in " ".join(warnings)
    assert "PG01" in " ".join(warnings)
    assert "PG02" in set(ratings["problem_id"])

    with pytest.raises(ValueError):
        normalize_formbricks_severity_export(export, problems=_clean(), strict=True)


def test_join_final_dataset_and_matrix_are_correct() -> None:
    ratings, _ = normalize_formbricks_severity_export(_formbricks_export(), problems=_clean())
    final, warnings = build_heuristic_final_dataset(_clean(), ratings)
    summary = build_problem_severity_summary(_clean(), ratings)
    matrix = build_expert_problem_matrix(_clean(), ratings)

    assert warnings == []
    assert len(final) == 3
    assert summary.loc[summary["problem_id"] == "PD01", "mean_severity"].iloc[0] == 3.5
    assert matrix.loc[matrix["problem_id"] == "PD01", "E01"].iloc[0] == 3
    assert matrix.loc[matrix["problem_id"] == "PD01", "mean_severity"].iloc[0] == 3.5


def test_distribution_counts_split_multiple_heuristics_and_categories_sum() -> None:
    clean = _clean().copy()
    clean.loc[0, "heuristic"] = "E1;E3"
    ratings, _ = normalize_formbricks_severity_export(_formbricks_export(), problems=clean)
    summary = build_problem_severity_summary(clean, ratings)
    heuristic_counts = build_heuristic_occurrence_counts(summary)
    category_counts = build_heuristic_category_counts(heuristic_counts, heuristic_category_mapping())

    deliveroo = heuristic_counts[heuristic_counts["app"] == "Deliveroo"]
    assert deliveroo.loc[deliveroo["heuristic"] == "E1", "count"].iloc[0] == 1
    assert deliveroo.loc[deliveroo["heuristic"] == "E3", "count"].iloc[0] == 1
    assert category_counts[category_counts["app"] == "Deliveroo"]["count"].sum() == deliveroo["count"].sum()


def test_distribution_counts_ignore_source_count_weights() -> None:
    clean = _clean().copy()
    clean["source_count"] = [4, 0]
    clean.loc[0, "heuristic"] = "E1;E3"
    clean.loc[1, "heuristic"] = "E8"
    ratings, _ = normalize_formbricks_severity_export(_formbricks_export(), problems=clean)
    summary = build_problem_severity_summary(clean, ratings)
    heuristic_counts = build_heuristic_occurrence_counts(summary)
    category_counts = build_heuristic_category_counts(heuristic_counts, heuristic_category_mapping())

    deliveroo = heuristic_counts[heuristic_counts["app"] == "Deliveroo"]
    glovo = heuristic_counts[heuristic_counts["app"] == "Glovo"]
    assert deliveroo.loc[deliveroo["heuristic"] == "E1", "count"].iloc[0] == 1
    assert deliveroo.loc[deliveroo["heuristic"] == "E3", "count"].iloc[0] == 1
    assert glovo.loc[glovo["heuristic"] == "E8", "count"].iloc[0] == 1
    assert category_counts[category_counts["app"] == "Deliveroo"]["count"].sum() == 2


def test_heuristic_categories_follow_project_grouping() -> None:
    summary = pd.DataFrame(
        [
            {"app": "Glovo", "heuristic": "E1;E3"},
            {"app": "Glovo", "heuristic": "E4;E7"},
            {"app": "Glovo", "heuristic": "E8"},
            {"app": "Glovo", "heuristic": "E10"},
        ]
    )

    heuristic_counts = build_heuristic_occurrence_counts(summary)
    category_counts = build_heuristic_category_counts(heuristic_counts, heuristic_category_mapping())

    glovo = category_counts[category_counts["app"].eq("Glovo")].set_index("category")["count"].to_dict()
    assert glovo["Percezione"] == 2
    assert glovo["Cognizione"] == 2
    assert glovo["Errori"] == 2


def test_problem_slide_table_includes_median_and_std() -> None:
    ratings, _ = normalize_formbricks_severity_export(_formbricks_export(), problems=_clean())
    summary = build_problem_severity_summary(_clean(), ratings)
    slide = build_problems_slide_table(summary)

    assert {"Sev. media", "Sev. mediana", "Dev. st."} <= set(slide.columns)
    assert slide.loc[slide["ID"] == "PD01", "Dev. st."].iloc[0] > 0


def test_profile_evaluators_slide_table_keeps_all_final_experts(tmp_path: Path) -> None:
    profiles = tmp_path / "expert_profiles.csv"
    pd.DataFrame(
        [
            {"evaluator_id": "ED1", "expert_group": "ED", "gender": "Maschio", "age_group": "Meno di 25 Anni", "occupation": "Studente", "familiarity": 2, "usability_experience": 8, "domain_experience": 8},
            {"evaluator_id": "EU1", "expert_group": "EU", "gender": "Femmina", "age_group": "Meno di 25 Anni", "occupation": "Studente", "familiarity": 2, "usability_experience": 9, "domain_experience": 7},
        ]
    ).to_csv(profiles, index=False)

    slide = build_profile_evaluators_slide_table(profiles)

    assert list(slide["Valutatore"]) == ["ED1", "EU1"]
    assert {"Gruppo", "Genere", "Eta", "Esperienza usabilita", "Esperienza dominio"} <= set(slide.columns)


def test_severity_pipeline_writes_expected_outputs(tmp_path: Path) -> None:
    problems = tmp_path / "clean_problems.csv"
    ratings = tmp_path / "severity_ratings_export.csv"
    processed = tmp_path / "processed"
    out = tmp_path / "out"
    _clean().to_csv(problems, index=False)
    _formbricks_export().to_csv(ratings, index=False)

    result = run_severity_pipeline(problems_path=problems, ratings_export_path=ratings, processed_dir=processed, out_dir=out, strict=True)

    assert len(result.problem_summary) == 2
    assert (processed / "problem_ratings_long.csv").exists()
    assert (processed / "heuristic_final_dataset.csv").exists()
    assert (processed / "expert_problem_matrix.csv").exists()
    assert (out / "charts" / "top_problems.png").exists()
    assert (out / "tables" / "critical_problems.csv").exists()
    assert (out / "texts" / "summary.md").exists()
