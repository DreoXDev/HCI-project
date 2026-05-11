# CLI API

Questa mappa e allineata ai comandi esposti da `python -m src.cli --help`.

## `python -m src.cli validate`

### Scopo
Valida users time, euristiche e questionari normalizzati in `data/raw/`.

### Input
`config.yaml` e CSV normalizzati.

### Output
Messaggi OK/WARNING/ERROR su terminale.

### Opzioni principali
`--config`.

### Esempio
```powershell
python -m src.cli validate
```

## `python -m src.cli create-templates`

### Scopo
Crea template CSV compilabili.

### Input
Nessuno obbligatorio.

### Output
File in `data/templates/`.

### Opzioni principali
`--overwrite`.

### Esempio
```powershell
python -m src.cli create-templates --overwrite
```

## `python -m src.cli import-formbricks-questionnaire`

### Scopo
Converte un export Formbricks questionario nei CSV Deliveroo/Glovo.

### Input
CSV Formbricks via `--input`.

### Output
`data/raw/questionnaire_deliveroo.csv` e `data/raw/questionnaire_glovo.csv`.

### Opzioni principali
`--input`, `--include-unfinished`.

### Esempio
```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/formbricks_questionnaire_demo_12_users.csv
```

## `python -m src.cli import-formbricks-heuristics-discovery`

### Scopo
Importa la survey Formbricks di discovery problemi euristici.

### Input
CSV discovery in `data/formbricks_raw/heuristics_discovery/`.

### Output
`data/processed/heuristics_candidates.csv`, `data/processed/heuristics_review.csv` e file tecnici in `data/processed/heuristics/`.

### Opzioni principali
`--input`, `--mapping`.

### Esempio
```powershell
python -m src.cli import-formbricks-heuristics-discovery --input data/formbricks_raw/heuristics_discovery/formbricks_heuristics_discovery_demo_6_experts.csv
```

## `python -m src.cli build-heuristics-review`

### Scopo
Controlla che il file di review manuale sia presente e abbia `problem_group_id`.

### Input
`data/processed/heuristics_review.csv` o path passato con `--input`.

### Output
Conferma terminale.

### Opzioni principali
`--input`.

### Esempio
```powershell
python -m src.cli build-heuristics-review
```

## `python -m src.cli import-formbricks-heuristics-ratings`

### Scopo
Importa i ratings di severita sui problemi consolidati.

### Input
CSV ratings via `--input`; problemi consolidati via `--output` se diverso dal demo incluso.

### Output
`data/processed/heuristics/final_problem_summary.csv` e report euristiche.

### Opzioni principali
`--input`, `--output`.

### Esempio
```powershell
python -m src.cli import-formbricks-heuristics-ratings --input data/formbricks_raw/heuristics_ratings/formbricks_heuristics_ratings_demo_6_experts.csv --output data/templates/heuristics_consolidated_problems_demo.csv
```

## `python -m src.cli all`

### Scopo
Valida, analizza e genera tabelle/grafici/testi/asset principali.

### Input
CSV normalizzati in `data/raw/`.

### Output
Artefatti in `outputs/`.

### Opzioni principali
`--plot-style`.

### Esempio
```powershell
python -m src.cli all --plot-style both
```

## `python -m src.cli full-pipeline`

### Scopo
Esegue import disponibili, validazione, analisi, asset, testi, slide pack e quality check.

### Input
Config e CSV nelle cartelle standard.

### Output
`outputs/figures/`, `outputs/tables/`, `outputs/text*`, `outputs/slide_pack/`, `outputs/reports/`.

### Opzioni principali
`--plot-style`, `--generate-slides`, `--overwrite`, `--timestamp`, `--include-unfinished`.

### Esempio
```powershell
python -m src.cli full-pipeline --plot-style both --generate-slides
```

## `python -m src.cli generate-slides`

### Scopo
Genera il PPTX finale dal template e dagli asset gia prodotti.

### Input
`slides/config/slide_deck.yml`, template PPTX, asset in `outputs/`.

### Output
PPTX in `outputs/slides/` e report di generazione.

### Opzioni principali
`--auto`, `--strict`, `--template`, `--output`, `--overwrite`, `--timestamp`.

### Esempio
```powershell
python -m src.cli generate-slides --auto --overwrite
```

## Altri comandi disponibili

`validate-users-time`, `analyze`, `generate-report`, `generate-demo-assets`, `validate-slide-template`, `import-formbricks`, `import-formbricks-all`, `all-from-formbricks`, `import-any-form`, `export-text`, `export-slide-assets`, `export-tables`, `export-figures`, `analyze-user-tests`, `analyze-users-time`, `analyze-heuristics`, `analyze-questionnaire`, `build-slide-pack`, `quality-check`, `analyze-benchmark`, `build-asset-manifest`.

Per ciascuno:

```powershell
python -m src.cli <command> --help
```

Nota: la CLI usa un parser globale, quindi molti comandi condividono le stesse opzioni.
