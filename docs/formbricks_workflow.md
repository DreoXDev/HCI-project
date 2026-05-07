# Workflow Formbricks

## 1. Prepara i form

Usa tag nei titoli delle domande quando possibile:

```txt
[DEMOGRAPHIC] Genere
[DEMOGRAPHIC] Eta
[DEMOGRAPHIC] App usata piu spesso
[UEQ][Deliveroo] Fastidioso/Piacevole
[UEQ][Glovo] Fastidioso/Piacevole
[NPS][Deliveroo] Quanto consiglieresti Deliveroo?
[NPS][Glovo] Quanto consiglieresti Glovo?
```

Per il form esperti:

```txt
[HEURISTIC] ID valutatore
[HEURISTIC] Tipo valutatore
[HEURISTIC] App valutata
[HEURISTIC] Titolo problema
[HEURISTIC] Descrizione problema
[HEURISTIC] Euristiche violate
[HEURISTIC] Severita
[HEURISTIC] Note aggiuntive
```

## 2. Scarica i CSV

Da Formbricks esporta i CSV e mettili qui:

```txt
data/formbricks_raw/questionnaire/export_questionario.csv
data/formbricks_raw/heuristics/export_esperti.csv
data/formbricks_raw/user_tests/user_tests.csv
```

## 3. Configura i mapping

Se i tag non sono presenti o i testi sono cambiati, aggiorna:

```txt
config.yaml
src/schemas/questionnaire_schema.yaml
src/schemas/heuristic_schema.yaml
```

## 4. Esegui

```powershell
python -m src.cli full-pipeline
```

## 5. Leggi i warning

Controlla:

```txt
outputs/import_report.md
outputs/slide_manifest.md
```

Se manca NPS, la pipeline continua e salta solo il grafico NPS. Se mancano euristiche consolidate, genera un template da revisionare.
