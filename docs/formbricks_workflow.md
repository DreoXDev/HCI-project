# Workflow Formbricks

Questo e il workflow raccomandato per nuovi progetti.

## 1. Esporta i dati

Salva i file in:

```txt
data/formbricks_raw/questionnaire/export_questionario.csv
data/formbricks_raw/heuristics/export_esperti.csv
data/raw/users_time.csv
```

`users_time.csv` non arriva da Formbricks: e il formato osservazionale compilato dagli osservatori durante i test utenti.

## 2. Importa questionario ed euristiche

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/export_questionario.csv
python -m src.cli import-formbricks-heuristics --input data/formbricks_raw/heuristics/export_esperti.csv
```

## 3. Revisiona le euristiche

Apri:

```txt
data/processed/heuristics_review.csv
```

Assegna lo stesso `problem_group_id` alle righe che descrivono lo stesso problema.

## 4. Genera i CSV finali

```powershell
python -m src.cli build-heuristics-from-review --input data/processed/heuristics_review.csv --output-dir data/raw
```

## 5. Valida e analizza

```powershell
python -m src.cli validate
python -m src.cli all
```

## Report da controllare

```txt
outputs/import_report.md
reports/heuristics_import_report.md
reports/heuristics_import_errors.csv
reports/heuristics_build_report.md
outputs/slide_manifest.md
```
