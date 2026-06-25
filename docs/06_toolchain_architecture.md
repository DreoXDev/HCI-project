# Toolchain Architecture

```text
raw CSV / config
  -> validation
  -> cleaned data
  -> analysis modules
  -> chart PNG / table CSV
  -> slide manifest
  -> PPTX builder
  -> optional PDF export
  -> run report
```

## Main Modules

- `src/cli.py`: command-line entrypoint.
- `src/validation.py`: input validation.
- `src/final_assets.py`: final chart/table assets.
- `scripts/validate_quantitative_report.py`: detailed quantitative tables and charts.
- `src/analysis/ueq_scoring.py`: UEQ raw-to-standard transformation.
- `src/analysis/ueq_benchmark.py`: official benchmark thresholds and categories.
- `src/slide_export/auto_deck.py`: generated slide order and content selection.
- `src/slide_export/pptx_generator.py`: PowerPoint generation.
- `src/slide_export/pdf_export.py`: LibreOffice PDF export.
- `src/run_manifest.py`: reproducibility manifest and environment doctor.

## Adding A Chart

Add the calculation, write the chart under `outputs/charts/`, add a slide spec or manifest entry, add a focused test, then regenerate the deck.

## Adding A Slide

Prefer `config/slides.yaml` for planning and `src/slide_export/auto_deck.py` for current runtime behavior. Use native PPTX tables where manual editing is expected.
