# HCI Toolkit - Deliveroo vs Glovo

> [!info]
> Toolkit Python per generare analisi, grafici, tabelle, testi, slide PPTX e PDF finali del progetto HCI Deliveroo vs Glovo.

## Quick Start

```powershell
python -m pip install -r requirements.txt
python -m src.cli full-pipeline --plot-style both --generate-slides --no-export-pdf
```

Per installare i CSV reali ricevuti dal gruppo nei percorsi canonici:

```powershell
python -m src.cli prepare-real-inputs --source-dir data/inbox --overwrite
```

Con i dati attuali il report e marcato come parziale: 18 utenti su 24 previsti. Quando arriva l'ultimo blocco utenti, rilanciare il bootstrap e la full pipeline.

Il comando rigenera analisi, asset e le due presentazioni principali:

- `outputs/slides/final_report.pptx`
- `outputs/slides/user_task_deck.pptx`

Per rigenerare solo la presentazione per i partecipanti ai task:

```powershell
python -m src.cli generate-slides --config slides/config/user_task_deck.yml --overwrite
```

> [!warning]
> L'export PDF richiede LibreOffice installato e accessibile come `soffice` o `libreoffice`.

Pulizia degli output rigenerabili, senza toccare dati, template e testi statici:

```powershell
python -m src.cli clean-outputs
```

Gli output finali sono concentrati in `outputs/`: CSV in `outputs/tables/`, Markdown tabellari in `outputs/tables/markdown/`, testi generati in `outputs/texts/`, asset intermedi per le slide in `outputs/slide_assets/`, e presentazioni finali in `outputs/slides/`. I testi statici editabili a mano non sono output: restano in `slides/content/reference_static_texts.md`.

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
- [Input reali progetto finale](docs/real_project_inputs.md)
- [Workflow Formbricks](docs/formbricks_workflow.md)
- [Generazione slide](docs/slide_generation.md)
- [Stile visuale](docs/visual_style.md)
- [Manuale slide finali](manual_slides.md)
- [Snippet testuali](docs/text_snippets.md)

I dati demo inclusi sono inventati e servono solo per provare la pipeline.
