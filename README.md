# HCI Toolkit - Deliveroo vs Glovo

Toolkit Python per il progetto HCI: importa dati Formbricks e CSV osservazionali, valida i dataset, genera analisi, grafici, tabelle, testi e, opzionalmente, una presentazione PowerPoint da template.

## Quick Start

```powershell
cd "D:\Projects\IUM\Improved Notebooks\HCI-project"
..\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.cli validate
python -m src.cli all --plot-style both
```

Per il flusso completo con file nuovi, segui solo [Manuale.md](Manuale.md).

## Entry Point

- `python -m src.cli ...`: entry point principale.
- `python main.py ...`: wrapper comodo per gli stessi comandi.

Comandi frequenti:

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/export_questionario.csv
python -m src.cli heuristics raw --input data/raw/formbricks/heuristics_experts_raw.csv
python -m src.cli heuristics severity --ratings data/raw/formbricks/heuristics_severity_ratings.csv --problems data/processed/heuristics/consolidated_problems.csv
python -m src.cli validate-users-time
python -m src.cli all --plot-style both
python main.py generate-slides --strict
```

## Documentazione

- [Mappa progetto](docs/project_map.md): struttura cartelle, entry point, config e output.
- [Pipeline analisi](docs/analysis_pipeline.md): comandi e ordine di esecuzione.
- [Formato dati](docs/data_format.md): CSV attesi e colonne principali.
- [Workflow Formbricks](docs/formbricks_workflow.md): import questionario e survey euristiche.
- [Workflow euristiche](docs/heuristics_workflow.md): survey raw, consolidamento manuale, survey severita.
- [Users time](docs/users_time.md): dataset osservazionale manuale.
- [Generazione slide](docs/slide_generation.md): template PPTX e YAML deck.
- [Stile grafici](docs/visual_style.md): tema e output figure.
- [Troubleshooting](docs/troubleshooting.md): errori comuni.
- [Guida manutenzione docs per AI](docs/ai_documentation_guide.md): template e checklist per aggiornare la documentazione.

## Struttura Essenziale

```txt
config.yaml              configurazione progetto
config/                  mapping import
data/raw/                input normalizzati o CSV manuali
data/formbricks_raw/     export Formbricks questionario
data/templates/          template CSV da compilare
src/                     codice toolkit
slides/                  template e config PPTX
docs/                    documentazione
tests/                   test automatici
outputs/                 artefatti generati, ignorati da git
reports/                 report generati, ignorati da git
```

## Note

Gli output generati non sono versionati. Rigenerali con i comandi sopra. I dark pattern non fanno parte della pipeline automatica: possono essere discussi manualmente nel report o nelle slide.
