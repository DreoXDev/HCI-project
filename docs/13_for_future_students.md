# How To Adapt This Repository For Your HCI Project

## Step 1 - Choose The Two Systems

Pick comparable systems and define the comparison objective.

## Step 2 - Update App Configuration

Edit `config/apps.yaml`, `config/theme.yaml` and app-specific text.

## Step 3 - Collect Expert Evaluation Data

Use `templates/data/evaluators_template.csv` and `templates/data/heuristic_findings_template.csv`.

## Step 4 - Collect User Testing Data

Use stable anonymous user ids and task ids. Keep task definitions in `config/tasks.yaml`.

## Step 5 - Export Survey / UEQ Data

Export completed responses and verify `Q01..Q26` plus NPS.

## Step 6 - Validate Your Data

Run `python -m src.cli validate` and fix data issues before generating slides.

## Step 7 - Generate Charts And Report

Run the full pipeline and inspect outputs.

## Step 8 - Review The Generated Presentation

Fix repeatable issues in config/code. Use manual PPTX edits only for final polish.

## Step 9 - Manual Polishing Checklist

- [ ] App names changed
- [ ] Brand colors changed
- [ ] Logos replaced
- [ ] Evaluators data complete
- [ ] Heuristic findings complete
- [ ] User test task data complete
- [ ] UEQ data exported
- [ ] Config validated
- [ ] Full pipeline runs without errors
- [ ] Generated PPTX reviewed manually
- [ ] Final PDF exported

## Step 10 - Final Export

Close the PDF viewer and run the PDF export command.
