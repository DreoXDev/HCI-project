# Troubleshooting

## File Formbricks non trovato

Controlla che i CSV siano in:

```txt
data/formbricks_raw/questionnaire/export_questionario.csv
data/raw/formbricks/heuristics_experts_raw.csv
```

Oppure modifica i path in `config.yaml`.

## Colonne non riconosciute

Usa tag nei titoli Formbricks o aggiorna gli alias in:

```txt
src/schemas/questionnaire_schema.yaml
config/heuristics_raw_mapping.yml
```

## NPS mancante

La pipeline continua. Il grafico NPS e il testo NPS segnalano che il dato non e disponibile.

## Euristiche da revisionare

Apri:

```txt
data/processed/heuristics/raw_problems_table.csv
data/templates/heuristics_consolidated_problems_template.csv
```

Compila `data/processed/heuristics/consolidated_problems.csv`. Quando hai la seconda survey:

```powershell
python -m src.cli heuristics severity --ratings data/raw/formbricks/heuristics_severity_ratings.csv --problems data/processed/heuristics/consolidated_problems.csv
python -m src.cli validate
```

## Report euristiche con errori

Controlla:

```txt
reports/heuristics_import_report.md
reports/heuristics_raw_report.md
reports/heuristics_final_report.md
```

Gli errori piu comuni sono colonne Formbricks non riconosciute, euristiche non normalizzabili, problemi parziali o severita fuori scala 0-4.

## Rigenerare gli output

Poi rilancia:

```powershell
python -m src.cli all
```

## Test

```powershell
python -m pytest
```
