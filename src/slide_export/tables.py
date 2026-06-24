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
    ranges = balanced_row_ranges(max(0, len(rows) - 1), max_rows)
    if not ranges:
        return [rows]
    header, data = rows[0], rows[1:]
    return [[header, *data[start : start + count]] for start, count in ranges] or [[header]]


def balanced_row_ranges(data_rows: int, max_rows: int) -> list[tuple[int, int]]:
    if data_rows <= 0:
        return [(0, 0)]
    if max_rows <= 0:
        return [(0, data_rows)]
    capped_max = min(12, max_rows)
    page_count = (data_rows + capped_max - 1) // capped_max
    base, remainder = divmod(data_rows, page_count)
    ranges = []
    start = 0
    for index in range(page_count):
        count = base + (1 if index < remainder else 0)
        ranges.append((start, count))
        start += count
    return ranges


def table_specs_from_paginated_table(spec: dict[str, Any]) -> list[dict[str, Any]]:
    table = spec.get("table") or {}
    if not table.get("paginate"):
        return [spec]
    rows = read_display_table(table["source"])
    requested_max = 12
    ranges = balanced_row_ranges(max(0, len(rows) - 1), requested_max)
    pages = paginate_rows(rows, requested_max)
    if len(pages) <= 1:
        return [spec]
    specs = []
    for index, (start_row, count) in enumerate(ranges):
        clone = {**spec, "fields": dict(spec.get("fields") or {}), "table": dict(table)}
        clone["table"]["start_row"] = start_row
        clone["table"]["max_rows"] = count
        base_title = table.get("title_prefix") or clone["fields"].get("TABLE_TITLE", "Tabella")
        separator = " — " if Path(str(table.get("source", ""))).name in {"user_testing_times_wide.csv", "user_profiles_slide.csv"} else " "
        suffix = f"{index + 1}/{len(pages)}" if separator.strip() == "—" else f"({index + 1}/{len(pages)})"
        clone["fields"]["TABLE_TITLE"] = f"{base_title}{separator}{suffix}"
        specs.append(clone)
    return specs
