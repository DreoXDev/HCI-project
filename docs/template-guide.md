# PowerPoint Template Guide

## Active Template

The active template used by the pipeline is:

```text
slides/templates/Deliveroo_vs_Glovo_clean_python_ready_template.pptx
```

The full legacy/safety copy is:

```text
slides/templates/hci_project_template_legacy_full.pptx
```

Template paths are documented in `config/presentation.yaml` and the runtime deck config is `slides/config/slide_deck.yml`.

## What TEMPLATE_ID Means

Each slide layout in the template deck contains a hidden or small technical marker:

```text
TEMPLATE_ID:<layout_id>
```

The generator duplicates the slide with the matching `TEMPLATE_ID`, fills fields, replaces images/tables, and removes the technical marker in the generated deck.

Do not rename or delete `TEMPLATE_ID` markers unless you also update the generator/config.

## Supported Layouts

| TEMPLATE_ID | Use | Required placeholders | Editable? | Notes |
| --- | --- | --- | --- | --- |
| `cover` | Cover slide | `PROJECT_TITLE`, `PROJECT_SUBTITLE`, `AUTHORS_DATE` | yes, keep marker | Used once in the final report. |
| `section_divider_neutral` | Section divider | `SECTION_NAME` | yes | Main divider used by the current final report. |
| `section_divider_deliveroo` | App-specific divider | `SECTION_NAME` | yes | Optional/legacy support. |
| `section_divider_glovo` | App-specific divider | `SECTION_NAME` | yes | Optional/legacy support. |
| `graph_full_neutral` | Generic chart | `GRAPH_TITLE`, `GRAPH_MAIN`, `INSIGHT_TEXT` | yes | Used for non app-specific charts. |
| `graph_full_deliveroo` | Deliveroo chart | `GRAPH_TITLE`, `GRAPH_MAIN`, `INSIGHT_TEXT` | yes | Keep Deliveroo branding. |
| `graph_full_glovo` | Glovo chart | `GRAPH_TITLE`, `GRAPH_MAIN`, `INSIGHT_TEXT` | yes | Keep Glovo branding. |
| `comparison_neutral` | Two visuals or visual+table | `COMPARISON_TITLE`, `LEFT_GRAPH`, `RIGHT_GRAPH`, `SUMMARY_TEXT` | yes | Heavily used in the report. |
| `table_large_neutral` | Large native PPTX table | `TABLE_TITLE`, `TABLE_MAIN`, `TABLE_FOOTNOTE` | yes | Used for generated editable tables. |
| `table_large_deliveroo` | Deliveroo table | `TABLE_TITLE`, `TABLE_MAIN`, `TABLE_FOOTNOTE` | yes | Keep placeholder names. |
| `table_large_glovo` | Glovo table | `TABLE_TITLE`, `TABLE_MAIN`, `TABLE_FOOTNOTE` | yes | Keep placeholder names. |
| `text_only_neutral` | Text slide | `TEXT_TITLE`, `TEXT_BODY` | yes | Main static text layout. |
| `text_only_deliveroo` | Deliveroo text slide | `TEXT_TITLE`, `TEXT_BODY` | yes | App-specific text. |
| `text_only_glovo` | Glovo text slide | `TEXT_TITLE`, `TEXT_BODY` | yes | App-specific text. |
| `findings_*` | Findings cards | `FINDINGS_TITLE`, `FINDING_1..4`, `MINI_GRAPH`, `SUMMARY_TEXT` | yes | Optional legacy/auto mode. |
| `task_results_*` | Task cards | `TASK_TITLE`, `TASK_DESCRIPTION`, `TASK_SCREENSHOT`, `SUCCESS_RATE_VALUE`, `AVG_TIME_VALUE` | yes | Optional task detail mode. |
| `ueq_question_*` | UEQ question detail | `QUESTION_TITLE`, `BOXPLOT`, `MEAN_VALUE`, `STD_VALUE`, `MIN_VALUE`, `MAX_VALUE` | yes | Optional UEQ item detail mode. |
| `final_verdict` | Legacy final verdict layout | verdict fields and `SUMMARY_GRAPH` | yes | Kept for compatibility. |
| `sources` | Sources slide | `SOURCES_TITLE`, `SOURCES_LIST` | yes | Used only when sources are enabled. |

Run `python tools/audit_pptx_template.py` to generate the current inventory in `docs/template-audit.md`.

## Safe Manual Edits

Safe to change:

- background colors;
- decorative shapes;
- fonts and font sizes;
- app-specific accent colors;
- image frame styling;
- layout spacing, as long as placeholders remain findable.

Do not change without code/config updates:

- `TEMPLATE_ID` text;
- placeholder names;
- placeholder text labels such as `GRAPH_MAIN`, `TABLE_MAIN`, `TEXT_BODY`;
- slide deletion for layouts still listed in `docs/template-audit.md` as used or optional.

## Example 1 - Change Project Colors

1. Open `slides/templates/Deliveroo_vs_Glovo_clean_python_ready_template.pptx`.
2. Change background and decorative shape colors.
3. Keep all `TEMPLATE_ID` markers.
4. Keep placeholder names/text.
5. Run `python -m src.cli validate-template`.
6. Regenerate the report.

## Example 2 - Adapt To Two Different Apps

1. Update app names/colors in `config/apps.yaml`.
2. Update chart/theme colors in `config/theme.yaml`.
3. Replace logos in `assets/logos/` or adjust configured paths.
4. Update app-specific template backgrounds if desired.
5. Run `python -m src.cli validate-template`.
6. Regenerate the presentation.

## Example 3 - Add A New Layout

1. Duplicate an existing layout slide in the template.
2. Give it a new unique `TEMPLATE_ID`.
3. Add placeholders needed by the new generator code.
4. Update `src/slide_export/template_variants.py` and slide config/code.
5. Add or update tests.
6. Run `python -m src.cli validate-template`.
7. Run the full pipeline.

## Validation Commands

```powershell
python -m src.cli validate-template
python tools/audit_pptx_template.py
python -m src.cli full-pipeline --plot-style both --generate-slides --no-export-pdf
```
