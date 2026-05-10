# Generazione slide

Il generatore PowerPoint assembla un deck finale partendo da:

- template PPTX con marker `TEMPLATE_ID`;
- grafici PNG gia esportati;
- tabelle CSV;
- testi Markdown;
- configurazione YAML del deck.

Il layer slide non ricalcola analisi o statistiche quando viene usato in modalita strict: consuma gli asset gia prodotti dalla pipeline.

## Comandi principali

Generare asset report e slide pack:

```powershell
python main.py generate-report
```

Generare solo il PowerPoint usando asset gia presenti:

```powershell
python main.py generate-slides --strict
```

Generare prima gli asset mancanti e poi il PowerPoint:

```powershell
python main.py generate-slides --auto
```

Eseguire tutta la pipeline e poi creare il PPTX:

```powershell
python main.py full-pipeline --generate-slides
```

Smoke test consigliato:

```powershell
python main.py generate-slides --output outputs/slides/clean_template_smoke.pptx --overwrite
```

## Template attivo

Il template attivo e:

```txt
slides/templates/Deliveroo_vs_Glovo_clean_python_ready_template.pptx
```

Ogni slide riutilizzabile deve contenere un textbox fuori canvas con un marker. Il template attivo usa varianti cromatiche per `neutral`, `deliveroo` e `glovo`:

```txt
TEMPLATE_ID:cover
TEMPLATE_ID:section_divider_neutral
TEMPLATE_ID:section_divider_deliveroo
TEMPLATE_ID:section_divider_glovo
TEMPLATE_ID:graph_full_neutral
TEMPLATE_ID:graph_full_deliveroo
TEMPLATE_ID:graph_full_glovo
TEMPLATE_ID:comparison_neutral
TEMPLATE_ID:table_large_neutral
TEMPLATE_ID:table_large_deliveroo
TEMPLATE_ID:table_large_glovo
TEMPLATE_ID:findings_neutral
TEMPLATE_ID:findings_deliveroo
TEMPLATE_ID:findings_glovo
TEMPLATE_ID:task_results_neutral
TEMPLATE_ID:task_results_deliveroo
TEMPLATE_ID:task_results_glovo
TEMPLATE_ID:ueq_question_neutral
TEMPLATE_ID:ueq_question_deliveroo
TEMPLATE_ID:ueq_question_glovo
TEMPLATE_ID:final_verdict
TEMPLATE_ID:sources
TEMPLATE_ID:text_only_neutral
TEMPLATE_ID:text_only_deliveroo
TEMPLATE_ID:text_only_glovo
```

Il generatore duplica solo le slide richieste o generate automaticamente, poi rimuove le slide template dal deck finale.

## Auto Slides

`slides/config/slide_deck.yml` abilita la generazione automatica ampia:

```yaml
auto_slides:
  enabled: true
  figure_style: dark
  include_figures: true
  include_tables: true
  include_text_findings: true
  include_text_slides: true
  include_slide_pack_text: false
  include_sources: true
  table_rows_per_slide: 12
  max_slides:
  exclude: []
```

### Modalita reference_order

Per seguire l'ordine del PDF di riferimento fornito dal gruppo, `slide_deck.yml`
puo usare:

```yaml
auto_slides:
  enabled: true
  mode: reference_order
  reference_texts: slides/content/reference_static_texts.md
```

In questa modalita il generatore sostituisce l'ordine automatico generico con
una scaletta stabile: copertina, indice, introduzione, valutazione euristica,
test utente, questionario, conclusioni e appendici. Quando un grafico o una
tabella esiste negli `outputs/`, viene inserito nella posizione corrispondente;
quando manca un contenuto specifico, viene creata una slide vuota o testuale da
completare manualmente.

I testi teorici, le descrizioni delle app e le note statiche sono centralizzati
in:

```txt
slides/content/reference_static_texts.md
```

Ogni sezione `## nome_chiave` del Markdown puo essere modificata senza cambiare
il codice Python.

