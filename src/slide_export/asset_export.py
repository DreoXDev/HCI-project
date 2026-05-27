from __future__ import annotations


def export_slide_assets() -> list[str]:
    """Compatibility shim.

    Slide assets are no longer copied into `outputs/slide_assets/`.
    Use `outputs/slide_assets/pack/assets_manifest.csv` to reference the source files.
    """
    return []

