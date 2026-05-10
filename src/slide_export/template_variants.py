from __future__ import annotations

from typing import Any


THEMES = {"neutral", "deliveroo", "glovo"}
VARIANT_TEMPLATES = {
    "section_divider",
    "graph_full",
    "table_large",
    "findings",
    "task_results",
    "ueq_question",
    "text_only",
}
FIXED_TEMPLATES = {"cover", "comparison", "final_verdict", "sources"}

REQUIRED_TEMPLATE_IDS = [
    "cover",
    "section_divider_neutral",
    "section_divider_deliveroo",
    "section_divider_glovo",
    "graph_full_neutral",
    "graph_full_deliveroo",
    "graph_full_glovo",
    "comparison_neutral",
    "table_large_neutral",
    "table_large_deliveroo",
    "table_large_glovo",
    "findings_neutral",
    "findings_deliveroo",
    "findings_glovo",
    "task_results_neutral",
    "task_results_deliveroo",
    "task_results_glovo",
    "ueq_question_neutral",
    "ueq_question_deliveroo",
    "ueq_question_glovo",
    "final_verdict",
    "sources",
    "text_only_neutral",
    "text_only_deliveroo",
    "text_only_glovo",
]

REQUIRED_SHAPES = {
    "cover": ["PROJECT_TITLE", "PROJECT_SUBTITLE", "AUTHORS_DATE"],
    "section_divider": ["SECTION_NAME"],
    "graph_full": ["GRAPH_TITLE", "GRAPH_MAIN", "INSIGHT_TEXT"],
    "comparison": ["COMPARISON_TITLE", "LEFT_GRAPH", "RIGHT_GRAPH", "SUMMARY_TEXT"],
    "table_large": ["TABLE_TITLE", "TABLE_MAIN", "TABLE_FOOTNOTE"],
    "findings": ["FINDINGS_TITLE", "FINDING_1", "FINDING_2", "FINDING_3", "FINDING_4", "MINI_GRAPH", "SUMMARY_TEXT"],
    "task_results": ["TASK_TITLE", "TASK_DESCRIPTION", "TASK_SCREENSHOT", "SUCCESS_RATE_VALUE", "AVG_TIME_VALUE"],
    "ueq_question": ["QUESTION_TITLE", "BOXPLOT", "MEAN_VALUE", "STD_VALUE", "MIN_VALUE", "MAX_VALUE"],
    "final_verdict": [
        "FINAL_TITLE",
        "DELIVEROO_STRENGTH_1",
        "DELIVEROO_STRENGTH_2",
        "DELIVEROO_WEAKNESS",
        "GLOVO_STRENGTH_1",
        "GLOVO_STRENGTH_2",
        "GLOVO_WEAKNESS",
        "SUMMARY_GRAPH",
        "WINNER_LABEL",
    ],
    "sources": ["SOURCES_TITLE", "SOURCES_LIST"],
    "text_only": ["TEXT_TITLE", "TEXT_BODY"],
}


def normalize_theme(theme: str | None) -> str:
    value = str(theme or "neutral").strip().lower()
    return value if value in THEMES else "neutral"


def infer_theme_from_app(value: Any) -> str:
    text = str(value or "").strip().lower()
    if "deliveroo" in text:
        return "deliveroo"
    if "glovo" in text:
        return "glovo"
    return "neutral"


def split_template_id(template_id: str) -> tuple[str, str]:
    for theme in THEMES:
        suffix = f"_{theme}"
        if template_id.endswith(suffix):
            return template_id[: -len(suffix)], theme
    if template_id == "comparison_neutral":
        return "comparison", "neutral"
    return template_id, "neutral"


def resolve_template_id(base_template: str, theme: str | None = "neutral") -> str:
    base = str(base_template or "").strip()
    if base in REQUIRED_TEMPLATE_IDS:
        base, theme = split_template_id(base)
    normalized_theme = normalize_theme(theme)
    if base in VARIANT_TEMPLATES:
        return f"{base}_{normalized_theme}"
    if base == "comparison":
        return "comparison_neutral"
    if base in FIXED_TEMPLATES:
        return base
    raise ValueError(f"Unknown slide template: {base_template}")


def base_template_for(template_id: str) -> str:
    base, _theme = split_template_id(template_id)
    return "comparison" if template_id == "comparison_neutral" else base
