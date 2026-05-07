from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.formbricks_heuristics_pipeline import (
    build_heuristics_from_review,
    calculate_priority,
    detect_columns,
    import_formbricks_heuristics,
    load_column_mapping,
    normalize_heuristic,
    normalize_severity,
    normalize_top5,
)


def test_detect_columns_from_configurable_aliases() -> None:
    df = pd.DataFrame(
        columns=[
            "ID valutatore",
            "App analizzata",
            "Task analizzata",
            "Descrizione breve",
            "Descrizione lunga",
            "Euristica violata",
            "Severita",
            "Problema tra i 5 piu gravi?",
        ]
    )

    detected = detect_columns(df, load_column_mapping())

    assert detected["evaluator_id"] == "ID valutatore"
    assert detected["short_description"] == "Descrizione breve"
    assert detected["top5"] == "Problema tra i 5 piu gravi?"


def test_normalizers_accept_formbricks_variants() -> None:
    assert normalize_heuristic("E1 - Visibility of system status") == ("E1", "Visibility of system status")
    assert normalize_heuristic("Aesthetic and minimalist design") == ("E8", "Aesthetic and minimalist design")
    assert normalize_severity("4 - Problema critico") == 4
    assert normalize_severity("5") is None
    assert normalize_top5("Si") is True
    assert normalize_top5("Top 5") is True
    assert normalize_top5("No") is False


def test_import_generates_candidates_review_and_errors(tmp_path: Path) -> None:
    source = tmp_path / "formbricks.csv"
    source.write_text(
        "\n".join(
            [
                "ID valutatore,App analizzata,Task analizzata,Descrizione breve,Descrizione lunga,Euristica violata,Severita,Problema tra i 5 piu gravi?",
                "EU1,Deliveroo,Checkout,Mancanza feedback,Manca feedback nel checkout,E1 - Visibility of system status,3,Si",
                "EU2,Glovo,Ricerca,Filtro ambiguo,Il filtro non e chiaro,Euristica inventata,5,boh",
            ]
        ),
        encoding="utf-8",
    )

    result = import_formbricks_heuristics(
        source,
        output_path=tmp_path / "heuristics_candidates.csv",
        review_path=tmp_path / "heuristics_review.csv",
        errors_path=tmp_path / "errors.csv",
        report_path=tmp_path / "report.md",
    )

    candidates = pd.read_csv(tmp_path / "heuristics_candidates.csv")
    review = pd.read_csv(tmp_path / "heuristics_review.csv")
    errors = pd.read_csv(tmp_path / "errors.csv")
    assert len(result.candidates) == 2
    assert candidates["candidate_id"].tolist() == ["C001", "C002"]
    assert review["problem_group_id"].tolist() == ["PG001", "PG002"]
    assert candidates.loc[0, "heuristic_id"] == "E1"
    assert candidates.loc[1, "include"] == False
    assert set(errors["field"]) == {"heuristic", "severity", "top5"}


def test_build_review_aggregates_groups_and_statistics(tmp_path: Path) -> None:
    review = pd.DataFrame(
        [
            {
                "candidate_id": "C001",
                "app": "Deliveroo",
                "task": "Checkout",
                "evaluator_id": "EU1",
                "short_description": "Mancanza feedback",
                "long_description": "Manca feedback nel checkout",
                "heuristic_id": "E1",
                "heuristic_label": "Visibility of system status",
                "severity": 3,
                "top5": True,
                "problem_group_id": "PG001",
                "include": True,
                "review_notes": "",
            },
            {
                "candidate_id": "C002",
                "app": "Deliveroo",
                "task": "Checkout",
                "evaluator_id": "EU2",
                "short_description": "Feedback pagamento poco visibile",
                "long_description": "Feedback pagamento insufficiente",
                "heuristic_id": "E8",
                "heuristic_label": "Aesthetic and minimalist design",
                "severity": 4,
                "top5": True,
                "problem_group_id": "PG001",
                "include": True,
                "review_notes": "",
            },
            {
                "candidate_id": "C003",
                "app": "Glovo",
                "task": "Ricerca",
                "evaluator_id": "EU1",
                "short_description": "Filtri poco chiari",
                "long_description": "Filtro non chiaro",
                "heuristic_id": "E4",
                "heuristic_label": "Consistency and standards",
                "severity": 2,
                "top5": False,
                "problem_group_id": "PG002",
                "include": True,
                "review_notes": "",
            },
        ]
    )
    review_path = tmp_path / "review.csv"
    review.to_csv(review_path, index=False)

    outputs = build_heuristics_from_review(review_path, output_dir=tmp_path, report_path=tmp_path / "build_report.md")

    deliveroo = outputs["Deliveroo"]
    assert (tmp_path / "heuristics_deliveroo.csv").exists()
    assert (tmp_path / "heuristics_glovo.csv").exists()
    assert deliveroo.loc[0, "ID"] == "PD1"
    assert deliveroo.loc[0, "Euristiche violate (ID)"] == "E1, E8"
    assert deliveroo.loc[0, "Popolarita"] == 2
    assert deliveroo.loc[0, "severity_mean"] == 3.5
    assert deliveroo.loc[0, "severity_median"] == 3.5
    assert deliveroo.loc[0, "severity_iqr"] == 0.5


def test_priority_uses_binomial_rule() -> None:
    assert calculate_priority(10, 0) == "A"
    assert calculate_priority(0, 10) == "C"
    assert calculate_priority(2, 1) == "B"
