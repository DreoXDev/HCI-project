# Consolidamento euristiche

Le risposte euristiche sono semi-strutturate: due valutatori possono descrivere lo stesso problema con parole diverse. Per questo il toolkit non unisce automaticamente i problemi.

## Output generati dall'import

```txt
data/processed/heuristics_submissions_clean.csv
data/processed/heuristics_consolidation_template.csv
outputs/heuristic_review/all_problems.md
outputs/heuristic_review/grouped_problems.md
outputs/heuristic_review/possible_duplicates.md
```

## Come usare il template

Apri:

```txt
data/processed/heuristics_consolidation_template.csv
```

Poi:

1. assegna o correggi `canonical_problem_id`
2. unisci manualmente problemi simili
3. scrivi `canonical_title` e `canonical_description`
4. controlla le euristiche violate
5. controlla i valori di severita per valutatore

Quando il file e pronto:

```powershell
python -m src.cli build-heuristics-from-consolidation
python -m src.cli analyze-heuristics
```

I file finali saranno:

```txt
data/raw/heuristics_deliveroo.csv
data/raw/heuristics_glovo.csv
```
