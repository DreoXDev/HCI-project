# Pipeline di analisi

## Comandi principali

Attivare il virtualenv creato nella cartella superiore:

```powershell
..\.venv\Scripts\Activate.ps1
```

Eseguire tutto:

```powershell
python -m src.cli all
```

Solo validazione:

```powershell
python -m src.cli validate
```

Creare template CSV:

```powershell
python -m src.cli create-templates
```

Importare dati da Formbricks:

```powershell
python -m src.cli import-formbricks-questionnaire
python -m src.cli import-formbricks-heuristics
python -m src.cli import-formbricks-all
python -m src.cli all-from-formbricks
```

## Output

La pipeline salva:

- grafici in `outputs/figures/`
- tabelle CSV in `outputs/tables/`
- tabelle Markdown in `outputs/tables_md/`
- frasi pronte per il report in `outputs/text_snippets/`
- report di import Formbricks in `outputs/import_report.md`

## Note di refactor

I notebook originali sono stati conservati in `notebooks/original/`. I nuovi notebook devono restare interfacce leggere e chiamare la logica in `src/`.
