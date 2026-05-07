from __future__ import annotations

from pathlib import Path
from typing import Literal

import matplotlib

matplotlib.use("Agg")

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib import font_manager

from ..config import resolve_path


PlotStyle = Literal["clean", "presentation", "both"]

DELIVEROO_COLOR = "#00CCBC"
GLOVO_COLOR = "#FFC244"

BRAND_COLORS = {
    "Deliveroo": DELIVEROO_COLOR,
    "Glovo": GLOVO_COLOR,
    "neutral": "#1F2937",
    "muted": "#6B7280",
    "grid": "#E5E7EB",
    "background": "#FFFFFF",
}

PRESENTATION_STYLE = {
    "figure_dpi": 220,
    "transparent": True,
    "font_family": "Inter",
    "fallback_font": "DejaVu Sans",
    "title_size": 20,
    "label_size": 13,
    "tick_size": 11,
    "legend_size": 11,
}

CLEAN_STYLE = {
    "figure_dpi": 180,
    "transparent": False,
    "font_family": "Inter",
    "fallback_font": "DejaVu Sans",
    "title_size": 16,
    "label_size": 12,
    "tick_size": 10,
    "legend_size": 10,
}


def visualization_config(config: dict | None = None) -> dict:
    defaults = {
        "style": "both",
        "export_svg": True,
        "export_png": True,
        "dpi": 220,
        "transparent_background": True,
        "fonts": {"preferred": "Inter", "fallback": "DejaVu Sans"},
        "colors": {
            "deliveroo": DELIVEROO_COLOR,
            "glovo": GLOVO_COLOR,
            "neutral": BRAND_COLORS["neutral"],
            "muted": BRAND_COLORS["muted"],
            "grid": BRAND_COLORS["grid"],
        },
        "presentation": {"enabled": True, "glow": True, "annotations": True},
    }
    if not config:
        return defaults
    merged = defaults.copy()
    user = config.get("visualization", {})
    for key, value in user.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def get_brand_palette(config: dict | None = None) -> dict[str, str]:
    visual = visualization_config(config)
    colors = visual["colors"]
    project = (config or {}).get("project", {})
    return {
        project.get("system_1", "Deliveroo"): colors.get("deliveroo", DELIVEROO_COLOR),
        project.get("system_2", "Glovo"): colors.get("glovo", GLOVO_COLOR),
        "Deliveroo": colors.get("deliveroo", DELIVEROO_COLOR),
        "Glovo": colors.get("glovo", GLOVO_COLOR),
    }


def palette_list(config: dict | None = None) -> list[str]:
    palette = get_brand_palette(config)
    project = (config or {}).get("project", {})
    return [
        palette.get(project.get("system_1", "Deliveroo"), DELIVEROO_COLOR),
        palette.get(project.get("system_2", "Glovo"), GLOVO_COLOR),
    ]


def _style_values(style: str) -> dict:
    return PRESENTATION_STYLE if style == "presentation" else CLEAN_STYLE


def _available_font(preferred: str, fallback: str) -> str:
    available = {font.name for font in font_manager.fontManager.ttflist}
    return preferred if preferred in available else fallback


def apply_base_theme(config: dict | None = None, style: str = "clean") -> None:
    visual = visualization_config(config)
    values = _style_values(style)
    fonts = visual.get("fonts", {})
    preferred = fonts.get("preferred", values["font_family"])
    fallback = fonts.get("fallback", values["fallback_font"])
    font_family = _available_font(preferred, fallback)
    background = "none" if style == "presentation" else BRAND_COLORS["background"]
    plt.style.use("default")
    plt.rcParams.update(
        {
            "font.family": [font_family],
            "figure.facecolor": background,
            "axes.facecolor": background,
            "savefig.facecolor": background,
            "axes.edgecolor": visual["colors"]["grid"],
            "axes.labelcolor": visual["colors"]["neutral"],
            "axes.titlesize": values["title_size"],
            "axes.labelsize": values["label_size"],
            "xtick.color": visual["colors"]["muted"],
            "ytick.color": visual["colors"]["muted"],
            "xtick.labelsize": values["tick_size"],
            "ytick.labelsize": values["tick_size"],
            "text.color": visual["colors"]["neutral"],
            "legend.fontsize": values["legend_size"],
            "grid.color": visual["colors"]["grid"],
            "grid.alpha": 0.18 if style == "presentation" else 0.28,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def apply_presentation_theme(config: dict | None = None) -> None:
    apply_base_theme(config, "presentation")


def style_axis(ax, title: str | None = None, xlabel: str | None = None, ylabel: str | None = None, style: str = "clean") -> None:
    if title:
        ax.set_title(title, pad=14 if style == "presentation" else 10, fontweight="semibold")
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.18 if style == "presentation" else 0.28)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def apply_light_effects(ax, enabled: bool = True) -> None:
    if not enabled:
        return
    for patch in ax.patches:
        patch.set_path_effects(
            [
                pe.SimplePatchShadow(offset=(0, -1), alpha=0.12, rho=0.95),
                pe.Normal(),
            ]
        )


def annotate_bars(ax, fmt: str = "{:.0f}", enabled: bool = True) -> None:
    if not enabled:
        return
    for patch in ax.patches:
        height = patch.get_height()
        if height != height:
            continue
        x = patch.get_x() + patch.get_width() / 2
        y = height
        label = fmt.format(height)
        ax.annotate(label, (x, y), ha="center", va="bottom", xytext=(0, 4), textcoords="offset points", fontsize=9)


def selected_styles(config: dict | None = None, plot_style: str | None = None) -> list[str]:
    visual = visualization_config(config)
    style = plot_style or visual.get("style", "both")
    if style == "both":
        return ["clean", "presentation"]
    if style in {"clean", "presentation"}:
        return [style]
    return ["clean", "presentation"]


def variant_path(path: str | Path, style: str, output_root: str | Path = "outputs/figures") -> Path:
    source = resolve_path(path)
    figures_root = resolve_path(output_root)
    name = source.name
    if figures_root in source.parents:
        relative = source.relative_to(figures_root)
        name = "_".join(relative.parts)
    return figures_root / style / name


def save_figure(fig, path: str | Path, config: dict | None = None, style: str = "clean", close: bool = True) -> Path:
    visual = visualization_config(config)
    values = _style_values(style)
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    transparent = bool(visual.get("transparent_background", True)) if style == "presentation" else False
    dpi = int(visual.get("dpi", values["figure_dpi"])) if style == "presentation" else values["figure_dpi"]
    if visual.get("export_png", True):
        fig.savefig(target, dpi=dpi, bbox_inches="tight", transparent=transparent)
    if visual.get("export_svg", True):
        fig.savefig(target.with_suffix(".svg"), bbox_inches="tight", transparent=transparent)
    if close:
        plt.close(fig)
    return target


def save_figure_variants(
    fig,
    path: str | Path,
    config: dict | None = None,
    plot_style: str | None = None,
    keep_legacy: bool = True,
) -> list[Path]:
    paths: list[Path] = []
    for style in selected_styles(config, plot_style):
        target = variant_path(path, style)
        paths.append(save_figure(fig, target, config, style=style, close=False))
    if keep_legacy:
        paths.append(save_figure(fig, path, config, style="clean", close=False))
    plt.close(fig)
    return paths
