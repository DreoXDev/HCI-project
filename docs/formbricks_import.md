# Import Formbricks

I CSV esportati da Formbricks non vanno modificati a mano. Vanno salvati in `data/formbricks_raw/` e convertiti con la CLI.

## Questionario

Input consigliato:

```txt
data/formbricks_raw/questionnaire/export_questionario.csv
```

Comando:

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/export_questionario.csv
```

Output:

```txt
data/raw/questionnaire_deliveroo.csv
data/raw/questionnaire_glovo.csv
data/processed/questionnaire_formbricks_clean.csv
data/processed/questionnaire_long.csv
outputs/import_report.md
```

Per includere risposte incomplete:

```powershell
python -m src.cli import-formbricks-questionnaire --include-unfinished
```

## Euristiche

Il nuovo flusso euristico e in due fasi: import dei candidati, review manuale, build dei CSV finali.

Input consigliato:

```txt
data/formbricks_raw/heuristics/export_esperti.csv
```

Import:

```powershell
python -m src.cli import-formbricks-heuristics --input data/formbricks_raw/heuristics/export_esperti.csv
```

Output:

```txt
data/processed/heuristics_candidates.csv
data/processed/heuristics_review.csv
reports/heuristics_import_report.md
reports/heuristics_import_errors.csv
```

Poi si modifica manualmente `data/processed/heuristics_review.csv`, soprattutto `problem_group_id`.

Build finale:

```powershell
python -m src.cli build-heuristics-from-review --input data/processed/heuristics_review.csv --output-dir data/raw
```

Output:

```txt
data/raw/heuristics_deliveroo.csv
data/raw/heuristics_glovo.csv
reports/heuristics_build_report.md
```

## User test

La pipeline di analisi legge:

```txt
data/raw/users_time.csv
```

Questo file non e un export Formbricks. Deve essere compilato dagli osservatori durante i test utenti usando il template `data/examples/users_time_template.xlsx`.

## Tag e mapping

Per il questionario usare tag nei titoli quando possibile:

```txt
[DEMOGRAPHIC] Eta
[UEQ][Deliveroo] Fastidioso/Piacevole
[UEQ][Glovo] Fastidioso/Piacevole
[NPS][Deliveroo] Quanto consiglieresti Deliveroo?
[NPS][Glovo] Quanto consiglieresti Glovo?
```

Per le euristiche, il mapping delle colonne vive in:

```txt
config/formbricks_heuristics_mapping.yml
```

Campi logici obbligatori:

- `evaluator_id`
- `app`
- `task`
- `short_description`
- `long_description`
- `heuristic`
- `severity`
- `top5`

## Workflow completo

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/export_questionario.csv
python -m src.cli import-formbricks-heuristics --input data/formbricks_raw/heuristics/export_esperti.csv
# revisiona data/processed/heuristics_review.csv
python -m src.cli build-heuristics-from-review --input data/processed/heuristics_review.csv --output-dir data/raw
python -m src.cli validate
python -m src.cli all
```
