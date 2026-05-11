from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.formbricks_heuristics_pipeline import (
    evaluator_problem_matrix_raw,
    import_heuristics_raw_survey,
    normalize_heuristic_codes,
    normalize_raw_heuristic_problems,
    normalize_severity_ratings,
    priority_band,
    summarize_severity_ratings,
)


def _raw_formbricks_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "1. ID valutatore:": "EU1",
                "2. Genere": "Maschio",
                "3. Occupazione": "Studente",
                "4. Familiarita con app di food delivery": "3",
                "5. Esperienza di usabilità": "6",
                "6. Esperienza di dominio": "6",
                "7. Di quale app hai riscontrato il problema?": "Deliveroo",
                "8. Dai una descrizione breve (come fosse un titolo) del problema riscontrato:": "Feedback assente",
                "9. Dai una descrizione più dettagliata del problema:": "Il checkout non conferma l'azione.",
                "10. Seleziona le euristiche violate:": "E1 - Visibilita; E6 - Riconoscimento",
                "11. Di quale app hai riscontrato il problema?": "Glovo",
                "12. Dai una descrizione breve (come fosse un titolo) del problema riscontrato:": "Filtro ambiguo",
                "13. Dai una descrizione più dettagliata del problema:": "",
                "14. Seleziona le euristiche violate:": "",
            }
        ]
    )


def test_normalize_heuristic_codes_handles_multiple_separators() -> None:
    assert normalize_heuristic_codes("E1 - Visibilita; E6 - Riconoscimento, E10 - Aiuto") == ["E1", "E6", "E10"]


def test_raw_wide_to_long_keeps_partial_and_skips_empty_slots() -> None:
    mapping = {
        "problem_slots": {
            "count": 3,
            "fields": {
                "app": ["Di quale app"],
                "short_description": ["descrizione breve"],
                "long_description": ["dettagliata"],
                "heuristics": ["euristiche violate"],
            },
        }
    }
    profile_columns = {
        "evaluator_id": "1. ID valutatore:",
        "gender": "2. Genere",
        "occupation": "3. Occupazione",
        "familiarity": "4. Familiarita con app di food delivery",
        "usability_experience": "5. Esperienza di usabilità",
        "domain_experience": "6. Esperienza di dominio",
    }

    raw, warnings, ignored = normalize_raw_heuristic_problems(_raw_formbricks_df(), mapping, profile_columns, ["Deliveroo", "Glovo"])

    assert raw["raw_problem_id"].tolist() == ["RAW001", "RAW002"]
    assert ignored == 1
    assert raw.loc[0, "heuristics"] == "E1;E6"
    assert raw.loc[1, "completion_status"] == "missing_heuristics"
    assert warnings


def test_raw_pipeline_writes_expected_outputs(tmp_path: Path) -> None:
    source = tmp_path / "formbricks.csv"
    _raw_formbricks_df().to_csv(source, index=False)

    result = import_heuristics_raw_survey(
        source,
        output_dir=tmp_path / "processed",
        figures_dir=tmp_path / "figures",
        report_path=tmp_path / "report.md",
        template_path=tmp_path / "template.csv",
    )

    assert len(result.raw_problems_table) == 2
    assert (tmp_path / "processed" / "raw_problems_long.csv").exists()
    assert (tmp_path / "processed" / "heuristic_counts.csv").exists()
    assert (tmp_path / "figures" / "problem_counts_by_app.png").exists()
    assert (tmp_path / "report.md").exists()
    assert (tmp_path / "template.csv").exists()


def test_evaluator_problem_matrix_raw() -> None:
    raw_table = pd.DataFrame(
        [
            {"raw_problem_id": "RAW001", "evaluator_id": "EU1"},
            {"raw_problem_id": "RAW002", "evaluator_id": "EU1"},
            {"raw_problem_id": "RAW003", "evaluator_id": "EU2"},
        ]
    )
    matrix = evaluator_problem_matrix_raw(raw_table)
    assert matrix.loc["EU1", "RAW001"] == 1
    assert matrix.loc["EU1", "RAW003"] == 0


def test_severity_summary_and_priority_band() -> None:
    problems = pd.DataFrame(
        [
            {"final_problem_id": "D-PB01", "app": "Deliveroo", "short_description": "A", "long_description": "B", "heuristics": "E1"},
            {"final_problem_id": "G-PB01", "app": "Glovo", "short_description": "C", "long_description": "D", "heuristics": "E3"},
        ]
    )
    ratings = pd.DataFrame(
        [
            {"evaluator_id": "EU1", "final_problem_id": "D-PB01", "severity": "4"},
            {"evaluator_id": "EU2", "final_problem_id": "D-PB01", "severity": "3"},
            {"evaluator_id": "EU1", "final_problem_id": "G-PB01", "severity": "1"},
        ]
    )
    ratings_long, warnings = normalize_severity_ratings(ratings, problems)
    summary = summarize_severity_ratings(problems, ratings_long)

    assert warnings == []
    assert summary.loc[summary["final_problem_id"] == "D-PB01", "severity_mean"].iloc[0] == 3.5
    assert summary.loc[summary["final_problem_id"] == "D-PB01", "priority_band"].iloc[0] == "A"
    assert priority_band(1.5) == "C"
