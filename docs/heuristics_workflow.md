# Workflow euristiche Formbricks

Il flusso euristico ha due fasi automatiche separate da una deduplicazione manuale.

```text
problemi grezzi -> review manuale -> clean_problems.csv -> survey severità -> output finali
```

> [!info]
> La deduplicazione semantica non viene automatizzata: richiede giudizio umano. Il toolkit valida il file clean e automatizza tutto ciò che avviene dopo.

## 1. Raccolta problemi

Ogni esperto compila il primo form con i problemi trovati. Salvare l'export in:

```text
data/formbricks_raw/heuristics/problems_raw_export.csv
```

Poi eseguire:

```powershell
python -m src.cli heuristics raw --input data/formbricks_raw/heuristics/problems_raw_export.csv
```

La pipeline genera tabelle grezze in `data/processed/heuristics/`, utili per la review.

## 2. Deduplicazione manuale

Creare:

```text
data/processed/heuristics/clean_problems.csv
```

Colonne obbligatorie:

| Colonna | Descrizione |
|---|---|
| `problem_id` | ID stabile, per esempio `P001` |
| `app` | App analizzata |
| `screen` | Schermata o area |
| `heuristic` | Euristica violata |
| `title` | Titolo breve |
| `description` | Descrizione pulita |

Colonne consigliate: `source_count`, `notes`, `raw_problem_ids`, `recommendation`, `impact`.

Validare il file:

```powershell
python -m src.cli heuristics validate-clean --problems data/processed/heuristics/clean_problems.csv
```

## 3. Survey di severità

Nel secondo form Formbricks inserire una domanda per ogni problema. Il titolo deve contenere l'ID:

```text
[P001] CTA checkout poco visibile
```

Scala Nielsen:

| Valore | Significato |
|---:|---|
| 0 | Non è un problema |
| 1 | Problema cosmetico |
| 2 | Problema minore |
| 3 | Problema maggiore |
| 4 | Problema critico |

> [!warning]
> Le colonne `- Option ID` dell'export Formbricks sono ignorate. Il collegamento avviene solo tramite il pattern `[P001]`.

## 4. Pipeline finale

Salvare l'export delle valutazioni in:

```text
data/formbricks_raw/heuristics/severity_ratings_export.csv
```

Eseguire:

```powershell
python -m src.cli heuristics severity-pipeline --problems data/processed/heuristics/clean_problems.csv --ratings-export data/formbricks_raw/heuristics/severity_ratings_export.csv --out outputs/heuristics --strict
```

Il comando esegue:

1. validazione di `clean_problems.csv`;
2. import wide-to-long dell'export Formbricks;
3. join tra problemi clean e valutazioni;
4. generazione di riepiloghi, tabelle, grafici e testi.

## Output

Dataset intermedi:

```text
data/processed/heuristics/problem_ratings_long.csv
data/processed/heuristics/heuristic_final_dataset.csv
data/processed/heuristics/problem_severity_summary.csv
data/processed/heuristics/expert_problem_matrix.csv
data/processed/heuristics/heuristic_severity_summary.csv
data/processed/heuristics/app_severity_summary.csv
```

Asset finali:

```text
outputs/heuristics/charts/
outputs/heuristics/tables/
outputs/heuristics/texts/
```

> [!tip]
> `python -m src.cli all --plot-style both` include automaticamente questa pipeline se trova `clean_problems.csv` e `severity_ratings_export.csv`; altrimenti mostra un warning e continua.
