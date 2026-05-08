from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import resolve_path


REQUIRED_COLUMNS = [
    "app",
    "pattern_name",
    "category",
    "description",
    "business_goal",
    "user_impact",
    "violated_heuristics",
    "evidence_path",
]


def ensure_dark_patterns_template(path: str | Path = "data/raw/dark_patterns.csv") -> Path:
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(target, index=False)
    return target


def analyze_dark_patterns(config: dict, input_path: str | Path = "data/raw/dark_patterns.csv") -> pd.DataFrame:
    path = ensure_dark_patterns_template(input_path)
    df = pd.read_csv(path)
    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    df = df[REQUIRED_COLUMNS].dropna(how="all")

    md_path = resolve_path("outputs/tables_md/dark_patterns.md")
    text_path = resolve_path("outputs/text_snippets/dark_patterns_summary.md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(df.to_markdown(index=False) if not df.empty else "Nessun dark pattern compilato manualmente.\n", encoding="utf-8")

    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    lines = ["# Dark pattern", ""]
    if df.empty:
        lines.append("Il file manuale `data/raw/dark_patterns.csv` non contiene ancora evidenze. La pipeline non identifica dark pattern automaticamente.")
    else:
        counts = df.groupby("app").size()
        lines.append(
            f"Sono stati documentati manualmente {len(df)} possibili dark pattern: "
            f"{systems[0]}={int(counts.get(systems[0], 0))}, {systems[1]}={int(counts.get(systems[1], 0))}."
        )
        lines.append("Questa sezione va trattata come evidenza qualitativa, da collegare a screenshot e note del gruppo.")
    text_path.write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    return df
