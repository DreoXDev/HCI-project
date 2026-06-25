# Mappa CLI

> [!info]
> Tutti i comandi partono da `python -m src.cli`.

## Comandi principali

| Comando | Scopo |
|---|---|
| `doctor` | Controlla ambiente, dipendenze, LibreOffice, template e scrittura output |
| `validate` | Valida i CSV normalizzati |
| `validate-final-data` | Esegue i controlli finali sui dati e sul deck generato |
| `clean-outputs` | Rimuove artefatti rigenerabili senza toccare dati, template e testi statici |
| `full-pipeline` | Rigenera analisi, asset, testi, slide pack e, con `--generate-slides`, il PPTX finale |
| `generate-slides` | Crea un PPTX dalla config indicata |
| `build-slide-pack` | Prepara testi e asset narrativi per le slide |
| `quality-check` | Controlla dati, output e documentazione |
| `validate-template` / `validate-slide-template` | Controlla i `TEMPLATE_ID` del template |
| `validate-slide-assets` | Controlla asset richiesti dal deck |

## Pipeline completa

```powershell
python -m src.cli full-pipeline --plot-style both --generate-slides --no-export-pdf
python -m src.cli full-pipeline --plot-style both --generate-slides --export-pdf
```

Con `--generate-slides`, la pipeline completa produce:

- `outputs/slides/final_report.pptx`
- `outputs/reports/pipeline_run.md`
- `outputs/reports/pipeline_run.json`
- report di validazione in `outputs/reports/`

Con `--export-pdf`, esporta anche il PDF del deck generato.

> [!tip]
> `full-pipeline` pulisce automaticamente `outputs/` e `reports/` prima di rigenerare gli artefatti. Il comando `all` resta disponibile per compatibilità, ma non è il flusso production consigliato.

## Pulizia output

```powershell
python -m src.cli clean-outputs
```

Rimuove solo output rigenerabili. Non tocca `data/`, `slides/templates/`, `slides/content/` o `slides/assets/appendices/`.

## Import Formbricks

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/users_questionnaire_export.csv
python -m src.cli heuristics severity-pipeline --problems data/processed/heuristics/clean_problems.csv --ratings-export data/formbricks_raw/heuristics/severity_ratings_export.csv --out outputs/heuristics --strict
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
python -m src.cli validate-template
python -m src.cli validate-slide-assets
python -m src.cli generate-slides --auto --overwrite
python -m src.cli build-slide-pack --export-pdf
```

La presentazione finale da revisionare manualmente si trova in `outputs/slides/final_report.pptx`. Il PDF, quando esportato, si trova in `outputs/slides/final_report.pdf`.

## Note

> [!warning]
> La CLI usa un parser globale: alcune opzioni sono visibili per più comandi, ma hanno effetto solo dove indicato.
