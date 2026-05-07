# Handbook operativo - Pipeline Formbricks -> output HCI

Questa guida spiega il flusso piu semplice per usare il toolkit partendo dai CSV scaricati da Formbricks.

## 1. Dove mettere i CSV scaricati

Salva gli export originali senza modificarli manualmente:

```txt
data/formbricks_raw/questionnaire/export_questionario.csv
data/formbricks_raw/heuristics/export_esperti.csv
data/formbricks_raw/user_tests/user_tests.csv
```

Il questionario e il file euristiche sono quelli principali. Il file user test puo anche essere gestito manualmente tramite:

```txt
data/raw/users-time.csv
```

## 2. Come nominare le domande Formbricks

Usa tag nei titoli per rendere il parser robusto:

```txt
[DEMOGRAPHIC] Genere
[DEMOGRAPHIC] Eta
[DEMOGRAPHIC] Professione
[DEMOGRAPHIC] Familiarita delivery
[DEMOGRAPHIC] App usata piu spesso

[UEQ][Deliveroo] Fastidioso/Piacevole
[UEQ][Deliveroo] Incomprensibile/Comprensibile
[UEQ][Glovo] Fastidioso/Piacevole
[UEQ][Glovo] Incomprensibile/Comprensibile

[NPS][Deliveroo] Quanto consiglieresti Deliveroo?
[NPS][Glovo] Quanto consiglieresti Glovo?
```

Per le euristiche:

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

## 3. Cosa modificare se cambiano le domande

Prima scelta: mantenere i tag nei titoli. In quel caso puoi cambiare quasi tutto il testo umano senza rompere l'import.

Se non puoi usare tag o se Formbricks esporta nomi diversi, aggiorna:

```txt
config.yaml
src/schemas/questionnaire_schema.yaml
src/schemas/heuristic_schema.yaml
```

In `config.yaml` controlla soprattutto:

```yaml
paths:
  questionnaire_raw: "data/formbricks_raw/questionnaire/export_questionario.csv"
  heuristics_raw: "data/formbricks_raw/heuristics/export_esperti.csv"

project:
  system_1: "Deliveroo"
  system_2: "Glovo"
```

Negli schema YAML aggiungi alias per le nuove domande demografiche o per campi euristici rinominati.

## 4. Comando principale

Da dentro la root della repo:

```powershell
python -m src.cli full-pipeline
```

Il comando esegue:

1. import CSV Formbricks disponibili
2. conversione nei CSV del toolkit
3. validazione
4. analisi
5. grafici
6. tabelle
7. testi per report
8. asset slide
9. manifest finale

## 5. Output principali

Dopo la pipeline apri:

```txt
outputs/slide_manifest.md
```

Questo file dice cosa usare nelle slide.

Cartelle utili:

```txt
outputs/figures/
outputs/tables/
outputs/tables_md/
outputs/text_snippets/
outputs/generated_report_sections/
outputs/slide_assets/
```

## 6. Risultati che ottieni

User test:

- efficacia per task
- intervalli di confidenza
- efficienza media
- boxplot tempi
- violin plot tempi

Euristiche:

- distribuzione euristiche violate
- euristiche per categoria
- tabella problemi prioritari
- file di consolidamento se i dati arrivano da Formbricks

Questionario:

- sintesi UEQ
- NPS se presente
- subgroup analysis per demographics disponibili

Report/slide:

- testi markdown pronti in `outputs/text_snippets/`
- sezioni report in `outputs/generated_report_sections/`
- asset slide in `outputs/slide_assets/`
- manifest in `outputs/slide_manifest.md`

## 7. Consolidamento euristiche

Se importi euristiche da Formbricks, controlla:

```txt
data/processed/heuristics_consolidation_template.csv
outputs/heuristic_review/all_problems.md
```

Il gruppo deve revisionare manualmente i problemi simili. Dopo la revisione:

```powershell
python -m src.cli build-heuristics-from-consolidation
python -m src.cli analyze-heuristics
python -m src.cli export-text
python -m src.cli export-slide-assets
```

## 8. Comandi utili

Flusso legacy con CSV gia puliti:

```powershell
python -m src.cli all
```

Solo import Formbricks:

```powershell
python -m src.cli import-formbricks
```

Import di un singolo file:

```powershell
python -m src.cli import-any-form --input data/formbricks_raw/questionnaire/export_questionario.csv
```

Solo testi:

```powershell
python -m src.cli export-text
```

Solo slide assets:

```powershell
python -m src.cli export-slide-assets
```

## 9. Warning comuni

Se manca NPS, la pipeline continua e salta il grafico NPS.

Se manca il CSV questionario Formbricks, la pipeline usa i CSV gia presenti in `data/raw/`.

Se le colonne non vengono riconosciute, aggiungi tag nei form o alias negli schema YAML.

Se mancano euristiche consolidate, compila il template in `data/processed/`.
