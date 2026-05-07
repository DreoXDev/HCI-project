# Troubleshooting

## File Formbricks non trovato

Controlla che i CSV siano in:

```txt
data/formbricks_raw/questionnaire/export_questionario.csv
data/formbricks_raw/heuristics/export_esperti.csv
```

Oppure modifica i path in `config.yaml`.

## Colonne non riconosciute

Usa tag nei titoli Formbricks o aggiorna gli alias in:

```txt
src/schemas/questionnaire_schema.yaml
config/formbricks_heuristics_mapping.yml
```

## NPS mancante

La pipeline continua. Il grafico NPS e il testo NPS segnalano che il dato non e disponibile.

## Euristiche da revisionare

Apri:

```txt
data/processed/heuristics_review.csv
```

Assegna `problem_group_id` ai problemi simili, poi rilancia:

```powershell
python -m src.cli build-heuristics-from-review --input data/processed/heuristics_review.csv --output-dir data/raw
python -m src.cli validate
```

## Report euristiche con errori

Controlla:

```txt
reports/heuristics_import_report.md
reports/heuristics_import_errors.csv
```

Gli errori piu comuni sono euristiche non riconosciute, severita fuori range o valori `top5` non interpretabili.

## Rigenerare gli output

Poi rilancia:

```powershell
python -m src.cli all
```

## Test

```powershell
python -m pytest
```
