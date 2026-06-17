<p align="center">
  <img src="assets/repo-cover.png" alt="HCI Project Toolkit cover" width="100%">
</p>

# HCI Project Toolkit

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white">
  <img alt="Pandas" src="https://img.shields.io/badge/Pandas-data%20analysis-150458?logo=pandas&logoColor=white">
  <img alt="Matplotlib" src="https://img.shields.io/badge/Matplotlib-visualization-11557C">
  <img alt="PowerPoint" src="https://img.shields.io/badge/PowerPoint-PPTX-B7472A?logo=microsoftpowerpoint&logoColor=white">
  <img alt="Status" src="https://img.shields.io/badge/status-student%20toolkit-2EA44F">
</p>

Toolkit Python per analisi HCI e usability testing: importa dati da Formbricks e CSV osservazionali, genera tabelle, grafici, testi di sintesi e un report finale in PowerPoint.

La repository pubblica contiene solo codice, configurazioni, template grafici e documentazione riutilizzabile. Dati reali, export Formbricks, deck locali e output generati restano sulla macchina di lavoro e sono esclusi dal tracking Git.

## Cosa Fa

- Normalizza questionari UEQ/NPS esportati da Formbricks.
- Gestisce valutazioni euristiche con problemi consolidati e rating di severita.
- Analizza tempi, successo, errori e richieste di aiuto nei test utenti.
- Produce grafici, tabelle CSV/Markdown, testi di report, quality gate e slide PPTX.
- Permette di inserire nel report finale un deck task curato manualmente.

## Quick Start

```powershell
python -m pip install -r requirements.txt
python -m src.cli create-templates
python -m src.cli validate
python -m src.cli full-pipeline --plot-style both --generate-slides --no-export-pdf
```

I dati locali vanno inseriti nei percorsi canonici sotto `data/`. La pipeline scrive gli artefatti in `outputs/` e `reports/`; entrambe le cartelle sono ignorate da Git.

```txt
data/raw/users_time.csv
data/formbricks_raw/questionnaire/users_questionnaire_export.csv
data/processed/heuristics/clean_problems.csv
data/formbricks_raw/heuristics/severity_ratings_export.csv
```

Il report principale pronto per la revisione manuale viene generato in:

```txt
outputs/final/final_report.pptx
```

Quando l'export PDF e abilitato, la copia finale viene salvata in `outputs/final/final_report.pdf`. La cartella `outputs/slides/` contiene invece gli artefatti tecnici prodotti dal generatore.

> [!NOTE]
> L'export PDF richiede LibreOffice installato e accessibile come `soffice` o `libreoffice`.

## Struttura

```txt
src/                  codice pipeline e CLI
config/               mapping Formbricks e configurazioni
slides/               template PowerPoint, asset visuali e testi statici
docs/                 guide operative
notebooks/            notebook didattici
data/                 input locali non versionati
outputs/              output generati non versionati
reports/              report intermedi non versionati
```

## Dati Locali

Questa repo non pubblica dataset del progetto, file personali, output finali o presentazioni generate. Per lavorare su un nuovo progetto:

1. Esegui `python -m src.cli create-templates`.
2. Compila i file generati localmente sotto `data/`.
3. Importa o valida i dati con la CLI.
4. Rigenera asset e slide con `full-pipeline`.

Per pulire gli artefatti rigenerabili:

```powershell
python -m src.cli clean-outputs
```

## Documentazione

- [Manuale operativo](docs/manual.md)
- [Mappa CLI](docs/cli_api.md)
- [Formato dati](docs/data_format.md)
- [Workflow Formbricks](docs/formbricks_workflow.md)
- [Generazione slide](docs/slide_generation.md)
- [Mappa progetto](docs/project_map.md)
- [Stile visuale](docs/visual_style.md)
