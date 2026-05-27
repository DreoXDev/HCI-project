# Mappa CLI

> [!info]
> Tutti i comandi partono da `python -m src.cli`.

## Comandi principali

| Comando | Scopo |
|---|---|
| `validate` | Valida i CSV normalizzati |
| `clean-outputs` | Rimuove artefatti rigenerabili senza toccare dati, template e testi statici |
| `full-pipeline` | Rigenera analisi, asset, testi, slide pack e, con `--generate-slides`, entrambi i PPTX finali |
| `generate-slides` | Crea un PPTX dalla config indicata |
| `build-slide-pack` | Prepara testi e asset narrativi per le slide |
| `quality-check` | Controlla dati, output e documentazione |
| `validate-slide-template` | Controlla i `TEMPLATE_ID` del template |
| `validate-slide-assets` | Controlla asset richiesti dal deck |

## Pipeline completa

```powershell
python -m src.cli full-pipeline --plot-style both --generate-slides --no-export-pdf
python -m src.cli full-pipeline --plot-style both --generate-slides --export-pdf
```

Con `--generate-slides`, la pipeline completa produce:

- `outputs/slides/final_report.pptx`
- `outputs/slides/user_task_deck.pptx`

Con `--export-pdf`, esporta anche i PDF dei deck generati.

> [!tip]
> `full-pipeline` pulisce automaticamente `outputs/` e `reports/` prima di rigenerare gli artefatti. Il comando `all` resta disponibile per compatibilità, ma non è il flusso production consigliato.

## Pulizia output

```powershell
python -m src.cli clean-outputs
```

Rimuove solo output rigenerabili. Non tocca `data/`, `slides/templates/`, `slides/content/` o `slides/assets/appendices/`.

## Import Formbricks

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/formbricks_questionnaire_demo_12_users.csv
python -m src.cli import-formbricks-heuristics-discovery --input data/formbricks_raw/heuristics_discovery/formbricks_heuristics_discovery_demo_6_experts.csv
python -m src.cli import-formbricks-heuristics-ratings --input data/formbricks_raw/heuristics_ratings/formbricks_heuristics_ratings_demo_6_experts.csv --output data/templates/heuristics_consolidated_problems_demo.csv
```

## Euristiche deduplicate

```powershell
python -m src.cli heuristics validate-clean --problems data/processed/heuristics/clean_problems.csv
python -m src.cli heuristics import-severity-formbricks --input data/formbricks_raw/heuristics/severity_ratings_export.csv --output data/processed/heuristics/problem_ratings_long.csv
python -m src.cli heuristics join-severity --problems data/processed/heuristics/clean_problems.csv --ratings data/processed/heuristics/problem_ratings_long.csv --output data/processed/heuristics/heuristic_final_dataset.csv
python -m src.cli heuristics analyze-final --dataset data/processed/heuristics/heuristic_final_dataset.csv --out outputs/heuristics
python -m src.cli heuristics severity-pipeline --problems data/processed/heuristics/clean_problems.csv --ratings-export data/formbricks_raw/heuristics/severity_ratings_export.csv --out outputs/heuristics --strict
```

> [!info]
> `severity-pipeline` esegue validazione, import Formbricks wide-to-long, join e generazione di grafici, tabelle e testi.

## Slide

```powershell
python -m src.cli validate-slide-template
python -m src.cli validate-slide-assets
python -m src.cli generate-slides --auto --overwrite
python -m src.cli generate-slides --config slides/config/user_task_deck.yml --overwrite
python -m src.cli build-slide-pack --export-pdf
```

## Note

> [!warning]
> La CLI usa un parser globale: alcune opzioni sono visibili per più comandi, ma hanno effetto solo dove indicato.
