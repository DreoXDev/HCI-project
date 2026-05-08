from __future__ import annotations

import matplotlib.pyplot as plt

from src.config import load_config
from src.visualization.theme import apply_base_theme, get_brand_palette


def test_get_brand_palette_contains_project_systems() -> None:
    config = load_config("config.yaml")

    palette = get_brand_palette(config)

    assert palette["Deliveroo"] == "#00CCBC"
    assert palette["Glovo"] == "#FFC244"
    assert palette[config["project"]["system_1"]] == "#00CCBC"
    assert palette[config["project"]["system_2"]] == "#FFC244"


def test_apply_base_theme_does_not_error() -> None:
    config = load_config("config.yaml")

    apply_base_theme(config, "dark")
    fig, ax = plt.subplots()
    ax.plot([1, 2], [1, 2])
    plt.close(fig)

    apply_base_theme(config, "presentation")
    fig, ax = plt.subplots()
    ax.plot([1, 2], [2, 1])
    plt.close(fig)
