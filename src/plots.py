from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns

from .visualization.theme import (
    annotate_bars,
    apply_base_theme,
    apply_light_effects,
    get_brand_palette,
    palette_list,
    save_figure_variants,
    style_axis,
)


def apply_project_theme(config: dict, theme: str = "clean") -> None:
    apply_base_theme(config, "presentation" if theme == "presentation" else "clean")


def _palette(config: dict) -> dict[str, str]:
    return get_brand_palette(config)


def save_figure(fig, path: str | Path, config: dict | None = None, also_svg: bool = True) -> None:
    save_figure_variants(fig, path, config=config, keep_legacy=True)


def plot_effectiveness(effectiveness, config: dict, path: str | Path) -> None:
    apply_project_theme(config)
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    sns.barplot(data=effectiveness, x="task", y="completion_rate", hue="system", palette=_palette(config), ax=ax)
    ax.set_ylim(0, 1)
    style_axis(ax, "Efficacia per task", "Task", "Tasso completamento")
    annotate_bars(ax, "{:.0%}", enabled=config.get("visualization", {}).get("presentation", {}).get("annotations", True))
    save_figure_variants(fig, path, config)


def plot_effectiveness_ci(effectiveness, config: dict, path: str | Path) -> None:
    apply_project_theme(config)
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    systems = effectiveness["system"].unique()
    colors = palette_list(config)
    width = 0.35
    for offset, system in zip([-width / 2, width / 2], systems):
        subset = effectiveness[effectiveness["system"] == system]
        x = subset["task"] + offset
        y = subset["completion_rate"]
        yerr = [y - subset["ci_low"], subset["ci_high"] - y]
        ax.bar(x, y, width=width, label=system, color=colors[list(systems).index(system)])
        ax.errorbar(x, y, yerr=yerr, fmt="none", ecolor="#1F2937", capsize=4, linewidth=1)
    ax.set_xticks([1, 2, 3])
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    style_axis(ax, "Efficacia con intervalli di confidenza", "Task", "Tasso completamento")
    save_figure_variants(fig, path, config)


def plot_efficiency_boxplot(efficiency_long, config: dict, path: str | Path) -> None:
    apply_project_theme(config)
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    sns.boxplot(data=efficiency_long, x="task", y="seconds", hue="system", palette=_palette(config), ax=ax)
    style_axis(ax, "Efficienza per task", "Task", "Secondi")
    save_figure_variants(fig, path, config)


def plot_efficiency_violin(efficiency_long, config: dict, path: str | Path) -> None:
    apply_project_theme(config)
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    sns.violinplot(data=efficiency_long, x="task", y="seconds", hue="system", palette=_palette(config), split=False, ax=ax)
    style_axis(ax, "Distribuzione efficienza", "Task", "Secondi")
    save_figure_variants(fig, path, config)


def plot_distribution(df, x: str, config: dict, path: str | Path, title: str) -> None:
    apply_project_theme(config)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.barplot(data=df, x=x, y="count", hue="system", palette=_palette(config), ax=ax)
    style_axis(ax, title, x.capitalize(), "Occorrenze")
    apply_light_effects(ax, config.get("visualization", {}).get("presentation", {}).get("glow", True))
    annotate_bars(ax, "{:.0f}", enabled=config.get("visualization", {}).get("presentation", {}).get("annotations", True))
    save_figure_variants(fig, path, config)


def plot_ueq_summary(ueq, config: dict, path: str | Path) -> None:
    apply_project_theme(config)
    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    sns.barplot(data=ueq, x="scale", y="mean", hue="system", palette=_palette(config), ax=ax)
    ax.set_ylim(config["analysis"]["ueq_scale_min"], config["analysis"]["ueq_scale_max"])
    ax.tick_params(axis="x", rotation=25)
    style_axis(ax, "Sintesi scale UEQ", "Scala UEQ", "Media")
    annotate_bars(ax, "{:.1f}", enabled=config.get("visualization", {}).get("presentation", {}).get("annotations", True))
    save_figure_variants(fig, path, config)


def plot_nps(nps, config: dict, path: str | Path) -> None:
    apply_project_theme(config)
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    sns.barplot(data=nps, x="system", y="nps", palette=_palette(config), hue="system", legend=False, ax=ax)
    ax.set_ylim(-100, 100)
    style_axis(ax, "Confronto NPS", "", "NPS")
    annotate_bars(ax, "{:.0f}", enabled=config.get("visualization", {}).get("presentation", {}).get("annotations", True))
    save_figure_variants(fig, path, config)
