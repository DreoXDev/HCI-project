from __future__ import annotations

import matplotlib.pyplot as plt

from src.config import load_config
from src.slide_export.slide_manifest import generate_slide_manifest
from src.visualization.theme import save_figure_variants


def test_save_figure_variants_creates_png_and_svg(tmp_path) -> None:
    config = load_config("config.yaml")
    fig, ax = plt.subplots()
    ax.bar(["Deliveroo", "Glovo"], [1, 2])

    paths = save_figure_variants(fig, tmp_path / "demo_chart.png", config, plot_style="both", keep_legacy=False)

    assert len(paths) == 2
    assert any("dark" in str(path) for path in paths)
    assert any("presentation" in str(path) for path in paths)
    for path in paths:
        assert path.exists()
        assert path.with_suffix(".svg").exists()


def test_slide_manifest_contains_presentation_references() -> None:
    generate_slide_manifest()

    manifest = open("outputs/slide_manifest.md", encoding="utf-8").read()

    assert "outputs/figures/presentation/" in manifest
    assert "outputs/figures/dark/" in manifest
