# Manuale operativo HCI-project

## 1. Setup

```powershell
cd "D:\Projects\IUM\Improved Notebooks\HCI-project"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 2. Dove mettere i CSV

- Questionario Formbricks: `data/formbricks_raw/questionnaire/`
- Euristiche discovery Formbricks: `data/formbricks_raw/heuristics_discovery/`
- Euristiche ratings Formbricks: `data/formbricks_raw/heuristics_ratings/`
- Tempi osservazionali: `data/raw/users_time.csv`

I file demo inventati sono gia presenti in `data/formbricks_raw/` e `data/examples/`.

## 3. Pipeline completa

```powershell
python -m src.cli full-pipeline --plot-style both
```

Per generare anche il PPTX:

```powershell
python -m src.cli full-pipeline --plot-style both --generate-slides
```

## 4. Review manuale euristiche

1. Importa la discovery:

```powershell
python -m src.cli import-formbricks-heuristics-discovery --input data/formbricks_raw/heuristics_discovery/formbricks_heuristics_discovery_demo_6_experts.csv
```

2. Apri `data/processed/heuristics_review.csv`.
3. Compila `problem_group_id` raggruppando problemi uguali o molto simili.
4. Usa il file review per preparare la survey ratings.
5. Importa i ratings:

```powershell
python -m src.cli import-formbricks-heuristics-ratings --input data/formbricks_raw/heuristics_ratings/formbricks_heuristics_ratings_demo_6_experts.csv --output data/templates/heuristics_consolidated_problems_demo.csv
```

## 5. Generazione slide

```powershell
python -m src.cli validate-slide-template
python -m src.cli generate-slides --auto --overwrite
```

## 6. Dove trovare gli output

- Grafici: `outputs/figures/`
- Tabelle: `outputs/tables/` e `outputs/tables_md/`
- Testi: `outputs/text/`, `outputs/text_snippets/`, `outputs/generated_report_sections/`
- Slide: `outputs/slides/`
- Report: `outputs/reports/`
- Manifest slide: `outputs/slide_manifest.md`

## 7. Problemi comuni

Vedi `docs/troubleshooting.md`.
