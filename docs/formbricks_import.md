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

Il nuovo flusso euristico e in due survey: raccolta grezza dei problemi, review manuale, survey severità.

Input consigliato:

```txt
data/raw/formbricks/heuristics_experts_raw.csv
```

Import:

```powershell
python -m src.cli heuristics raw --input data/raw/formbricks/heuristics_experts_raw.csv
```

Output:

```txt
data/processed/heuristics/raw_problems_long.csv
data/processed/heuristics/raw_problems_table.csv
data/processed/heuristics/expert_profiles.csv
reports/heuristics_raw_report.md
```

Poi si modifica manualmente il template `data/templates/heuristics_consolidated_problems_template.csv` e si salva il risultato come `data/processed/heuristics/consolidated_problems.csv`.

Survey severità:

```powershell
python -m src.cli heuristics severity --ratings data/raw/formbricks/heuristics_severity_ratings.csv --problems data/processed/heuristics/consolidated_problems.csv
```

Output:

```txt
data/processed/heuristics/severity_ratings_long.csv
data/processed/heuristics/final_problem_summary.csv
reports/heuristics_final_report.md
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
[NPS][Deliveroo] Quanto consiglieresti Deliveroo
[NPS][Glovo] Quanto consiglieresti Glovo
```

Per le euristiche, il mapping delle colonne vive in:

```txt
config/heuristics_raw_mapping.yml
```

Campi logici obbligatori:

- `evaluator_id`
- `app`
- `short_description`
- `long_description`
- `heuristics`

## Workflow completo

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/export_questionario.csv
python -m src.cli heuristics raw --input data/raw/formbricks/heuristics_experts_raw.csv
# compila data/processed/heuristics/consolidated_problems.csv
python -m src.cli heuristics severity --ratings data/raw/formbricks/heuristics_severity_ratings.csv --problems data/processed/heuristics/consolidated_problems.csv
python -m src.cli validate
python -m src.cli all
```
