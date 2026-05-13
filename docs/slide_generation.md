# Generazione slide

> [!info]
> Questa pagina descrive come produrre la presentazione PPTX e il PDF finale.

## Input

| Risorsa | Percorso |
|---|---|
| Template PPTX | `slides/templates/Deliveroo_vs_Glovo_clean_python_ready_template.pptx` |
| Config deck | `slides/config/slide_deck.yml` |
| Testi statici | `slides/content/reference_static_texts.md` |
| Asset generati | `outputs/figures/`, `outputs/tables/`, `outputs/text_snippets/` |

## Comandi

```powershell
python -m src.cli validate-slide-template
python -m src.cli validate-slide-assets
python -m src.cli generate-slides --auto --overwrite
```

Per generare la presentazione separata da mostrare ai partecipanti durante i task:

```powershell
python -m src.cli generate-slides --config slides/config/user_task_deck.yml --overwrite
```

Il file prodotto è `outputs/slides/user_task_deck.pptx`. I testi delle task e il placeholder del link survey sono in `slides/content/reference_static_texts.md`.

Per esportare anche il PDF:

```powershell
python -m src.cli full-pipeline --plot-style both --export-pdf
```

> [!warning]
> L'export PDF richiede LibreOffice. Su Windows installa LibreOffice e aggiungi `soffice.exe` al `PATH`.

## Uso degli snippet testuali nelle slide

| Snippet | Slide/Output | Uso |
|---|---|---|
| `intro_summary.md` | Introduzione | Contesto sintetico |
| `heuristic_conclusions.md` | Valutazione euristica | Insight principali |
| `user_test_effectiveness_conclusions.md` | User test | Sintesi efficacia |
| `user_test_efficiency_conclusions.md` | User test | Sintesi tempi |
| `questionnaire_conclusions.md` | Questionario | Interpretazione UEQ |
| `nps_conclusions.md` | Questionario | Interpretazione NPS |
| `final_comparative_conclusions.md` | Conclusioni | Executive summary |

## Cosa resta manuale

Il confronto con il PDF guida e tracciato in [`manual_slides.md`](../manual_slides.md). In breve:

- grafici, tabelle, matrici, testi statici e slide placeholder sono generati dalla pipeline;
- screenshot reali, allegati amministrativi, appendici individuali complete e conclusioni finali validate dal gruppo restano manuali;
- se un contenuto manuale diventa strutturato in CSV o immagine, può essere collegato a `slides/config/slide_deck.yml` o alla modalità `reference_order`.

## Tabelle paginate

```yaml
table:
  placeholder: TABLE_MAIN
  source: outputs/tables/heuristics_problems_slide.csv
  max_rows: 6
  paginate: true
  title_prefix: "Problemi rilevati"
```

> [!info]
> Le tabelle destinate alle slide usano label italiane e colonne sintetiche. I CSV tecnici restano disponibili in `outputs/tables/`.

## Asset euristiche deduplicate

La generazione slide non ricalcola l'analisi: legge gli asset già prodotti dalla pipeline euristica finale.

```powershell
python -m src.cli heuristics severity-pipeline --problems data/processed/heuristics/clean_problems.csv --ratings-export data/formbricks_raw/heuristics/severity_ratings_export.csv --out outputs/heuristics --strict
```

Asset disponibili:

```text
outputs/heuristics/heuristics_top_problems.png
outputs/heuristics/heuristics_problem_expert_heatmap.png
outputs/heuristics/heuristics_by_app.png
outputs/heuristics/heuristics_by_heuristic.png
outputs/heuristics/heuristics_critical_problems_table.csv
outputs/heuristics/heuristics_summary.md
outputs/heuristics/heuristics_top_findings.md
```

## Template PowerPoint

- Mantieni i marker `TEMPLATE_ID`.
- Mantieni i placeholder principali o aggiorna `slides/config/slide_deck.yml`.
- Usa font con supporto ai caratteri italiani accentati.
- Esegui `validate-slide-template` dopo ogni modifica manuale.

## Troubleshooting PDF

| Problema | Soluzione |
|---|---|
| `LibreOffice non trovato` | Installa LibreOffice e verifica `soffice --version` |
| PDF non prodotto | Controlla che il PPTX esista e che `outputs/slides/` sia scrivibile |
| Layout PDF diverso | Apri il PPTX in LibreOffice e verifica font/template |
