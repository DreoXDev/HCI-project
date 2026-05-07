# Manuale: da Formbricks all'analisi completa

Segui questi step quando arrivi con i file raccolti per l'analisi completa.

## 1. Metti i file al posto giusto

```txt
data/formbricks_raw/questionnaire/export_questionario.csv
data/formbricks_raw/heuristics/export_esperti.csv
data/raw/users_time.csv
```

Nota: questionario ed euristiche vengono importati da Formbricks. Gli user test non sono una survey: vanno compilati manualmente nel formato osservazionale `users_time.csv`.

## 2. Attiva l'ambiente

```powershell
cd "D:\Projects\IUM\Improved Notebooks\HCI-project"
..\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 3. Controlla configurazione e mapping

Apri `config.yaml` e verifica nomi app e path.

Se le colonne del form euristico hanno nomi diversi da quelli attesi, aggiorna `config/formbricks_heuristics_mapping.yml`.

## 4. Prepara o valida users_time

Per generare il template:

```powershell
python -m src.cli create-templates
```

Compila `data/examples/users_time_template.xlsx`, poi salva il file finale come:

```txt
data/raw/users_time.csv
```

Valida:

```powershell
python -m src.cli validate-users-time
```

## 5. Importa il questionario

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/export_questionario.csv
```

## 6. Importa le euristiche come candidati

```powershell
python -m src.cli import-formbricks-heuristics --input data/formbricks_raw/heuristics/export_esperti.csv
```

Controlla:

```txt
reports/heuristics_import_report.md
reports/heuristics_import_errors.csv
```

## 7. Raggruppa manualmente i problemi euristici

Apri:

```txt
data/processed/heuristics_review.csv
```

Modifica solo le colonne di review:

- `problem_group_id`: stesso valore per problemi equivalenti
- `include`: `true` se il problema va tenuto, `false` se va escluso
- `review_notes`: note libere del team

## 8. Genera i file euristici finali

```powershell
python -m src.cli build-heuristics-from-review --input data/processed/heuristics_review.csv --output-dir data/raw
```

## 9. Valida i dati

```powershell
python -m src.cli validate
```

Non andare avanti con errori di validazione.

## 10. Genera analisi, grafici, tabelle e testi

```powershell
python -m src.cli all
```

Se vuoi rigenerare solo gli output del dataset osservazionale:

```powershell
python -m src.cli analyze-users-time
```

## 11. Consegna gli output

Usa:

```txt
outputs/figures/
outputs/tables/
outputs/tables_md/
outputs/text_snippets/
outputs/text/
outputs/generated_report_sections/
outputs/slide_manifest.md
```

## 12. Checklist finale

- `python -m pytest` passa
- `python -m src.cli validate` non mostra errori
- `data/raw/users_time.csv` contiene tutti i task previsti
- `data/raw/questionnaire_deliveroo.csv` e `data/raw/questionnaire_glovo.csv` sono aggiornati
- `data/raw/heuristics_deliveroo.csv` e `data/raw/heuristics_glovo.csv` derivano dal file di review
- `outputs/tables/users_time_summary.md` esiste se `users_time.csv` e presente
- `outputs/slide_manifest.md` esiste