Con questa configurazione il deck include:

- tutti i PNG in `outputs/figures/dark/`;
- slide task-by-task e app-by-app con `task_results`;
- slide item-by-item UEQ e app-by-app con `ueq_question`;
- tabelle CSV in `outputs/tables/`, paginate quando sono lunghe;
- testi brevi da `outputs/text_snippets/` in `findings`;
- testi lunghi da `outputs/slide_pack/` e `outputs/generated_report_sections/` in `text_only`;
- slide `text_only` con la lista degli asset usati. Il vecchio layout `sources` resta supportato come fallback, ma non e il default per questo deck.

`max_slides` vuoto significa: genera tutto quello che e disponibile. Per una revisione rapida si puo impostare un numero.

## Theme

Le slide possono dichiarare un contesto grafico:

```yaml
theme: neutral
theme: deliveroo
theme: glovo
```

Il generatore accetta sia il formato storico:

```yaml
- template_id: graph_full
  theme: deliveroo
```

sia il formato nuovo consigliato:

```yaml
- template: graph_full
  theme: deliveroo
```

Il resolver centrale trasforma automaticamente:

```txt
graph_full + deliveroo -> graph_full_deliveroo
graph_full + glovo -> graph_full_glovo
graph_full + neutral -> graph_full_neutral
comparison + qualsiasi theme -> comparison_neutral
cover -> cover
```

Regola pratica:

- slide comparative o generali -> `neutral`;
- slide solo Deliveroo -> `deliveroo`;
- slide solo Glovo -> `glovo`.

La generazione automatica inferisce il theme dai path, dai nomi degli asset e dai testi Markdown quando contengono una prevalenza chiara di `deliveroo` o `glovo`; altrimenti usa `neutral`. Per i task e gli item UEQ, quando i CSV contengono colonne o righe per app, il generatore crea slide separate Deliveroo/Glovo invece di una sola slide aggregata.

Validare il template:

```powershell
python main.py validate-slide-template
```

## Placeholder

I placeholder testuali sono sostituiti se compaiono con o senza parentesi quadre:

```txt
[PROJECT_TITLE]
PROJECT_TITLE
[GRAPH_TITLE]
GRAPH_TITLE
```

Le immagini si dichiarano cosi:

```yaml
images:
  GRAPH_MAIN: outputs/figures/dark/questionnaire/ueq_scales.png
```

Le tabelle CSV diventano tabelle PowerPoint native:

```yaml
table:
  placeholder: TABLE_MAIN
  source: outputs/tables/users_time_stat_tests.csv
```

I testi da file Markdown possono essere inseriti cosi:

```yaml
fields_from_file:
  INSIGHT_TEXT: outputs/text_snippets/questionnaire_conclusions.md
```

## Dark Mode

Il deck corrente e pensato per dark mode:

- `figure_style: dark` forza l'uso dei grafici scuri;
- i grafici dark vengono risalvati con sfondo scuro e testo chiaro;
- le tabelle native usano header scuro, righe alternate scure e testo chiaro;
- il testo generato nel PPTX viene forzato a colore chiaro;
- i placeholder opzionali non risolti vengono svuotati per evitare residui visibili.

## Anti Overflow

Il generatore applica una protezione anti-overflow sui testi:

- stima quante righe servono in base a larghezza e altezza della shape;
- riduce il font solo quando il testo rischia di uscire dalla sua area;
- mantiene il font esistente quando il testo sta gia comodamente nella shape.

Questa protezione non sostituisce una revisione visiva finale, ma riduce gli errori piu comuni nelle slide generate in massa.

## Troubleshooting

Template mancante:

```txt
Place the PowerPoint template in slides/templates/ or pass --template.
```

Asset mancante:

```txt
Run python main.py generate-report first, or use python main.py generate-slides --auto.
```

Placeholder non trovato:

```txt
Controllare che il nome nel file YAML coincida con il testo o il nome della shape nel template.
```
