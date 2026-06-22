from __future__ import annotations


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
