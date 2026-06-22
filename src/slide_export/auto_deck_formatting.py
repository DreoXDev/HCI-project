from __future__ import annotations

import re
from typing import Any


def format_value(value: Any, *, percent: bool = False, prefix: str = "", suffix: str = "") -> str:
    if value in (None, ""):
        return "n.d."
    try:
        number = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return f"{prefix}{value}{suffix}"
    if percent:
        return f"{prefix}{number:.0%}{suffix}"
    formatted = f"{number:.2f}".rstrip("0").rstrip(".")
    return f"{prefix}{formatted}{suffix}"


def format_average(rows: list[dict[str, str]], column: str, *, percent: bool = False, suffix: str = "") -> str:
    values = []
    for row in rows:
        try:
            values.append(float(row[column]))
        except (KeyError, TypeError, ValueError):
            pass
    if not values:
        return "n.d."
    value = sum(values) / len(values)
    if percent:
        return f"{value:.0%}"
    return f"{value:.1f}{suffix}"


def number_field(row: dict[str, str] | None, key: str, prefix: str = "") -> str:
    if not row or not row.get(key):
        return "n.d."
    try:
        return f"{prefix}{float(row[key]):.2f}"
    except ValueError:
        return f"{prefix}{row[key]}"


def safe_int(value: Any) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def float_or_none(value: Any) -> float | None:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def findings_from_markdown(text: str) -> list[str]:
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    candidates = []
    for line in text.splitlines():
        line = re.sub(r"^\s*[-*]\s*", "", line).strip()
        line = re.sub(r"[*_`]+", "", line)
        if len(line) >= 24 and not line.lower().startswith(("asset consigliati", "testo suggerito")):
            candidates.append(compact(line, 150))
    if candidates:
        return candidates[:4]
    paragraph = compact(" ".join(text.split()), 150)
    return [paragraph] if paragraph else []


def one_line_markdown(text: str) -> str:
    findings = findings_from_markdown(text)
    return compact(findings[0] if findings else "Risultati generati dalla pipeline.", 220)


def markdown_body(text: str) -> str:
    lines = []
    skip_section = False
    for line in text.splitlines():
        heading = re.match(r"^#{1,6}\s*(.+)\s*$", line)
        if heading:
            title = heading.group(1).strip().lower()
            skip_section = title in {"asset consigliati", "note da completare manualmente"}
            if title == "testo suggerito":
                skip_section = False
            continue
        if skip_section:
            continue
        lines.append(line)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"[*_`]+", "", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def humanize(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("_", " ").replace("-", " ")).strip().capitalize()


def slug(value: str) -> str:
    slugged = re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")
    return slugged or "asset"


def compact(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[: limit - 1].rstrip()


def chunks(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]
