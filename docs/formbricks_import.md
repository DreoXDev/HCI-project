# Import Formbricks

I CSV esportati da Formbricks non vanno modificati manualmente. Salvarli in `data/formbricks_raw/` e usare l'adapter del toolkit per convertirli nel formato atteso dalla pipeline.

## Questionario utenti

Input predefinito:

```txt
data/formbricks_raw/questionnaire_export.csv
```

Comando:

```powershell
python -m src.cli import-formbricks-questionnaire
```

Con input esplicito:

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire_export_2026_05_07.csv
```

Output:

```txt
data/raw/questionnaire_deliveroo.csv
data/raw/questionnaire_glovo.csv
data/processed/questionnaire_formbricks_clean.csv
outputs/import_report.md
```

Di default vengono usate solo le risposte con `Finished = Yes`. Per includere anche risposte incomplete:

```powershell
python -m src.cli import-formbricks-questionnaire --include-unfinished
```

## Valutazione euristica

Input predefinito:

```txt
data/formbricks_raw/heuristic_export.csv
```

Comando:

```powershell
python -m src.cli import-formbricks-heuristics
```

Output:

```txt
data/raw/heuristics_deliveroo.csv
data/raw/heuristics_glovo.csv
data/processed/heuristics_formbricks_clean.csv
outputs/import_report.md
```

Il form euristico deve contenere almeno:

- ID valutatore
- App valutata
- Codice problema
- Descrizione breve
- Euristiche violate
- Severita

## Workflow completo

```powershell
python -m src.cli import-formbricks-all
python -m src.cli validate
python -m src.cli all
```

Oppure:

```powershell
python -m src.cli all-from-formbricks
```

`all-from-formbricks` importa, valida, analizza e rigenera tutti gli output.

Per un singolo CSV taggato, si puo usare anche:

```powershell
python -m src.cli import-any-form --input data/formbricks_raw/export.csv
```

Il comando rileva se l'export sembra un questionario o una valutazione euristica.

## Tag consigliati

Per evitare dipendenze da ordine e testo delle domande, usare tag nei titoli Formbricks:

```txt
[DEMOGRAPHIC] Age
[UEQ][Deliveroo] Fastidioso/Piacevole
[UEQ][Glovo] Fastidioso/Piacevole
[NPS][Deliveroo]
[NPS][Glovo]
[HEURISTIC] Severity
```

## Configurazione

I mapping delle colonne Formbricks sono in `config.yaml`, sezione `formbricks`. Se nel form finale cambiano i testi delle domande, aggiornare quei mapping invece di modificare il CSV esportato.

Gli schemi estendibili sono in `src/schemas/`.
