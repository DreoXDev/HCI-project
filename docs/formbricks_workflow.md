# Workflow Formbricks

Questa pagina descrive i percorsi canonici finali usati dalla pipeline.

## Questionario utenti

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/users_questionnaire_export.csv
```

Output normalizzati:

```text
data/raw/questionnaire_deliveroo.csv
data/raw/questionnaire_glovo.csv
data/processed/questionnaire/
```

## Euristiche finali

La deduplicazione e gia consolidata in:

```text
data/processed/heuristics/clean_problems.csv
```

L'export Formbricks finale delle severita e:

```text
data/formbricks_raw/heuristics/severity_ratings_export.csv
```

Comando unico:

```powershell
python -m src.cli heuristics severity-pipeline --problems data/processed/heuristics/clean_problems.csv --ratings-export data/formbricks_raw/heuristics/severity_ratings_export.csv --out outputs/heuristics --strict
```

## Dati osservazionali

I tempi dei test utente sono nel file reale:

```text
data/raw/users_time.csv
```

## Pipeline finale

```powershell
python -m src.cli full-pipeline --plot-style both --generate-slides --no-export-pdf --overwrite
```

Il report finale viene scritto in:

```text
outputs/final/final_report.pptx
```
