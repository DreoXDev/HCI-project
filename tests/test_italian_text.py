from src.text_generation.italian import fix_common_ascii_italian


def test_common_italian_fixes() -> None:
    assert fix_common_ascii_italian("criticità severità priorità") == "criticità severità priorità"
    assert fix_common_ascii_italian("criticita severita priorita") == "criticità severità priorità"
