from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import resolve_path
from ..text_generation.display_labels import prepare_display_table


def read_display_table(csv_path: str | Path) -> list[list[str]]:
    target = resolve_path(csv_path)
    with target.open(newline="", encoding="utf-8-sig") as handle:
        sample = handle.read(2048)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;") if sample.strip() else csv.excel
        except csv.Error:
            dialect = csv.excel
        rows = [row for row in csv.reader(handle, dialect) if any(cell.strip() for cell in row)]
    if not rows:
        return []
    df = pd.DataFrame(rows[1:], columns=rows[0])
    return [prepare_display_table(df).columns.tolist(), *prepare_display_table(df).values.tolist()]


def paginate_rows(rows: list[list[str]], max_rows: int) -> list[list[list[str]]]:
    if not rows:
        return []
    if max_rows <= 0:
        return [rows]
    header, data = rows[0], rows[1:]
    return [[header, *data[start : start + max_rows]] for start in range(0, len(data), max_rows)] or [[header]]


def table_specs_from_paginated_table(spec: dict[str, Any]) -> list[dict[str, Any]]:
    table = spec.get("table") or {}
    if not table.get("paginate"):
        return [spec]
    rows = read_display_table(table["source"])
    pages = paginate_rows(rows, int(table.get("max_rows") or 6))
    if len(pages) <= 1:
        return [spec]
    specs = []
    for index, _page in enumerate(pages):
        clone = {**spec, "fields": dict(spec.get("fields") or {}), "table": dict(table)}
        clone["table"]["start_row"] = index * int(table.get("max_rows") or 6)
        clone["fields"]["TABLE_TITLE"] = f"{table.get('title_prefix') or clone['fields'].get('TABLE_TITLE', 'Tabella')} ({index + 1}/{len(pages)})"
        specs.append(clone)
    return specs
