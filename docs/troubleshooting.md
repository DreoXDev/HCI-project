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
src/schemas/heuristic_schema.yaml
```

## NPS mancante

La pipeline continua. Il grafico NPS e il testo NPS segnalano che il dato non e disponibile.

## Euristiche da consolidare

Apri:

```txt
data/processed/heuristics_consolidation_template.csv
```

Poi rilancia:

```powershell
python -m src.cli build-heuristics-from-consolidation
python -m src.cli analyze-heuristics
```

## Test

```powershell
python -m pytest
```
