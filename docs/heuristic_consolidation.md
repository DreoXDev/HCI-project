# Review manuale delle euristiche

La valutazione euristica non viene deduplicata automaticamente. Il toolkit importa ogni riga Formbricks come problema candidato e lascia al team la decisione su quali segnalazioni descrivono lo stesso problema.

## File generati dall'import

```txt
data/processed/heuristics_candidates.csv
data/processed/heuristics_review.csv
reports/heuristics_import_report.md
reports/heuristics_import_errors.csv
```

`heuristics_candidates.csv` e una fotografia normalizzata dell'export. `heuristics_review.csv` e il file da modificare manualmente.

## Colonne da modificare

- `problem_group_id`: stesso valore per problemi simili o duplicati
- `include`: `true` per tenere la riga, `false` per escluderla dalla build finale
- `review_notes`: annotazioni libere

Le altre colonne dovrebbero restare derivate dall'import, salvo correzioni motivate.

## Regole di gruppo

Esempio:

| candidate_id | short_description | evaluator_id | problem_group_id |
| --- | --- | --- | --- |
| C001 | Home troppo piena | EU1 | PG001 |
| C002 | Troppe informazioni nella home | EU2 | PG001 |
| C003 | Mancanza feedback checkout | EU1 | PG002 |

## Build finale

```powershell
python -m src.cli build-heuristics-from-review --input data/processed/heuristics_review.csv --output-dir data/raw
```

Il comando genera un problema finale per ogni `problem_group_id` e calcola:

- ID problema per app (`PD1`, `PG1`, ...)
- descrizione breve e lunga dalla riga con severita piu alta
- euristiche violate senza duplicati
- popolarita come numero di valutatori distinti
- media, deviazione standard, mediana e IQR della severita
- priorita `A/B/C` da `top5` con test binomiale

Output:

```txt
data/raw/heuristics_deliveroo.csv
data/raw/heuristics_glovo.csv
reports/heuristics_build_report.md
```

## Flusso legacy

Il vecchio `heuristics_consolidation_template.csv` puo ancora essere presente in alcune doc o output storici, ma il flusso consigliato per nuovi dati e `heuristics_review.csv` + `build-heuristics-from-review`.
