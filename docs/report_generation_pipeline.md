# Report generation pipeline

Comando quantitativo: `python -m scripts.validate_quantitative_report`.
Il comando genera asset quantitativi in `outputs/tables`, `outputs/charts` e `outputs/validation`.
La pipeline slide esistente resta separata; gli asset generati qui possono essere inseriti nel deck finale.
Comando report esistente: `python -m src.cli full-pipeline --plot-style both --generate-slides`.
