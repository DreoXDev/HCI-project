from src.slide_export.tables import paginate_rows


def test_paginate_table_rows_repeats_header() -> None:
    rows = [["ID", "Problema"], *[[str(index), f"P{index}"] for index in range(13)]]
    pages = paginate_rows(rows, max_rows=6)
    assert len(pages) == 3
    assert all(page[0] == ["ID", "Problema"] for page in pages)
    assert [len(page) for page in pages] == [7, 7, 2]

