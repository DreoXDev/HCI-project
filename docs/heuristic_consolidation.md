# Review manuale delle euristiche

La deduplicazione dei problemi euristici resta manuale. Il toolkit normalizza l'export Formbricks grezzo e produce tabelle, grafici e report per aiutare il gruppo a leggere i problemi raccolti; non prova ad accorpare automaticamente descrizioni simili.

## Fase 1: problemi grezzi

Input consigliato:

```txt
data/raw/formbricks/heuristics_experts_raw.csv
```

Comando:

```powershell
python -m src.cli heuristics raw --input data/raw/formbricks/heuristics_experts_raw.csv
```

Output principali:

```txt
data/processed/heuristics/raw_problems_long.csv
data/processed/heuristics/raw_problems_table.csv
data/processed/heuristics/expert_profiles.csv
data/processed/heuristics/problem_counts_by_app.csv
data/processed/heuristics/problem_counts_by_evaluator.csv
data/processed/heuristics/heuristic_counts.csv
data/processed/heuristics/evaluator_problem_matrix.csv
outputs/figures/heuristics/
reports/heuristics_raw_report.md
```

La configurazione delle colonne Formbricks e in:

```txt
config/heuristics_raw_mapping.yml
```

## Consolidamento manuale

Dopo la Fase 1, aprire:

```txt
data/processed/heuristics/raw_problems_table.csv
data/templates/heuristics_consolidated_problems_template.csv
```

Creare manualmente:

```txt
data/processed/heuristics/consolidated_problems.csv
```

Colonne:

```csv
final_problem_id,app,short_description,long_description,heuristics,source_raw_problem_ids,notes
```

Usare ID chiari, per esempio `D-PB01` per Deliveroo e `G-PB01` per Glovo. `source_raw_problem_ids` deve mantenere il legame con i problemi grezzi, per esempio `RAW001;RAW007`.

## Fase 2: severita

Quando e disponibile la seconda survey Formbricks con rating 0-4:

```powershell
python -m src.cli heuristics severity --ratings data/raw/formbricks/heuristics_severity_ratings.csv --problems data/processed/heuristics/consolidated_problems.csv
```

Output previsti:

```txt
data/processed/heuristics/severity_ratings_long.csv
data/processed/heuristics/final_problem_summary.csv
data/processed/heuristics/final_evaluator_problem_matrix.csv
data/processed/heuristics/problem_priority_bands.csv
reports/heuristics_final_report.md
```

La priorita e trasparente:

- `A`: severita media >= 3.25
- `B`: severita media >= 2.00 e < 3.25
- `C`: severita media < 2.00

I dark pattern possono essere discussi manualmente nella presentazione, ma non fanno piu parte della pipeline automatica del toolkit.
