# Mappa notebook

> [!Info]
> I notebook sono wrapper didattici sopra i moduli `src/`. Per produzione usare la CLI.

## `notebooks/00_run_all.ipynb`

| Campo | Valore |
|---|---|
| Scopo | Eseguire la pipeline completa |
| Input | CSV in `data/` |
| Output | Tutti gli output principali |
| Usa moduli | `src.cli`, `src.config` |
| Produzione | No, usare `python -m src.cli full-pipeline --plot-style both --generate-slides --no-export-pdf` |

## `notebooks/01_user_test_analysis.ipynb`

| Campo | Valore |
|---|---|
| Scopo | Analizzare tempi, errori e successo dei task |
| Input | `data/raw/users_time.csv` |
| Output | Tabelle e grafici user test |
| Produzione | No, usare la CLI |

## `notebooks/02_heuristic_analysis.ipynb`

| Campo | Valore |
|---|---|
| Scopo | Esplorare le euristiche consolidate |
| Input | `data/raw/heuristics_deliveroo.csv`, `data/raw/heuristics_glovo.csv` |
| Output | Tabelle e grafici euristici |
| Produzione | No |

## `notebooks/03_questionnaire_ueq_nps.ipynb`

| Campo | Valore |
|---|---|
| Scopo | Analizzare UEQ e NPS |
| Input | `data/raw/questionnaire_deliveroo.csv`, `data/raw/questionnaire_glovo.csv` |
| Output | Tabelle UEQ/NPS |
| Produzione | No |

## `notebooks/04_slide_generation.ipynb`

| Campo | Valore |
|---|---|
| Scopo | Verificare template e generazione slide |
| Input | `slides/config/slide_deck.yml`, asset in `outputs/` |
| Output | PPTX in `outputs/slides/` |
| Produzione | No |
