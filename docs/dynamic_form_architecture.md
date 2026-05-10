# Architettura import Formbricks

Il toolkit usa Formbricks per due aree:

- questionari UEQ/NPS;
- valutazione euristica in due survey.

## Questionari

Il questionario usa adapter schema/tag driven:

```txt
src/adapters/formbricks/questionnaire_adapter.py
src/adapters/formbricks/mapping_engine.py
src/schemas/questionnaire_schema.yaml
config.yaml
```

I titoli Formbricks possono contenere tag come:

```txt
[DEMOGRAPHIC] Eta
[UEQ][Deliveroo] Fastidioso/Piacevole
[UEQ][Glovo] Fastidioso/Piacevole
[NPS][Deliveroo] Quanto consiglieresti Deliveroo?
```

Comando:

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/export_questionario.csv
```

## Euristiche

Le euristiche non usano piu un adapter candidato/review automatico. Il flusso attivo e in:

```txt
src/formbricks_heuristics_pipeline.py
config/heuristics_raw_mapping.yml
```

Fase 1:

```powershell
python -m src.cli heuristics raw --input data/raw/formbricks/heuristics_experts_raw.csv
```

Fase manuale:

```txt
data/processed/heuristics/raw_problems_table.csv
data/processed/heuristics/consolidated_problems.csv
```

Fase 2:

```powershell
python -m src.cli heuristics severity --ratings data/raw/formbricks/heuristics_severity_ratings.csv --problems data/processed/heuristics/consolidated_problems.csv
```

## Design

- La normalizzazione e configurabile via YAML.
- La deduplicazione semantica dei problemi resta manuale.
- Gli export reali Formbricks sono ignorati da git.
- Gli output normalizzati sono rigenerabili in `data/processed/`.
