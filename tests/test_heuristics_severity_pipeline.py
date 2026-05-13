from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.formbricks_heuristics_pipeline import (
    build_expert_problem_matrix,
    build_heuristic_final_dataset,
    build_problem_severity_summary,
    normalize_formbricks_severity_export,
    normalize_severity_strict,
    run_severity_pipeline,
    validate_clean_problems,
)


def _clean() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "problem_id": "P001",
                "app": "Deliveroo",
                "screen": "Checkout",
                "heuristic": "H4",
                "title": "CTA checkout poco visibile",
                "description": "Il pulsante finale non risulta evidente.",
            },
            {
                "problem_id": "P002",
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
                "1. Qual è il tuo id esperto?": "E01",
                "2. [P001] CTA checkout poco visibile": "3 - Problema maggiore",
                "2. [P001] CTA checkout poco visibile - Option ID": "opt_3",
                "3. [P002] Home troppo affollata": "2",
                "3. [P002] Home troppo affollata - Option ID": "opt_2",
            },
            {
                "No.": 2,
                "Response ID": "r2",
                "Timestamp": "2026-05-13",
                "Finished": True,
                "Survey ID": "s1",
                "1. Qual è il tuo id esperto?": "E02",
                "2. [P001] CTA checkout poco visibile": "4 - Problema critico",
                "2. [P001] CTA checkout poco visibile - Option ID": "opt_4",
                "3. [P002] Home troppo affollata": "",
                "3. [P002] Home troppo affollata - Option ID": "",
            },
        ]
    )


def test_validate_clean_problems_requires_columns_and_unique_ids() -> None:
    result = validate_clean_problems(_clean())
    assert result.valid

    invalid = _clean()
    invalid.loc[1, "problem_id"] = "P001"
    result = validate_clean_problems(invalid)
    assert not result.valid
    assert any("duplicati" in error for error in result.errors)


def test_formbricks_wide_export_extracts_problem_ids_and_ignores_metadata() -> None:
    ratings, warnings = normalize_formbricks_severity_export(_formbricks_export(), problems=_clean())

    assert warnings == []
    assert ratings.to_dict("records") == [
        {"expert_id": "E01", "problem_id": "P001", "severity": 3},
        {"expert_id": "E01", "problem_id": "P002", "severity": 2},
        {"expert_id": "E02", "problem_id": "P001", "severity": 4},
    ]
    assert "Option ID" not in set(ratings["problem_id"])


def test_severity_conversion_accepts_text_and_rejects_out_of_range() -> None:
    assert normalize_severity_strict("0 - Non è un problema") == 0
    assert normalize_severity_strict("4 - Problema critico") == 4
    assert normalize_severity_strict("5") is None
    assert normalize_severity_strict("non classificabile") is None


def test_unknown_and_missing_problem_warnings() -> None:
    export = _formbricks_export().rename(columns={"3. [P002] Home troppo affollata": "3. [P003] Problema non clean"})
    ratings, warnings = normalize_formbricks_severity_export(export, problems=_clean(), strict=False)

    assert "P003" in " ".join(warnings)
    assert "P002" in " ".join(warnings)
    assert "P003" in set(ratings["problem_id"])

    with pytest.raises(ValueError):
        normalize_formbricks_severity_export(export, problems=_clean(), strict=True)


def test_join_final_dataset_and_matrix_are_correct() -> None:
    ratings, _ = normalize_formbricks_severity_export(_formbricks_export(), problems=_clean())
    final, warnings = build_heuristic_final_dataset(_clean(), ratings)
    summary = build_problem_severity_summary(_clean(), ratings)
    matrix = build_expert_problem_matrix(_clean(), ratings)

    assert warnings == []
    assert len(final) == 3
    assert summary.loc[summary["problem_id"] == "P001", "mean_severity"].iloc[0] == 3.5
    assert matrix.loc[matrix["problem_id"] == "P001", "E01"].iloc[0] == 3
    assert matrix.loc[matrix["problem_id"] == "P001", "mean_severity"].iloc[0] == 3.5


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
