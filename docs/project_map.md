# Mappa progetto

Questa pagina descrive la struttura corrente del toolkit e distingue file sorgente, input utente e output generati.

## Entry Point

```txt
main.py
src/cli.py
```

`src/cli.py` e l'entry point principale. `main.py` e solo un wrapper per usare `python main.py ...`.

Comandi principali:

```powershell
python -m src.cli validate
python -m src.cli all --plot-style both
python -m src.cli import-formbricks-heuristics-discovery --input data/formbricks_raw/heuristics_discovery/formbricks_heuristics_discovery_demo_6_experts.csv
python -m src.cli import-formbricks-heuristics-ratings --input data/formbricks_raw/heuristics_ratings/formbricks_heuristics_ratings_demo_6_experts.csv
python -m src.cli generate-slides --auto --overwrite
```

## Configurazione

```txt
config.yaml
config/heuristics_raw_mapping.yml
config/formbricks_questionnaire_mapping.yml
config/formbricks_heuristics_mapping.yml
config/slide_export.yml
```

- `config.yaml`: nomi progetto, sistemi confrontati, path principali, tema grafici e parametri analisi.
- `config/heuristics_raw_mapping.yml`: mapping robusto per l'export Formbricks wide della survey euristica raw.

## Input

```txt
data/raw/
data/formbricks_raw/
data/templates/
data/examples/
```

- `data/raw/users_time.csv`: dataset osservazionale manuale dei test.
- `data/raw/users-time.csv`: dataset legacy ancora supportato dalla pipeline storica.
- `data/formbricks_raw/questionnaire/`: export Formbricks questionario. I CSV reali sono ignorati da git.
- `data/formbricks_raw/heuristics_discovery/`: survey discovery problemi euristici.
- `data/formbricks_raw/heuristics_ratings/`: survey rating dei problemi consolidati.
- `data/templates/`: template da compilare.
- `data/examples/`: esempi leggeri versionabili.

## Codice

```txt
src/
src/adapters/formbricks/
src/slide_export/
src/text_generation/
src/visualization/
```

- `src/cli.py`: CLI centralizzata.
- `src/config.py`: root path, config e directory output.
- `src/data_loading.py`: caricamento CSV normalizzati.
- `src/validation.py`: validazioni input.
- `src/formbricks_adapter.py`: wrapper import Formbricks.
- `src/formbricks_heuristics_pipeline.py`: survey euristica raw, template consolidamento, survey severità.
- `src/user_tests.py`, `src/users_time.py`: analisi user test legacy e osservazionale.
- `src/questionnaire.py`: UEQ, NPS e sottogruppi.
- `src/heuristics.py`: analisi dei file euristici consolidati legacy.
- `src/plots.py`, `src/visualization/theme.py`: grafici e tema.
- `src/slide_export/pptx_generator.py`: generazione PPTX da template.

## Slide

```txt
slides/templates/
slides/config/
slides/assets/
```

- `slides/templates/Deliveroo_vs_Glovo_clean_python_ready_template.pptx`: template attivo per generazione PPTX.
- `slides/config/slide_deck.yml`: deck reale.
- `slides/config/demo_slide_deck.yml`: deck demo.
- `slides/assets/`: asset del template.

## Output Generati

```txt
outputs/
reports/
data/processed/
```

Queste cartelle contengono artefatti rigenerabili e sono ignorate da git, salvo `.gitkeep` dove serve mantenere la struttura.

Output principali:

```txt
outputs/figures/
outputs/tables/
outputs/tables_md/
outputs/text_snippets/
outputs/slide_pack/
outputs/slides/
reports/
data/processed/heuristics/
```

## Documentazione

```txt
README.md
docs/
```

- `README.md`: panoramica breve e indice.
- `docs/manual.md`: istruzioni minime per eseguire il progetto.
- `docs/`: spiegazioni dettagliate per singola area.

## Regole di Pulizia

- Non versionare output generati.
- Non versionare export reali Formbricks.
- Non aggiungere nuovi entry point se non strettamente necessario: estendere `src/cli.py`.
- Se cambia un comando, aggiornare `README.md`, `docs/manual.md`, `docs/cli_api.md` e la pagina docs corrispondente.
- Se cambia un formato CSV, aggiornare `docs/data_format.md` e i test.
