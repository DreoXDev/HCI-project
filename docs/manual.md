# Manuale operativo

> [!info]
> Guida rapida per generare tutti gli output finali: analisi, grafici, tabelle, testi, slide PPTX e PDF.

## Indice

- [Prerequisiti](#prerequisiti)
- [Step 1 - Inserire i CSV](#step-1---inserire-i-csv)
- [Step 2 - Importare i dati Formbricks](#step-2---importare-i-dati-formbricks)
- [Step 3 - Completare la review euristica](#step-3---completare-la-review-euristica)
- [Step 4 - Lanciare la pipeline completa](#step-4---lanciare-la-pipeline-completa)
- [Step 5 - Controllare gli output](#step-5---controllare-gli-output)

## Prerequisiti

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

> [!warning]
> Per generare anche il PDF installa LibreOffice e verifica che `soffice` sia nel `PATH`.

## Step 1 - Inserire i CSV

| Dato | Cartella |
|---|---|
| Questionario Formbricks | `data/formbricks_raw/questionnaire/users_questionnaire_export.csv` |
| Problemi euristici consolidati | `data/processed/heuristics/clean_problems.csv` |
| Severita euristiche | `data/formbricks_raw/heuristics/severity_ratings_export.csv` |
| Tempi osservazionali | `data/raw/users_time.csv` |

## Step 2 - Importare i dati Formbricks

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/users_questionnaire_export.csv
```

## Step 3 - Rigenerare le euristiche finali

Verificare i 40 problemi consolidati e importare le severita finali:

```powershell
python -m src.cli heuristics validate-clean --problems data/processed/heuristics/clean_problems.csv
python -m src.cli heuristics severity-pipeline --problems data/processed/heuristics/clean_problems.csv --ratings-export data/formbricks_raw/heuristics/severity_ratings_export.csv --out outputs/heuristics --strict
```

## Step 4 - Lanciare la pipeline completa

> [!Example]
> Comando consigliato:
>
> ```powershell
> python -m src.cli full-pipeline --plot-style both --generate-slides --no-export-pdf
> ```

Se LibreOffice non è disponibile:

```powershell
python -m src.cli full-pipeline --plot-style both --generate-slides --no-export-pdf
```

Per pulire solo gli artefatti rigenerabili prima di una consegna:

```powershell
python -m src.cli clean-outputs
```

## Step 5 - Controllare gli output

| Output | Percorso |
|---|---|
| Grafici | `outputs/figures/` |
| Grafici final report | `outputs/assets/final_report/` |
| Tabelle | `outputs/tables/`, `outputs/tables/markdown/` |
| Tabelle final report | `data/processed/final_report/` |
| Snippet utili | `outputs/texts/snippets/` |
| Slide finali per revisione | `outputs/final/final_report.pptx` |
| Quality gate finale | `outputs/final/final_report_quality_gate.md` |
| Changelog finale | `outputs/final/final_report_changelog.md` |
| Slide task partecipanti | `outputs/slides/user_task_deck.pptx` |
| PDF | `outputs/final/final_report.pdf`, `outputs/slides/user_task_deck.pdf` |
| Manifest | `outputs/slide_manifest.md` |

## Checklist finale

- [ ] CSV Formbricks inseriti
- [ ] `users_time.csv` aggiornato
- [ ] Review euristiche completata
- [ ] Pipeline eseguita
- [ ] PPTX finale e deck task generati
- [ ] PDF generato o motivazione documentata
- [ ] `python -m src.cli quality-check` senza errori critici

## Collegamenti

- [Mappa CLI](cli_api.md)
- [Formato dati](data_format.md)
- [Generazione slide](slide_generation.md)
- [Troubleshooting](troubleshooting.md)

# Workflow euristiche: deduplicazione e valutazione severità

## 1. Esporta i problemi grezzi da Formbricks

Scaricare il CSV dalla survey in cui gli esperti inseriscono liberamente i problemi trovati e salvarlo in:

```text
data/formbricks_raw/heuristics/problems_raw_export.csv
```

## 2. Genera o apri la tabella raw dei problemi

```powershell
python -m src.cli heuristics raw --input data/formbricks_raw/heuristics/problems_raw_export.csv
```

Output atteso:

```text
data/processed/heuristics/raw_problems_table.csv
```

## 3. Deduplica manualmente i problemi

Aprire la tabella raw e creare manualmente:

```text
data/processed/heuristics/clean_problems.csv
```

La deduplicazione trasforma più segnalazioni simili in un unico problema canonico.

> [!example]
> Raw: "Il bottone del checkout è poco visibile", "La CTA finale non si nota", "Checkout button difficile da trovare".  
> Clean: `P001,Deliveroo,Checkout,H4,"CTA checkout poco visibile","Il pulsante finale di conferma ordine non risulta abbastanza evidente."`

## 4. Regole per creare `clean_problems.csv`

> [!warning]
> Non modificare mai i `problem_id` dopo aver creato il form di valutazione severità. Gli ID sono il collegamento tra il file clean e le risposte Formbricks.

Regole:

1. Ogni problema deve avere un ID stabile: `P001`, `P002`, `P003`, ...
2. Ogni riga deve rappresentare un solo problema.
3. Problemi equivalenti devono essere uniti.
4. Problemi composti devono essere separati.
5. Problemi fuori scope devono essere eliminati.
6. Il titolo deve essere breve.
7. La descrizione deve essere chiara e neutra.
8. L'euristica deve essere coerente.
9. La schermata deve essere scritta sempre nello stesso modo.
10. L'app deve essere scritta sempre nello stesso modo: `Deliveroo` o `Glovo`.

Colonne obbligatorie: `problem_id`, `app`, `screen`, `heuristic`, `title`, `description`.

## 5. Valida il file clean

```powershell
python -m src.cli heuristics validate-clean --problems data/processed/heuristics/clean_problems.csv
```

Se ci sono errori, correggere il CSV prima di continuare.

## 6. Crea il secondo form Formbricks

Prima domanda obbligatoria:

```text
Qual è il tuo id esperto
```

Poi creare una domanda per ogni problema. Il titolo deve contenere l'ID tra parentesi quadre:

```text
[P001] CTA checkout poco visibile
```

Opzioni consigliate:

```text
0 - Non è un problema
1 - Problema cosmetico
2 - Problema minore
3 - Problema maggiore
4 - Problema critico
```

> [!important]
> Il codice tra parentesi quadre, per esempio `[P001]`, è obbligatorio. Serve al programma per collegare la risposta al problema corretto.

## 7. Esporta le valutazioni da Formbricks

Salvare il CSV in:

```text
data/formbricks_raw/heuristics/severity_ratings_export.csv
```

## 8. Esegui la pipeline finale

```powershell
python -m src.cli heuristics severity-pipeline --problems data/processed/heuristics/clean_problems.csv --ratings-export data/formbricks_raw/heuristics/severity_ratings_export.csv --out outputs/heuristics --strict
```

Output generati:

```text
data/processed/heuristics/problem_ratings_long.csv
data/processed/heuristics/heuristic_final_dataset.csv
data/processed/heuristics/problem_severity_summary.csv
data/processed/heuristics/expert_problem_matrix.csv
outputs/heuristics/charts/
outputs/heuristics/tables/
outputs/heuristics/texts/
```

## 9. Usa gli output per report e slide

Gli output finali possono essere usati direttamente in `reports/`, `slides/` e `outputs/heuristics/`. La parte manuale finisce con `clean_problems.csv` e con la creazione del form di valutazione.
