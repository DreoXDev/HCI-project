# Template PowerPoint: stato e checklist

Template attivo:

```txt
slides/templates/Deliveroo_vs_Glovo_clean_python_ready_template.pptx
```

Questo file e la versione graficamente pulita del template originale, con metadata Python aggiunti fuori canvas. Non usare piu `Deliveroo_vs_Glovo_python_ready_template.pptx`.

## Stato attuale

Il template contiene 25 slide template: una cover, una comparison neutral, final verdict, sources, piu varianti `neutral`, `deliveroo`, `glovo` per i layout principali.

```txt
cover
section_divider_neutral
section_divider_deliveroo
section_divider_glovo
graph_full_neutral
graph_full_deliveroo
graph_full_glovo
comparison_neutral
table_large_neutral
table_large_deliveroo
table_large_glovo
findings_neutral
findings_deliveroo
findings_glovo
task_results_neutral
task_results_deliveroo
task_results_glovo
ueq_question_neutral
ueq_question_deliveroo
ueq_question_glovo
final_verdict
sources
text_only_neutral
text_only_deliveroo
text_only_glovo
```

Le ultime modifiche richieste sono state applicate o riparate localmente:

- `INSIGHT_TEXT` presente in `graph_full`;
- `SUMMARY_TEXT` presente in `comparison`;
- `SUMMARY_TEXT` presente in `findings`;
- `TABLE_MAIN` allargata;
- `text_only` aggiunta con `TEXT_TITLE` e `TEXT_BODY`.
- `TEMPLATE_ID` aggiunti fuori canvas per tutte le slide template;
- nomi shape semantici ripristinati per grafici, testi, tabelle e immagini.
- `comparison_neutral` riparata localmente: `LEFT_GRAPH`, `RIGHT_GRAPH`, `COMPARISON_TITLE` e `SUMMARY_TEXT` puntano ora agli slot visivi corretti.

## Regole da mantenere se il template viene modificato ancora

- Non aggiungere overlay, box tratteggiati o etichette tecniche visibili.
- Ogni slide template deve avere un solo `TEMPLATE_ID:<id>` fuori canvas.
- I `TEMPLATE_ID` non devono essere visibili in slideshow.
- Le shape sostituibili devono mantenere nomi stabili nel Selection Pane.
- I testi visibili devono restare chiari su sfondo scuro.
- Se si aggiunge una nuova variante, aggiornare anche `src/slide_export/template_variants.py`.

## Shape richieste per layout

`cover`:

```txt
PROJECT_TITLE
PROJECT_SUBTITLE
AUTHORS_DATE
```

`section_divider`:

```txt
SECTION_NAME
```

`graph_full`:

```txt
GRAPH_TITLE
INSIGHT_TEXT
GRAPH_MAIN
```

`comparison`:

```txt
COMPARISON_TITLE
SUMMARY_TEXT
LEFT_GRAPH
RIGHT_GRAPH
```

`table_large`:

```txt
TABLE_TITLE
TABLE_MAIN
TABLE_FOOTNOTE
```

`findings`:

```txt
FINDINGS_TITLE
SUMMARY_TEXT
FINDING_1
FINDING_2
FINDING_3
FINDING_4
MINI_GRAPH
```

`task_results`:

```txt
TASK_TITLE
TASK_DESCRIPTION
TASK_SCREENSHOT
SUCCESS_RATE_VALUE
AVG_TIME_VALUE
```

`ueq_question`:

```txt
QUESTION_TITLE
BOXPLOT
MEAN_VALUE
STD_VALUE
MIN_VALUE
MAX_VALUE
```

`final_verdict`:

```txt
FINAL_TITLE
DELIVEROO_STRENGTH_1
DELIVEROO_STRENGTH_2
DELIVEROO_WEAKNESS
GLOVO_STRENGTH_1
GLOVO_STRENGTH_2
GLOVO_WEAKNESS
SUMMARY_GRAPH
WINNER_LABEL
```

`sources`:

```txt
SOURCES_TITLE
SOURCES_LIST
```

Nota: al momento il generatore usa `text_only` per le fonti, per evitare il layout legacy con foto + source singola. `sources` resta utile solo come fallback o se in futuro verra ridisegnato come pagina fonti vera.

`text_only`:

```txt
TEXT_TITLE
TEXT_BODY
```

## Smoke test

Dopo ogni modifica al template:

```powershell
python main.py generate-slides --output outputs/slides/template_smoke.pptx --overwrite
python -m pytest tests
```

Controlli attesi:

- deck generato senza errori;
- `Missing optional assets: 0`;
- nessun placeholder residuo in stile `[PLACEHOLDER]`;
- tutti i PNG dark disponibili sono usati nel deck espanso;
- le slide task e UEQ vengono duplicate per app quando i dati contengono Deliveroo/Glovo;
- revisione visiva rapida delle prime slide, delle tabelle e di alcune slide `text_only`.
