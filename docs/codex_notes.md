# Note per agenti AI

Queste note servono a chi lavora sul progetto come agente automatico.

## Contesto

- Repo locale: `D:\Projects\IUM\Improved Notebooks\HCI-project`
- Virtualenv: `D:\Projects\IUM\Improved Notebooks\.venv`
- Progetto configurato per Deliveroo vs Glovo in `config.yaml`
- I notebook originali sono in `notebooks/original/`; non usarli come sorgente primaria di logica nuova.

## Regole operative

- Prima di modificare, controlla `git status --short`.
- Non sovrascrivere dati reali in `data/raw/` con esempi, salvo richiesta esplicita.
- Non versionare export reali Formbricks o report generati.
- Mantieni i notebook come wrapper sottili sopra `src/`.
- Preferisci aggiungere test in `tests/` quando modifichi import, normalizzazione o statistiche.
- Usa `python -m pytest` e `python -m src.cli validate` come verifica minima.

## Workflow dati raccomandato

1. Import questionario Formbricks con `import-formbricks-questionnaire`.
2. Import survey euristica raw con `python -m src.cli heuristics raw --input data/raw/formbricks/heuristics_experts_raw.csv`.
3. Review manuale di `data/processed/heuristics/raw_problems_table.csv`.
4. Compilazione di `data/processed/heuristics/consolidated_problems.csv`.
5. Import survey severità con `python -m src.cli heuristics severity --ratings data/raw/formbricks/heuristics_severity_ratings.csv --problems data/processed/heuristics/consolidated_problems.csv`.
6. Validazione e `python -m src.cli all`.

## Scelte di design

- La deduplicazione euristica resta manuale. Non introdurre AI o matching semantico automatico senza richiesta esplicita.
- `users_time.csv` e un dataset osservazionale manuale, non un export Formbricks.
- `config/heuristics_raw_mapping.yml` e il punto di estensione per colonne euristiche Formbricks raw.
- `config.yaml` resta il punto centrale per nomi sistemi, path e parametri di analisi.
- I report in `reports/` e gli output in `outputs/` sono generati.

## Aree da trattare con cautela

- `src/formbricks_heuristics_pipeline.py` contiene il flusso euristiche in due fasi. Non reintrodurre deduplicazione automatica senza richiesta esplicita.
- Esistono modifiche locali possibili nei CSV raw: non ripristinarle senza conferma.
- Se l'export user-test Formbricks cambia formato, aggiungere un adapter dedicato invece di fare parsing fragile nel notebook.
