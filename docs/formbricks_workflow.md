# Workflow Formbricks

Questo e il workflow raccomandato per nuovi progetti.

## 1. Esporta i dati

Salva i file in:

```txt
data/formbricks_raw/questionnaire/export_questionario.csv
data/raw/formbricks/heuristics_experts_raw.csv
data/raw/users_time.csv
```

`users_time.csv` non arriva da Formbricks: e il formato osservazionale compilato dagli osservatori durante i test utenti.

## 2. Importa questionario e survey euristica raw

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/export_questionario.csv
python -m src.cli heuristics raw --input data/raw/formbricks/heuristics_experts_raw.csv
```

## 3. Revisiona le euristiche

Apri:

```txt
data/processed/heuristics/raw_problems_table.csv
data/templates/heuristics_consolidated_problems_template.csv
```

Accorpa manualmente i problemi simili e crea `data/processed/heuristics/consolidated_problems.csv`.

## 4. Survey severita

```powershell
python -m src.cli heuristics severity --ratings data/raw/formbricks/heuristics_severity_ratings.csv --problems data/processed/heuristics/consolidated_problems.csv
```

## 5. Valida e analizza

```powershell
python -m src.cli validate
python -m src.cli all
```

## Report da controllare

```txt
outputs/import_report.md
reports/heuristics_raw_report.md
reports/heuristics_final_report.md
outputs/slide_manifest.md
```
