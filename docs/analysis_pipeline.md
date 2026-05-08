# Pipeline di analisi

## Comandi principali

Attivare il virtualenv dalla root della repo:

```powershell
..\.venv\Scripts\Activate.ps1
```

Validare i CSV in `data/raw/`:

```powershell
python -m src.cli validate
```

Eseguire analisi, grafici, tabelle e testi:

```powershell
python -m src.cli all --plot-style both
```

Creare template:

```powershell
python -m src.cli create-templates
```

## Pipeline da Formbricks

```powershell
python -m src.cli validate-users-time
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/export_questionario.csv
python -m src.cli import-formbricks-heuristics --input data/formbricks_raw/heuristics/export_esperti.csv
# review manuale di data/processed/heuristics_review.csv
python -m src.cli build-heuristics-from-review --input data/processed/heuristics_review.csv --output-dir data/raw
python -m src.cli validate
python -m src.cli all --plot-style both
python -m src.cli build-slide-pack
python -m src.cli quality-check
```

Per una pipeline piu automatica, quando le euristiche sono gia consolidate:

```powershell
python -m src.cli full-pipeline --plot-style both
```

## Output

- `outputs/figures/`: grafici PNG/SVG
- `outputs/tables/`: tabelle CSV
- `outputs/tables_md/`: tabelle Markdown
- `outputs/text_snippets/`: frasi pronte per report
- `outputs/text/`: testi deterministici dedicati, incluso `users_time_interpretation.md`
- `outputs/reports/`: report di validazione
- `outputs/generated_report_sections/`: sezioni report
- `outputs/slide_manifest.md`: indice operativo per le slide
- `outputs/slide_pack/`: markdown finale per slide, executive summary e manifest CSV degli asset

## Comandi extra per slide finali

```powershell
python -m src.cli analyze-dark-patterns
python -m src.cli analyze-benchmark
python -m src.cli build-asset-manifest
python -m src.cli build-slide-pack
python -m src.cli quality-check
```

`analyze-dark-patterns` crea e legge `data/raw/dark_patterns.csv`: la scoperta resta manuale, la pipeline esporta solo la tabella e il testo. `analyze-benchmark` usa `data/raw/ueq_benchmark.csv` se presente; se manca, emette un warning non bloccante.

## Nota di architettura

I notebook nuovi devono restare interfacce leggere. La logica va nei moduli in `src/` e deve essere coperta da test quando cambia comportamento.
