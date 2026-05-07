# Architettura import dinamico

Il toolkit separa la logica analitica dalla struttura dei form. Gli export CSV vengono convertiti da adapter configurabili in dataset normalizzati, poi la pipeline esistente continua a lavorare sui CSV in `data/raw/`.

```txt
Formbricks CSV
  -> Adapter layer
  -> Oggetti interni normalizzati
  -> CSV toolkit
  -> Validazione
  -> Analisi
  -> Grafici, tabelle, report
```

## Adapter layer

La nuova struttura vive in:

```txt
src/adapters/formbricks/
```

Moduli principali:

- `models.py`: dataclass interne (`QuestionnaireResponse`, `HeuristicProblem`, `UserTestResult`)
- `normalization.py`: normalizzazione testo, accenti, item UEQ, codici euristici
- `detection.py`: parsing tag e matching colonne
- `mapping_engine.py`: filtro risposte finite, demographics dinamiche, report import
- `questionnaire_adapter.py`: import questionari Formbricks
- `heuristic_adapter.py`: import valutazioni euristiche Formbricks

Il vecchio modulo `src/formbricks_adapter.py` rimane come wrapper compatibile per CLI e import esistenti.

## Schema YAML

Gli schemi si trovano in:

```txt
src/schemas/
```

File disponibili:

- `questionnaire_schema.yaml`
- `heuristic_schema.yaml`
- `user_test_schema.yaml`

Gli schemi definiscono alias, campi opzionali, campi richiesti e item attesi. Se cambiano i testi delle domande, aggiornare gli alias nello schema o usare tag nei titoli del form.

## Tag consigliati nei form

Per rendere i form robusti a ordine, testo e domande aggiunte, usare tag machine-readable nei titoli.

Questionario utenti:

```txt
[DEMOGRAPHIC] Gender
[DEMOGRAPHIC] Age
[DEMOGRAPHIC] Delivery familiarity
[DEMOGRAPHIC] Preferred App

[UEQ][Deliveroo] Fastidioso/Piacevole
[UEQ][Deliveroo] Incomprensibile/Comprensibile

[UEQ][Glovo] Fastidioso/Piacevole
[UEQ][Glovo] Incomprensibile/Comprensibile

[NPS][Deliveroo]
[NPS][Glovo]
```

Form euristico:

```txt
[HEURISTIC] Evaluator ID
[HEURISTIC] Evaluator Type
[HEURISTIC] System
[HEURISTIC] Problem Title
[HEURISTIC] Problem Description
[HEURISTIC] Violated Heuristics
[HEURISTIC] Severity
[HEURISTIC] Notes
```

## Demographics dinamiche

Le domande demografiche non sono piu una lista chiusa. Il toolkit:

- legge campi `[DEMOGRAPHIC]`
- prova a mapparli sugli alias dello schema
- mantiene campi custom come `preferred_app`
- li esclude dagli item UEQ anche se non sono previsti in `config.yaml`
- genera subgroup analysis per i campi demografici disponibili

## Euristiche

Le valutazioni euristiche restano semi-strutturate. Il toolkit normalizza i problemi in `HeuristicProblem`, genera CSV compatibili e crea anche una cartella di review:

```txt
outputs/heuristic_review/
```

Contiene:

- `all_problems.md`
- `grouped_problems.md`
- `possible_duplicates.md`

La deduplicazione resta una decisione umana.

## Comando generico

Per un CSV Formbricks taggato:

```powershell
python -m src.cli import-any-form --input data/formbricks_raw/export.csv
```

Il comando rileva se il form sembra un questionario o una valutazione euristica e usa l'adapter corretto.
