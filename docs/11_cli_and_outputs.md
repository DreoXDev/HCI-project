# CLI And Outputs

## Common Commands

```powershell
python -m src.cli doctor
python -m src.cli validate
python -m src.cli validate-final-data
python -m src.cli full-pipeline --plot-style both --generate-slides --no-export-pdf
python -m src.cli full-pipeline --plot-style both --generate-slides --export-pdf
python -m pytest
```

## Output Layout

- `outputs/charts/`: generated charts.
- `outputs/tables/`: CSV tables for slides/reports.
- `outputs/reports/`: validation, doctor and run reports.
- `outputs/slides/`: final PPTX/PDF and slide-generation artifacts.
- `outputs/slide_assets/`: packaged assets used by the deck builder.
- `docs/audits/`: manual-vs-generated audit outputs.

## Run Manifest

Every full pipeline run writes:

- `outputs/reports/pipeline_run.md`
- `outputs/reports/pipeline_run.json`
