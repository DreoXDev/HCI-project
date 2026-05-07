from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import load_config
from src.formbricks_adapter import convert_questionnaire_export, filter_finished, normalize_item_name
from src.questionnaire import numeric_items, available_subgroup_fields


def test_filter_finished_accepts_yes_values() -> None:
    df = pd.DataFrame({"Finished": ["Yes", "No", "true", "Sì"], "value": [1, 2, 3, 4]})

    result = filter_finished(df)

    assert result["value"].tolist() == [1, 3, 4]


def test_normalize_item_name_handles_numbers_accents_and_typos() -> None:
    assert normalize_item_name("6. Incomprensibile/Comprensibile") == "incomprensibile-comprensibile"
    assert normalize_item_name("19. Conorme alle Aspettative/Non Conorme alle Aspettative") == (
        "conforme alle aspettative-non conforme alle aspettative"
    )


def test_convert_questionnaire_export_transposes_and_splits_systems(tmp_path: Path) -> None:
    source = tmp_path / "questionnaire_export.csv"
    source.write_text(
        "\n".join(
            [
                "No.,Response ID,Finished,1. Genere,2. Eta,3. Professione,4. Familiarita con app di delivery di cibo.,"
                "5. Inserisci una valutazione per ogni campo riguardo all'app di Deliveroo. Fastidioso/Piacevole,"
                "6. Incomprensibile/Comprensibile,"
                "31. Inserisci una valutazione per ogni campo riguardo all'app di Glovo. Fastidioso/Piacevole,"
                "32. Incomprensibile/Comprensibile,Quanto consiglieresti Deliveroo?,Quanto consiglieresti Glovo?",
                "1,r1,Yes,Maschio,Meno di 25 anni,Studente,Alta,5,6,4,5,9,8",
                "2,r2,No,Femmina,25-45,Lavoratore,Bassa,1,1,1,1,0,0",
                "3,r3,Yes,Femmina,25-45,Studente,Media,6,7,5,6,10,9",
            ]
        ),
        encoding="utf-8",
    )
    config = load_config("config.yaml")
    config["formbricks"]["questionnaire"]["export_path"] = str(source)
    config["formbricks"]["questionnaire"]["output_system_1"] = str(tmp_path / "questionnaire_deliveroo.csv")
    config["formbricks"]["questionnaire"]["output_system_2"] = str(tmp_path / "questionnaire_glovo.csv")
    config["formbricks"]["questionnaire"]["ueq_items"] = [
        "fastidioso-piacevole",
        "incomprensibile-comprensibile",
    ]
    config["formbricks"]["questionnaire"]["nps_system_1"] = "Quanto consiglieresti Deliveroo?"
    config["formbricks"]["questionnaire"]["nps_system_2"] = "Quanto consiglieresti Glovo?"

    convert_questionnaire_export(None, config)

    deliveroo = pd.read_csv(tmp_path / "questionnaire_deliveroo.csv", index_col=0)
    glovo = pd.read_csv(tmp_path / "questionnaire_glovo.csv", index_col=0)
    assert list(deliveroo.columns) == ["Utente 1", "Utente 2"]
    assert deliveroo.loc["genere"].tolist() == ["Maschio", "Femmina"]
    assert pd.to_numeric(deliveroo.loc["fastidioso-piacevole"]).tolist() == [5, 6]
    assert pd.to_numeric(glovo.loc["fastidioso-piacevole"]).tolist() == [4, 5]
    assert pd.to_numeric(deliveroo.loc["NPS"]).tolist() == [9, 10]
    assert "familiarita delivery" not in numeric_items(deliveroo, config).index

    Path("outputs/import_report.md").unlink(missing_ok=True)
    Path("data/processed/questionnaire_formbricks_clean.csv").unlink(missing_ok=True)


def test_tagged_questionnaire_export_is_order_independent_and_dynamic(tmp_path: Path) -> None:
    source = tmp_path / "tagged_questionnaire_export.csv"
    source.write_text(
        "\n".join(
            [
                "Finished,[UEQ][Glovo] Incomprensibile/Comprensibile,[DEMOGRAPHIC] Preferred App,[DEMOGRAPHIC] Age,"
                "[NPS][Deliveroo],[UEQ][Deliveroo] Fastidioso/Piacevole,[DEMOGRAPHIC] Delivery Familiarity,"
                "[NPS][Glovo],[UEQ][Glovo] Fastidioso/Piacevole,[UEQ][Deliveroo] Incomprensibile/Comprensibile",
                "Yes,5,Deliveroo,22,9,6,Alta,8,4,7",
                "Yes,6,Glovo,23,10,5,Media,9,5,6",
            ]
        ),
        encoding="utf-8",
    )
    config = load_config("config.yaml")
    config["formbricks"]["questionnaire"]["export_path"] = str(source)
    config["formbricks"]["questionnaire"]["output_system_1"] = str(tmp_path / "questionnaire_deliveroo.csv")
    config["formbricks"]["questionnaire"]["output_system_2"] = str(tmp_path / "questionnaire_glovo.csv")
    config["formbricks"]["questionnaire"]["ueq_items"] = [
        "fastidioso-piacevole",
        "incomprensibile-comprensibile",
    ]

    convert_questionnaire_export(None, config)

    deliveroo = pd.read_csv(tmp_path / "questionnaire_deliveroo.csv", index_col=0)
    glovo = pd.read_csv(tmp_path / "questionnaire_glovo.csv", index_col=0)
    assert pd.to_numeric(deliveroo.loc["fastidioso-piacevole"]).tolist() == [6, 5]
    assert pd.to_numeric(deliveroo.loc["incomprensibile-comprensibile"]).tolist() == [7, 6]
    assert pd.to_numeric(glovo.loc["fastidioso-piacevole"]).tolist() == [4, 5]
    assert pd.to_numeric(glovo.loc["incomprensibile-comprensibile"]).tolist() == [5, 6]
    assert pd.to_numeric(deliveroo.loc["NPS"]).tolist() == [9, 10]
    assert pd.to_numeric(deliveroo.loc["eta"]).tolist() == [22, 23]
    assert "preferred_app" in available_subgroup_fields(deliveroo, config)
    assert "eta" in available_subgroup_fields(deliveroo, config)
    assert "preferred_app" not in numeric_items(deliveroo, config).index

    Path("outputs/import_report.md").unlink(missing_ok=True)
    Path("data/processed/questionnaire_formbricks_clean.csv").unlink(missing_ok=True)
