from __future__ import annotations

from src.final_assets import _questionnaire_item_slide_table


def test_questionnaire_item_slide_table_uses_horizontal_editable_format() -> None:
    left = {
        "app": "Deliveroo",
        "n": 24,
        "min": 1,
        "q1": 2,
        "mean": 3,
        "median": 4,
        "q3": 5,
        "max": 6,
        "variance": 1.25,
        "std": 1.12,
    }
    right = {**left, "app": "Glovo", "variance": 0.9, "std": 0.95}

    table = _questionnaire_item_slide_table(left, right, "Wilcoxon signed-rank", 24, 0.0123)

    assert list(table.columns) == ["App", "Min", "Q1", "Media", "Mediana", "Q3", "Max"]
    assert list(table["App"]) == ["Deliveroo", "Glovo"]
    assert table.loc[table["App"] == "Deliveroo", "Media"].iloc[0] == 3.0
    assert table.loc[table["App"] == "Glovo", "Max"].iloc[0] == 6.0
