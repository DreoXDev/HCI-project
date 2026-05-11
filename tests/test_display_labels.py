import pandas as pd

from src.text_generation.display_labels import display_column_name, prepare_display_table


def test_display_column_names() -> None:
    assert display_column_name("expert_id") == "Valutatore"
    assert display_column_name("severity_score") == "Severità media"


def test_prepare_display_table_removes_technical_headers() -> None:
    df = pd.DataFrame([{"expert_id": "E01", "severity_score": 3.5, "priority": "high"}])
    display = prepare_display_table(df)
    assert display.columns.tolist() == ["Valutatore", "Severità media", "Priorità"]
    assert display.loc[0, "Priorità"] == "Alta"

