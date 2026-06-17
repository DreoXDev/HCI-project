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

Questo path viene creato localmente con `python -m src.cli create-templates` ed e ignorato da Git.

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

Gli errori più comuni sono colonne Formbricks non riconosciute, euristiche non normalizzabili, problemi parziali o severità fuori scala 0-4.

## Rigenerare gli output

Poi rilancia:

```powershell
python -m src.cli all
```

## Test

```powershell
python -m pytest
```

## Errori nella pipeline severità deduplicata

### `problem_id` non valido

Eseguire:

```powershell
python -m src.cli heuristics validate-clean --problems data/processed/heuristics/clean_problems.csv
```

Gli ID devono seguire il formato `P001`, `P002`, ... e devono essere univoci.

### Nessuna colonna `[P001]` trovata

Controllare i titoli delle domande nel secondo form Formbricks. Ogni domanda di severità deve contenere il codice tra parentesi quadre:

```text
[P001] Titolo problema
```

### Severità non convertibile

Usare valori numerici `0`, `1`, `2`, `3`, `4` oppure opzioni testuali come `3 - Problema maggiore`. Valori fuori scala bloccano o generano warning.

### Problema nel form ma non nel file clean

Con `--strict` la pipeline si ferma. Correggere il titolo della domanda Formbricks o aggiungere il problema a `clean_problems.csv` se è davvero parte del dataset finale.
