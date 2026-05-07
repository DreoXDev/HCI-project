# Handbook operativo

Questa guida e il percorso breve per arrivare dagli export Formbricks agli output finali del toolkit HCI.

## Prerequisiti

Lavora dalla root del progetto:

```powershell
cd "D:\Projects\IUM\Improved Notebooks\HCI-project"
..\.venv\Scripts\Activate.ps1
```

Installa o aggiorna le dipendenze se necessario:

```powershell
python -m pip install -r requirements.txt
```

## I tre file di partenza

La pipeline completa usa tre sorgenti:

```txt
data/formbricks_raw/questionnaire/export_questionario.csv
data/formbricks_raw/heuristics/export_esperti.csv
data/raw/users_time.csv
```

I primi due sono export Formbricks importati automaticamente. Il terzo, `users_time.csv`, e una tabella osservazionale manuale descritta in `docs/users_time.md`.

## Step 1 - Configura progetto e mapping

Controlla in `config.yaml`:

```yaml
project:
  system_1: "Deliveroo"
  system_2: "Glovo"
paths:
  questionnaire_raw: "data/formbricks_raw/questionnaire/export_questionario.csv"
  heuristics_raw: "data/formbricks_raw/heuristics/export_esperti.csv"
  users_time: "data/raw/users-time.csv"
users_time:
  input_path: "data/raw/users_time.csv"
```

Se Formbricks esporta intestazioni diverse per il form euristico, aggiorna:

```txt
config/formbricks_heuristics_mapping.yml
```

Per il questionario, preferisci titoli con tag:

```txt
[DEMOGRAPHIC] Genere
[UEQ][Deliveroo] Fastidioso/Piacevole
[UEQ][Glovo] Fastidioso/Piacevole
[NPS][Deliveroo] Quanto consiglieresti Deliveroo?
[NPS][Glovo] Quanto consiglieresti Glovo?
```

## Step 2 - Prepara users_time

```powershell
python -m src.cli create-templates
```

Compila il template `data/examples/users_time_template.xlsx` e salva il CSV finale in:

```txt
data/raw/users_time.csv
```

Poi valida:

```powershell
python -m src.cli validate-users-time
```

## Step 3 - Importa il questionario Formbricks

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/export_questionario.csv
```

Output:

```txt
data/raw/questionnaire_deliveroo.csv
data/raw/questionnaire_glovo.csv
data/processed/questionnaire_long.csv
outputs/import_report.md
```

## Step 4 - Importa le euristiche Formbricks

```powershell
python -m src.cli import-formbricks-heuristics --input data/formbricks_raw/heuristics/export_esperti.csv
```

Output:

```txt
data/processed/heuristics_candidates.csv
data/processed/heuristics_review.csv
reports/heuristics_import_report.md
reports/heuristics_import_errors.csv
```

Apri `reports/heuristics_import_report.md` e correggi eventuali errori segnalati prima di procedere.

## Step 5 - Revisiona manualmente i gruppi euristici

Apri:

```txt
data/processed/heuristics_review.csv
```

Compila `problem_group_id` con questa regola:

- problemi diversi: gruppi diversi, per esempio `PG001`, `PG002`
- problemi simili o duplicati: stesso gruppo, per esempio due righe entrambe `PG001`

Non serve usare AI in questa fase. La scelta del gruppo e una decisione metodologica del team.

## Step 6 - Genera i CSV euristici finali

```powershell
python -m src.cli build-heuristics-from-review --input data/processed/heuristics_review.csv --output-dir data/raw
```

Output:

```txt
data/raw/heuristics_deliveroo.csv
data/raw/heuristics_glovo.csv
reports/heuristics_build_report.md
```

## Step 7 - Verifica tutti i dati

```powershell
python -m src.cli validate
```

Se compaiono errori, correggi i CSV sorgente o i mapping e ripeti gli step precedenti.

## Step 8 - Esegui analisi e output finali

```powershell
python -m src.cli all
```

Output principali:

```txt
outputs/figures/
outputs/tables/
outputs/tables_md/
outputs/text_snippets/
outputs/generated_report_sections/
outputs/slide_manifest.md
```

## Step 9 - Controllo finale

Prima di consegnare:

```powershell
python -m pytest
python -m src.cli validate
```

Controlla almeno:

- `outputs/tables_md/problems_priority_table.md`
- `outputs/tables_md/heuristics_summary.md`
- `outputs/tables_md/ueq_summary.md`
- `outputs/tables/users_time_summary.md`
- `outputs/slide_manifest.md`

## Comandi utili

Flusso legacy con CSV gia pronti in `data/raw/`:

```powershell
python -m src.cli all
```

Import automatico dei file configurati:

```powershell
python -m src.cli import-formbricks
```

Import con rilevamento del tipo form:

```powershell
python -m src.cli import-any-form --input data/formbricks_raw/questionnaire/export_questionario.csv
```

Rigenerare solo testi e asset slide:

```powershell
python -m src.cli export-text
python -m src.cli export-slide-assets
```
