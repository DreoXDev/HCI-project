from pathlib import Path

from src.slide_export import tables
from src.slide_export.tables import balanced_row_ranges, paginate_rows, table_specs_from_paginated_table


def test_paginate_table_rows_repeats_header_and_balances_pages() -> None:
    rows = [["ID", "Problema"], *[[str(index), f"P{index}"] for index in range(13)]]
    pages = paginate_rows(rows, max_rows=12)
    assert len(pages) == 2
    assert all(page[0] == ["ID", "Problema"] for page in pages)
    assert [len(page) for page in pages] == [8, 7]


def test_paginate_table_rows_caps_pages_at_twelve_items() -> None:
    rows = [["ID"], *[[str(index)] for index in range(24)]]
    pages = paginate_rows(rows, max_rows=20)
    assert len(pages) == 2
    assert [len(page) - 1 for page in pages] == [12, 12]


def test_balanced_row_ranges_keep_equal_parts() -> None:
    assert balanced_row_ranges(25, 12) == [(0, 9), (9, 8), (17, 8)]


def test_paginated_specs_expand_to_twelve_rows_even_when_source_spec_was_smaller(tmp_path: Path, monkeypatch) -> None:
    def resolve_in_tmp(path: str | Path, base_dir: Path = tmp_path) -> Path:
        value = Path(path)
        return value if value.is_absolute() else tmp_path / value

    monkeypatch.setattr(tables, "resolve_path", resolve_in_tmp)
    source = tmp_path / "table.csv"
    source.write_text("ID\n" + "\n".join(str(index) for index in range(24)) + "\n", encoding="utf-8")
    spec = {
        "fields": {"TABLE_TITLE": "Tabella"},
        "table": {"source": "table.csv", "paginate": True, "max_rows": 6},
    }

    pages = table_specs_from_paginated_table(spec)

    assert len(pages) == 2
    assert [page["table"]["start_row"] for page in pages] == [0, 12]
    assert [page["table"]["max_rows"] for page in pages] == [12, 12]
