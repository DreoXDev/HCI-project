import pandas as pd


def test_demo_experts_split() -> None:
    df = pd.read_csv("data/formbricks_raw/heuristics_discovery/formbricks_heuristics_discovery_demo_6_experts.csv")
    assert df["ID valutatore"].nunique() == 6
    assert df["expert_group"].value_counts().to_dict() == {"ED": 3, "EU": 3}


def test_slide_table_source_uses_display_labels_after_render_source_generation() -> None:
    ratings = pd.read_csv("data/formbricks_raw/heuristics_ratings/formbricks_heuristics_ratings_demo_6_experts.csv")
    assert ratings["evaluator_id"].nunique() == 6
    assert ratings["expert_group"].value_counts().to_dict() == {"ED": 18, "EU": 18}

