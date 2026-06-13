from __future__ import annotations

import re


COMMON_ITALIAN_FIXES = {
    "criticita": "criticità",
    "severita": "severità",
    "priorita": "priorità",
    "qualita": "qualità",
    "accessibilita": "accessibilità",
    "usabilita": "usabilità",
    "affidabilita": "affidabilità",
    "velocita": "velocità",
    "modalita": "modalità",
    "attivita": "attività",
    "quantita": "quantità",
    "ambiguita": "ambiguità",
    "liberta": "libertà",
    "citta": "città",
    "funzionalita": "funzionalità",
    "disponibilita": "disponibilità",
    "perspicuita": "perspicuità",
    "novita": "novità",
    "piu": "più",
    "perche": "perché",
    "puo": "può",
    "cosi": "così",
    "e'": "è",
}

POWERPOINT_SAFE_REPLACEMENTS = {
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "–": "-",
    "—": "-",
    "•": "-",
}


def fix_common_ascii_italian(text: str) -> str:
    """Apply only known, conservative Italian accent fixes."""
    result = str(text)
    for raw, fixed in COMMON_ITALIAN_FIXES.items():
        result = re.sub(rf"\b{re.escape(raw)}\b", fixed, result, flags=re.IGNORECASE)
    return result


def italian_display_text(value: object) -> str:
    """Return safe display text for final Italian outputs."""
    if value is None:
        return ""
    text = fix_common_ascii_italian(str(value))
    for source, target in POWERPOINT_SAFE_REPLACEMENTS.items():
        text = text.replace(source, target)
    return text
