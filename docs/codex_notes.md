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
2. Import euristiche Formbricks con `import-formbricks-heuristics`.
3. Review manuale di `data/processed/heuristics_review.csv`.
4. Build finale con `build-heuristics-from-review`.
5. Validazione e `python -m src.cli all`.

## Scelte di design

- La deduplicazione euristica resta manuale. Non introdurre AI o matching semantico automatico senza richiesta esplicita.
- `users_time.csv` e un dataset osservazionale manuale, non un export Formbricks.
- `config/formbricks_heuristics_mapping.yml` e il punto di estensione per colonne euristiche Formbricks.
- `config.yaml` resta il punto centrale per nomi sistemi, path e parametri di analisi.
- I report in `reports/` e gli output in `outputs/` sono generati.

## Aree da trattare con cautela

- `src/adapters/formbricks/heuristic_adapter.py` contiene il vecchio flusso di consolidamento. Il flusso consigliato e ora `src/formbricks_heuristics_pipeline.py`.
- Esistono modifiche locali possibili nei CSV raw: non ripristinarle senza conferma.
- Se l'export user-test Formbricks cambia formato, aggiungere un adapter dedicato invece di fare parsing fragile nel notebook.
