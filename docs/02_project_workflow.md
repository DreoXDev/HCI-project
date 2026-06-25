# Project Workflow

1. Choose the two systems to compare.
2. Update app metadata, colors and labels in `config/apps.yaml` and `config/theme.yaml`.
3. Define tasks in `config/tasks.yaml`.
4. Collect expert heuristic findings and severity ratings.
5. Run user tests and record task outcomes, times, help requests and notes.
6. Export UEQ/NPS questionnaire data.
7. Run `python -m src.cli validate`.
8. Run the full pipeline and inspect charts/tables.
9. Generate the PPTX.
10. Review the deck manually, but move repeatable edits back into config/code.
11. Export final PDF.

The toolchain is the source of truth for metrics, statistical tests, UEQ scoring and benchmark categories. Manual edits should mainly polish language, ordering and visual details.
