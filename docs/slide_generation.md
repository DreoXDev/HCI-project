# Generazione slide

> [!Info]
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

Per esportare anche il PDF:

```powershell
python -m src.cli full-pipeline --plot-style both --export-pdf
```

> [!Warning]
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

## Tabelle paginate

```yaml
table:
  placeholder: TABLE_MAIN
  source: outputs/tables/heuristics_problems_slide.csv
  max_rows: 6
  paginate: true
  title_prefix: "Problemi rilevati"
```

> [!Info]
> Le tabelle destinate alle slide usano label italiane e colonne sintetiche. I CSV tecnici restano disponibili in `outputs/tables/`.

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

