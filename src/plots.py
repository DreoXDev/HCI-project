from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns

from .config import resolve_path


def apply_project_theme(config: dict, theme: str = "dark") -> None:
    style = config["style"]
    if theme == "dark":
        plt.style.use("dark_background")
        bg = style["background"]
        text = style["text"]
        grid = "#333333"
    else:
        plt.style.use("default")
        bg = "#FFFFFF"
        text = "#111111"
        grid = "#DDDDDD"
    plt.rcParams.update(
        {
            "figure.facecolor": bg,
            "axes.facecolor": bg,
            "axes.edgecolor": grid,
            "axes.labelcolor": text,
            "xtick.color": text,
            "ytick.color": text,
            "text.color": text,
            "grid.color": grid,
            "font.size": 11,
        }
    )


def _palette(config: dict) -> list[str]:
    return [config["style"]["system_1_color"], config["style"]["system_2_color"]]


def save_figure(fig, path: str | Path, also_svg: bool = True) -> None:
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(target, dpi=180, bbox_inches="tight")
    if also_svg:
        fig.savefig(target.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def plot_effectiveness(effectiveness, config: dict, path: str | Path) -> None:
    apply_project_theme(config)
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=effectiveness, x="task", y="completion_rate", hue="system", palette=_palette(config), ax=ax)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Task")
    ax.set_ylabel("Tasso completamento")
    ax.set_title("Efficacia per task")
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, path)


def plot_effectiveness_ci(effectiveness, config: dict, path: str | Path) -> None:
    apply_project_theme(config)
    fig, ax = plt.subplots(figsize=(9, 5))
    systems = effectiveness["system"].unique()
    width = 0.35
    for offset, system in zip([-width / 2, width / 2], systems):
        subset = effectiveness[effectiveness["system"] == system]
        x = subset["task"] + offset
        y = subset["completion_rate"]
        yerr = [y - subset["ci_low"], subset["ci_high"] - y]
        ax.bar(x, y, width=width, label=system, color=_palette(config)[list(systems).index(system)])
        ax.errorbar(x, y, yerr=yerr, fmt="none", ecolor="white", capsize=4)
    ax.set_xticks([1, 2, 3])
    ax.set_ylim(0, 1)
    ax.set_xlabel("Task")
    ax.set_ylabel("Tasso completamento")
    ax.set_title("Efficacia con intervalli di confidenza")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, path)


def plot_efficiency_boxplot(efficiency_long, config: dict, path: str | Path) -> None:
    apply_project_theme(config)
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(data=efficiency_long, x="task", y="seconds", hue="system", palette=_palette(config), ax=ax)
    ax.set_xlabel("Task")
    ax.set_ylabel("Secondi")
    ax.set_title("Efficienza per task")
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, path)


def plot_efficiency_violin(efficiency_long, config: dict, path: str | Path) -> None:
    apply_project_theme(config)
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.violinplot(data=efficiency_long, x="task", y="seconds", hue="system", palette=_palette(config), split=False, ax=ax)
    ax.set_xlabel("Task")
    ax.set_ylabel("Secondi")
    ax.set_title("Distribuzione efficienza")
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, path)


def plot_distribution(df, x: str, config: dict, path: str | Path, title: str) -> None:
    apply_project_theme(config)
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df, x=x, y="count", hue="system", palette=_palette(config), ax=ax)
    ax.set_title(title)
    ax.set_ylabel("Occorrenze")
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, path)


def plot_ueq_summary(ueq, config: dict, path: str | Path) -> None:
    apply_project_theme(config)
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=ueq, x="scale", y="mean", hue="system", palette=_palette(config), ax=ax)
    ax.set_ylim(config["analysis"]["ueq_scale_min"], config["analysis"]["ueq_scale_max"])
    ax.set_xlabel("Scala UEQ")
    ax.set_ylabel("Media")
    ax.set_title("Sintesi scale UEQ")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, path)


def plot_nps(nps, config: dict, path: str | Path) -> None:
    apply_project_theme(config)
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.barplot(data=nps, x="system", y="nps", palette=_palette(config), hue="system", legend=False, ax=ax)
    ax.set_ylim(-100, 100)
    ax.set_xlabel("")
    ax.set_ylabel("NPS")
    ax.set_title("Confronto NPS")
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, path)
