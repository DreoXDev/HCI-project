# Troubleshooting

## PDF Export Fails

Close `final_report.pdf` in Acrobat/PowerPoint and rerun with `--export-pdf`. Windows blocks overwriting files that are open in another process.

## Missing CSV Columns

Run:

```powershell
python -m src.cli validate
```

Compare your file with templates in `templates/data/` and schemas in `schemas/`.

## UEQ Values Outside Range

Raw UEQ values must be `1..7`. NPS must be `0..10`. Fix the source CSV rather than patching generated outputs.

## Slide Assets Missing

Run the full pipeline before `generate-slides`, or use:

```powershell
python -m src.cli validate-slide-assets
```
