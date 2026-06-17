from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import resolve_path
from .text_generation.display_labels import prepare_display_table


def export_table(df: pd.DataFrame, path: str | Path, decimals: int = 2) -> None:
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    suffix = target.suffix.lower()
    rounded = df.round(decimals).fillna("")
    if suffix == ".csv":
        rounded.to_csv(target, index=False, encoding="utf-8-sig")
    elif suffix == ".xlsx":
        rounded.to_excel(target, index=False)
    elif suffix == ".md":
        target.write_text(prepare_display_table(rounded).to_markdown(index=False), encoding="utf-8")
    else:
        raise ValueError(f"Formato tabella non supportato: {target}")
