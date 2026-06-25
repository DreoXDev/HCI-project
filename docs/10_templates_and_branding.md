# Templates And Branding

## PowerPoint Template

The base template is:

```text
slides/templates/Deliveroo_vs_Glovo_clean_python_ready_template.pptx
```

The legacy full copy is:

```text
slides/templates/hci_project_template_legacy_full.pptx
```

The generator expects placeholders and layout conventions from this template. Do not rename shapes/placeholders without updating the slide export code.

For detailed layout IDs and safe editing rules, see [template-guide.md](template-guide.md) and regenerate `docs/template-audit.md` with:

```powershell
python tools/audit_pptx_template.py
```

## Colors And Logos

Update:

- `config/apps.yaml` for app labels, colors and logo paths;
- `config/theme.yaml` for global palette and table/chart style;
- `assets/logos/` for replacement logos.

## Adding Layouts

Add the layout to the PPTX template, document its placeholder names, then update `src/slide_export` to populate it.

## Regeneration

```powershell
python -m src.cli full-pipeline --plot-style both --generate-slides --no-export-pdf
```

Use `--export-pdf` after closing any open PDF viewer.
