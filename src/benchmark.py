from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .config import resolve_path
from .plots import save_figure
from .visualization.theme import get_brand_palette, style_axis


def analyze_ueq_benchmark(config: dict, input_path: str | Path = "data/raw/ueq_benchmark.csv") -> pd.DataFrame:
    path = resolve_path(input_path)
    text_path = resolve_path("outputs/texts/snippets/ueq_benchmark_conclusions.md")
    text_path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        text_path.write_text(
            "# Benchmark UEQ\n\nBenchmark non presente: la sezione e stata saltata senza bloccare la pipeline.\n",
            encoding="utf-8",
        )
        print(f"WARNING: benchmark UEQ non trovato: {path}")
        return pd.DataFrame()

    benchmark = pd.read_csv(path)
    ueq_path = resolve_path("outputs/tables/ueq_summary.csv")
    if not ueq_path.exists():
        text_path.write_text("# Benchmark UEQ\n\nEseguire prima l'analisi questionario per generare `outputs/tables/ueq_summary.csv`.\n", encoding="utf-8")
        return pd.DataFrame()
    ueq = pd.read_csv(ueq_path)
    merged = ueq.merge(benchmark, on="scale", how="left", suffixes=("_project", "_benchmark"))
    out_dir = resolve_path("outputs/tables")
    out_dir.mkdir(parents=True, exist_ok=True)
    for system in config["project"]["system_1"], config["project"]["system_2"]:
        merged[merged["system"] == system].to_csv(out_dir / f"ueq_benchmark_{system.lower()}.csv", index=False)

    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    sns.barplot(data=merged, x="scale", y="mean_project", hue="system", palette=get_brand_palette(config), ax=ax)
    if "mean_benchmark" in merged:
        for scale, value in merged[["scale", "mean_benchmark"]].drop_duplicates().dropna().itertuples(index=False):
            xpos = list(merged["scale"].drop_duplicates()).index(scale)
            ax.hlines(value, xpos - 0.4, xpos + 0.4, colors="#111827", linestyles="dashed", linewidth=1)
    ax.tick_params(axis="x", rotation=25)
    style_axis(ax, "Confronto UEQ con benchmark", "Scala", "Media")
    save_figure(fig, "outputs/figures/questionnaire/ueq_benchmark_comparison.png", config)

    best = merged.sort_values("mean_project", ascending=False).head(1)
    note = "Benchmark importato e confrontato con le scale UEQ del progetto."
    if not best.empty:
        note += f" Scala con media più alta: {best.iloc[0]['scale']} ({best.iloc[0]['system']})."
    text_path.write_text("# Benchmark UEQ\n\n" + note + "\n", encoding="utf-8")
    return merged

