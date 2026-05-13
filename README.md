# HCI Toolkit - Deliveroo vs Glovo

> [!info]
> Toolkit Python per generare analisi, grafici, tabelle, testi, slide PPTX e PDF finali del progetto HCI Deliveroo vs Glovo.

## Quick Start

```powershell
python -m pip install -r requirements.txt
python -m src.cli full-pipeline --plot-style both --export-pdf
```

> [!warning]
> L'export PDF richiede LibreOffice installato e accessibile come `soffice` o `libreoffice`.

## Pipeline euristiche Formbricks

Il flusso supporta una deduplicazione manuale seguita da import automatico delle valutazioni di severità:

```powershell
python -m src.cli heuristics raw --input data/formbricks_raw/heuristics/problems_raw_export.csv
python -m src.cli heuristics validate-clean --problems data/processed/heuristics/clean_problems.csv
python -m src.cli heuristics severity-pipeline --problems data/processed/heuristics/clean_problems.csv --ratings-export data/formbricks_raw/heuristics/severity_ratings_export.csv --out outputs/heuristics --strict
```

> [!info]
> La deduplicazione resta manuale: il file stabile è `data/processed/heuristics/clean_problems.csv`. Dopo l'export Formbricks delle valutazioni, la pipeline genera dataset, grafici, tabelle e testi in modo automatico.

## Documentazione

- [Manuale operativo](docs/manual.md)
- [Mappa CLI](docs/cli_api.md)
- [Mappa notebook](docs/notebooks_map.md)
- [Formato dati](docs/data_format.md)
- [Workflow Formbricks](docs/formbricks_workflow.md)
- [Generazione slide](docs/slide_generation.md)
- [Snippet testuali](docs/text_snippets.md)

I dati demo inclusi sono inventati e servono solo per provare la pipeline.
