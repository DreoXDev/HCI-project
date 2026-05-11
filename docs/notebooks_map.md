# Mappa notebook

## Notebook production

| Notebook | Scopo | Input principali | Output principali | Quando usarlo |
|---|---|---|---|---|
| `notebooks/00_run_all.ipynb` | Esecuzione guidata della pipeline completa | `config.yaml`, CSV in `data/raw/` e `data/formbricks_raw/` | Output completi in `outputs/` | Demo o riproduzione end-to-end |
| `notebooks/01_user_test_analysis.ipynb` | Analisi user test e tempi osservazionali | `data/raw/users_time.csv` | Tabelle e grafici user test | Ispezione didattica dei tempi/task |
| `notebooks/02_heuristic_analysis.ipynb` | Analisi euristiche consolidate | `data/raw/heuristics_deliveroo.csv`, `data/raw/heuristics_glovo.csv` | Tabelle e grafici euristiche | Lettura dei problemi dopo review |
| `notebooks/03_questionnaire_ueq_nps.ipynb` | Analisi questionario UEQ/NPS | `data/raw/questionnaire_deliveroo.csv`, `data/raw/questionnaire_glovo.csv` | Tabelle UEQ/NPS | Esplorazione dei questionari |
| `notebooks/04_slide_generation.ipynb` | Generazione/validazione slide | `slides/config/slide_deck.yml`, asset in `outputs/` | PPTX in `outputs/slides/` | Controllo manuale del deck |

## Notebook legacy

| Notebook | Stato | Note |
|---|---|---|
| `notebooks/original/stats_ium.ipynb` | legacy | Conservato solo come riferimento storico |
| `notebooks/original/Stats quest utente.ipynb` | legacy | Conservato solo come riferimento storico |

