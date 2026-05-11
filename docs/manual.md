# Manuale operativo

> [!Info]
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

> [!Warning]
> Per generare anche il PDF installa LibreOffice e verifica che `soffice` sia nel `PATH`.

## Step 1 - Inserire i CSV

| Dato | Cartella |
|---|---|
| Questionario Formbricks | `data/formbricks_raw/questionnaire/` |
| Euristiche discovery | `data/formbricks_raw/heuristics_discovery/` |
| Euristiche ratings | `data/formbricks_raw/heuristics_ratings/` |
| Tempi osservazionali | `data/raw/users_time.csv` |

> [!Info]
> I dati demo inclusi sono inventati: 12 utenti e 6 esperti, con split 3 ED e 3 EU.

## Step 2 - Importare i dati Formbricks

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/formbricks_questionnaire_demo_12_users.csv
python -m src.cli import-formbricks-heuristics-discovery --input data/formbricks_raw/heuristics_discovery/formbricks_heuristics_discovery_demo_6_experts.csv
```

## Step 3 - Completare la review euristica

- [ ] Aprire `data/processed/heuristics_review.csv`
- [ ] Compilare `problem_group_id`
- [ ] Preparare o verificare il file problemi consolidati
- [ ] Importare i ratings

```powershell
python -m src.cli import-formbricks-heuristics-ratings --input data/formbricks_raw/heuristics_ratings/formbricks_heuristics_ratings_demo_6_experts.csv --output data/templates/heuristics_consolidated_problems_demo.csv
```

## Step 4 - Lanciare la pipeline completa

> [!Example]
> Comando consigliato:
>
> ```powershell
> python -m src.cli full-pipeline --plot-style both --export-pdf
> ```

Se LibreOffice non è disponibile:

```powershell
python -m src.cli full-pipeline --plot-style both --generate-slides --no-export-pdf
```

## Step 5 - Controllare gli output

| Output | Percorso |
|---|---|
| Grafici | `outputs/figures/` |
| Tabelle | `outputs/tables/`, `outputs/tables_md/` |
| Snippet utili | `outputs/text_snippets/` |
| Slide | `outputs/slides/final_report.pptx` |
| PDF | `outputs/slides/final_report.pdf` |
| Manifest | `outputs/slide_manifest.md` |

## Checklist finale

- [ ] CSV Formbricks inseriti
- [ ] `users_time.csv` aggiornato
- [ ] Review euristiche completata
- [ ] Pipeline eseguita
- [ ] PPTX generato
- [ ] PDF generato o motivazione documentata
- [ ] `python -m src.cli quality-check` senza errori critici

## Collegamenti

- [Mappa CLI](cli_api.md)
- [Formato dati](data_format.md)
- [Generazione slide](slide_generation.md)
- [Troubleshooting](troubleshooting.md)

