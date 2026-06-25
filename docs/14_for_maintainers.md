# For Maintainers

## Origin

The repository extends/adapts course-provided HCI tooling into a reproducible project pipeline.

## Main Extensions

- Formbricks import support.
- Heuristic problem consolidation and severity analysis.
- User testing effectiveness/efficiency metrics.
- UEQ/NPS scoring and benchmark handling.
- PowerPoint generation from templates.
- Validation reports, audit scripts and run manifests.

## How To Verify Results

Run:

```powershell
python -m src.cli doctor
python -m src.cli validate
python -m src.cli validate-final-data
python -m pytest
```

For presentation review, compare manual and generated PDFs with:

```powershell
python tools/audit/compare_report_pdfs.py --manual path/to/manual.pdf --generated path/to/generated.pdf --out docs/audits/manual_vs_generated_report.md
```

## Known Limits

Some slide ordering still lives in `src/slide_export/auto_deck.py` for compatibility. `config/slides.yaml` documents the target manifest and should guide future refactoring.

PDF export depends on LibreOffice and can fail if the target PDF is open.
