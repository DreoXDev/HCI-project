from __future__ import annotations

import re
import unicodedata
from typing import Any


FINISHED_TRUE_VALUES = {"yes", "si", "sì", "true", "1", "completed", "complete"}


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text))
    return "".join(char for char in normalized if not unicodedata.combining(char))


def comparable(text: Any) -> str:
    value = strip_accents(str(text)).lower().replace("\n", " ")
    value = re.sub(r"^\d+\.\s*", "", value)
    value = re.sub(r"\[[^\]]+\]", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_item_name(column: str) -> str:
    text = strip_accents(str(column)).replace("\n", " ")
    text = re.sub(r"^\d+\.\s*", "", text)
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = text.lower().strip()
    text = text.replace("/", "-")
    text = re.sub(r"\s+", " ", text)
    text = text.replace("conorme", "conforme")
    text = text.replace("non conforme alle aspettative-non conforme alle aspettative", "conforme alle aspettative-non conforme alle aspettative")
    return text


def normalize_heuristic_codes(value: Any) -> list[str]:
    codes = re.findall(r"E(?:10|[1-9])", str(value).upper())
    return list(dict.fromkeys(codes))

