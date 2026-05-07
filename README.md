# HCI Project - Toolkit di analisi per Deliveroo vs Glovo

Questo progetto nasce come repository di supporto per un progetto di Interazione Uomo-Macchina. La versione originale conteneva notebook Jupyter e CSV di esempio pensati per generare rapidamente grafici e statistiche a partire dai dati raccolti durante user test, valutazione euristica e questionari utente.

La repository e stata poi rifattorizzata per diventare un piccolo toolkit modulare, configurabile e riusabile. L'obiettivo attuale e supportare il progetto **Deliveroo vs Glovo** senza dover modificare manualmente il codice dei notebook ogni volta che cambiano nomi dei sistemi, path dei file o impostazioni grafiche.

## Attenzione

I dati presenti nella repository sono puramente illustrativi. Ogni progetto deve usare dati propri raccolti durante il lavoro di gruppo.

I CSV in `data/raw/` sono pronti per Deliveroo e Glovo, ma al momento derivano dai file di esempio originali. Per usare la pipeline nel progetto reale, sostituire questi file con i dati effettivamente raccolti.

## Cosa fa il progetto

Il toolkit permette di:

- validare automaticamente i CSV prima dell'analisi
- calcolare efficacia ed efficienza degli user test
- analizzare il dataset osservazionale `users_time.csv` con tempi, success rate, errori e richieste di aiuto
- generare grafici comparativi tra i due sistemi
- analizzare i problemi della valutazione euristica
- calcolare severita media, mediana e priorita dei problemi
- contare le euristiche violate e raggrupparle per categoria
- analizzare questionari UEQ e NPS
- esportare tabelle in CSV e Markdown
- esportare grafici in PNG e SVG
- generare brevi frasi interpretative pronte per report o slide
- rilanciare l'intera pipeline con un unico comando o un unico notebook

## Differenze rispetto alla versione originale

Nella versione originale la logica era concentrata soprattutto in due notebook:

- `stats_ium.ipynb`: statistiche e grafici su efficacia, efficienza, euristiche violate e prioritizzazione dei problemi
- `Stats quest utente.ipynb`: statistiche sui questionari utente, grafici UEQ e analisi NPS

Dopo il refactor:

- i notebook originali sono conservati in `notebooks/original/`
- la logica riusabile e stata spostata in `src/`
- i nomi dei sistemi sono letti da `config.yaml`
- i path dei file sono centralizzati
- i CSV sono organizzati in `data/`
- gli output sono salvati automaticamente in `outputs/`
- i nuovi notebook sono interfacce leggere sopra i moduli Python
- e possibile eseguire tutto con `python -m src.cli all`

## Setup

Il virtual environment Python e stato creato nella cartella superiore alla repo:

```powershell
D:\Projects\IUM\Improved Notebooks\.venv
```

Per attivarlo da dentro la cartella `HCI-project`:

```powershell
..\.venv\Scripts\Activate.ps1
```

Se si deve ricreare l'ambiente da zero:

```powershell
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

## Esecuzione rapida

Da dentro la cartella della repo:

```powershell
python -m src.cli full-pipeline
```

Il comando esegue:

- import dei CSV Formbricks disponibili
- caricamento della configurazione
- caricamento dei CSV
- validazione dei dati
- analisi user test
- analisi euristica
- analisi questionari UEQ e NPS
- esportazione grafici, tabelle e testi
- generazione asset slide
- generazione `outputs/slide_manifest.md`

Se trova un export euristico Formbricks, il comando si ferma dopo aver creato `data/processed/heuristics_review.csv`: bisogna completare la review manuale e lanciare `build-heuristics-from-review` prima dell'analisi finale.

Se si vogliono usare solo i CSV gia puliti in `data/raw/`, usare invece:

```powershell
python -m src.cli all
```

## Comandi disponibili

Validare soltanto i dati:

```powershell
python -m src.cli validate
```

Eseguire le analisi e generare gli output:

```powershell
python -m src.cli analyze
```

Creare template CSV vuoti o minimali:

```powershell
python -m src.cli create-templates
```

Eseguire tutto:

```powershell
python -m src.cli all
```

Importare e convertire i CSV esportati da Formbricks:

```powershell
python -m src.cli import-formbricks
python -m src.cli import-formbricks-questionnaire
python -m src.cli import-formbricks-heuristics
python -m src.cli build-heuristics-from-review
python -m src.cli validate-users-time
python -m src.cli analyze-users-time
python -m src.cli import-formbricks-all
python -m src.cli all-from-formbricks
python -m src.cli import-any-form --input data/formbricks_raw/export.csv
python -m src.cli full-pipeline
```

Con un file esplicito:

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire_export_2026_05_07.csv
```

## Valutazione euristica da Formbricks

Questo e il flusso consigliato per nuovi dati. Importa una riga Formbricks per ogni problema trovato da un valutatore, genera una tabella di candidati e lascia manuale solo il raggruppamento dei problemi simili.

1. Creare il form con almeno questi campi: `evaluator_id`, `app`, `task`, `short_description`, `long_description`, `heuristic`, `severity`, `top5`.
2. Se Formbricks esporta intestazioni diverse, aggiornare `config/formbricks_heuristics_mapping.yml`.
3. Salvare il CSV esportato in `data/formbricks_raw/heuristics/`, per esempio `data/formbricks_raw/heuristics/export_esperti.csv`.
4. Importare e normalizzare i candidati:

```powershell
python -m src.cli import-formbricks-heuristics --input data/formbricks_raw/heuristics/export_esperti.csv
```

Il comando genera:

```txt
data/processed/heuristics_candidates.csv
data/processed/heuristics_review.csv
reports/heuristics_import_report.md
reports/heuristics_import_errors.csv
```

5. Aprire `data/processed/heuristics_review.csv` e compilare manualmente `problem_group_id`: problemi diversi devono avere gruppi diversi, problemi simili o duplicati devono condividere lo stesso gruppo.
6. Generare i CSV finali per app:

```powershell
python -m src.cli build-heuristics-from-review --input data/processed/heuristics_review.csv --output-dir data/raw
```

Il comando genera file come:

```txt
data/raw/heuristics_deliveroo.csv
data/raw/heuristics_glovo.csv
reports/heuristics_build_report.md
```

La priorita viene calcolata con `scipy.stats.binomtest` sul numero di valutatori che hanno marcato il problema come `top5`: `A` quando i `top5` prevalgono in modo significativo, `C` quando prevalgono i non `top5`, `B` nei casi intermedi. La deduplicazione semantica non e automatica: resta una revisione manuale del gruppo problema.

Gli esempi minimi sono in:

```txt
examples/formbricks_heuristics_export_example.csv
examples/heuristics_review_example.csv
examples/heuristics_final_deliveroo_example.csv
examples/heuristics_final_glovo_example.csv
```

## Manuale operativo

Per il flusso completo partendo dai tre file di lavoro, usare:

```txt
Manuale.md
handbook.md
docs/formbricks_workflow.md
```

La sequenza di produzione e:

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/export_questionario.csv
python -m src.cli import-formbricks-heuristics --input data/formbricks_raw/heuristics/export_esperti.csv
# revisione manuale di data/processed/heuristics_review.csv
python -m src.cli build-heuristics-from-review --input data/processed/heuristics_review.csv --output-dir data/raw
python -m src.cli validate
python -m src.cli all
```

`data/raw/users_time.csv` deve essere compilato manualmente dagli osservatori. Non usare Formbricks per questi dati: parti dal template in `data/examples/users_time_template.xlsx`.

## Users Time osservazionale

`users_time` e il dataset manuale dei test utenti. Non va raccolto tramite Formbricks: contiene misurazioni osservazionali compilate dall'osservatore.

File ufficiale:

```txt
data/raw/users_time.csv
```

Template ed esempi:

```txt
data/examples/users_time_template.csv
data/examples/users_time_template.xlsx
data/examples/users_time_example.csv
data/examples/users_time_example.xlsx
```

Comandi:

```powershell
python -m src.cli create-templates
python -m src.cli validate-users-time
python -m src.cli analyze-users-time
```

Output:

```txt
outputs/reports/users_time_validation_report.md
outputs/tables/users_time_summary.csv
outputs/tables/users_time_summary.md
outputs/tables/users_time_stat_tests.csv
outputs/figures/users_time_mean_by_task.png
outputs/figures/users_time_boxplot_by_task.png
outputs/figures/users_time_success_rate.png
outputs/figures/users_time_errors_by_task.png
outputs/text/users_time_interpretation.md
```

Il vecchio `data/raw/users-time.csv` resta usato dalla pipeline legacy di efficacia/efficienza. Per nuovi dati, preferire `data/raw/users_time.csv`.

## Graph styling

La pipeline genera due versioni dei grafici:

- `clean`: grafici puliti per report e controllo statistico
- `presentation`: grafici con sfondo trasparente e DPI alto per slide

Comandi:

```powershell
python -m src.cli full-pipeline --plot-style clean
python -m src.cli full-pipeline --plot-style presentation
python -m src.cli full-pipeline --plot-style both
```

Output:

```txt
outputs/figures/clean/
outputs/figures/presentation/
```

La guida completa e in `docs/visual_style.md`.

## Notebook

I notebook nuovi sono pensati per essere leggibili e leggeri. Non contengono piu tutta la logica di analisi, ma importano le funzioni da `src/`.

- `notebooks/00_run_all.ipynb`: esegue l'intera pipeline
- `notebooks/01_user_test_analysis.ipynb`: analisi user test
- `notebooks/02_heuristic_analysis.ipynb`: analisi valutazione euristica
- `notebooks/03_questionnaire_ueq_nps.ipynb`: analisi UEQ e NPS
- `notebooks/original/`: notebook originali conservati come riferimento

Per aprire Jupyter:

```powershell
jupyter notebook
```

Poi aprire `notebooks/00_run_all.ipynb`.

## Struttura del progetto

```txt
HCI-project/
|
|-- config.yaml
|-- requirements.txt
|-- README.md
|
|-- data/
|   |-- raw/
|   |-- examples/
|   |-- formbricks_raw/
|   |-- processed/
|   |-- templates/
|
|-- docs/
|   |-- data_format.md
|   |-- analysis_pipeline.md
|   |-- formbricks_import.md
|   |-- dynamic_form_architecture.md
|   |-- codex_notes.md
|
|-- notebooks/
|   |-- 00_run_all.ipynb
|   |-- 01_user_test_analysis.ipynb
|   |-- 02_heuristic_analysis.ipynb
|   |-- 03_questionnaire_ueq_nps.ipynb
|   |-- original/
|
|-- outputs/
|   |-- figures/
|   |-- tables/
|   |-- tables_md/
|   |-- report_assets/
|   |-- text_snippets/
|
|-- src/
    |-- adapters/
    |-- config.py
    |-- data_loading.py
    |-- validation.py
    |-- user_tests.py
    |-- heuristics.py
    |-- questionnaire.py
    |-- statistics.py
    |-- plots.py
    |-- tables.py
    |-- export.py
    |-- cli.py
    |-- schemas/
```

## Configurazione

Il file `config.yaml` contiene le impostazioni principali del progetto:

- titolo del progetto
- nomi dei due sistemi
- path dei CSV
- path degli output
- colori Deliveroo e Glovo
- parametri di analisi
- range validi per UEQ e NPS
- numero di decimali da usare negli output
- mapping delle colonne esportate da Formbricks
- righe demografiche del questionario
- tag machine-readable per import dinamico
- path degli schemi YAML

Per cambiare progetto o sistemi confrontati, modificare principalmente:

```yaml
project:
  system_1: "Deliveroo"
  system_2: "Glovo"
```

e i path nella sezione:

```yaml
paths:
```

## Formato dei dati

### User test

Formato osservazionale consigliato:

```txt
data/raw/users_time.csv
```

Ogni riga rappresenta un utente che esegue una task su una app. Colonne principali:

```txt
user_id,app,task_id,task_name,completion_time_sec,success,errors_count,help_requests
```

Formato legacy ancora supportato:

```txt
data/raw/users-time.csv
```

Formato delle colonne:

```txt
User;Task 1 Deliveroo;Task 2 Deliveroo;Task 3 Deliveroo;Task 1 Glovo;Task 2 Glovo;Task 3 Glovo;Sesso;Eta;Lavoro;Istruzione
```

Ogni cella task deve avere il formato:

```txt
1.23-C
```

Dove:

- `1.23` indica minuti e secondi
- `C` significa task completato correttamente
- `A` significa task completato con aiuto
- `F` significa task fallito

### Valutazione euristica

File attivi:

```txt
data/raw/heuristics_deliveroo.csv
data/raw/heuristics_glovo.csv
```

Formato concettuale:

| Codice problema | Problema             | Expert 1 | Expert 2 | ... | Euristiche | Id valutatori |
| --------------- | -------------------- | -------: | -------: | --- | ---------- | ------------- |
| PB1             | Descrizione problema |        2 |        3 | ... | E1-E5      | EU1-ED1       |

Indicazioni:

- la prima colonna contiene il codice del problema
- `Problema` contiene una descrizione breve
- `Expert X` contiene la severita assegnata dal valutatore, da 0 a 4
- `Euristiche` contiene valori come `E1`, `E2-E3` o `E1-E5-E10`
- `Id valutatori` contiene gli identificativi dei valutatori che hanno trovato il problema, per esempio `EU2-ED1`

### Questionari UEQ e NPS

File attivi:

```txt
data/raw/questionnaire_deliveroo.csv
data/raw/questionnaire_glovo.csv
```

Ogni colonna rappresenta un utente. Le righe iniziali contengono informazioni demografiche, poi seguono gli item UEQ e infine la riga `NPS`.

Formato concettuale:

| item                          | Utente 1 | ... |  Utente 24 |
| ----------------------------- | -------: | --- | ---------: |
| genere                        |  Maschio | ... |    Femmina |
| eta                           |       25 | ... |         32 |
| situazione lavorativa         | Studente | ... | Lavoratore |
| istruzione                    |   Laurea | ... |    Diploma |
| fastidioso-piacevole          |        4 | ... |          6 |
| incomprensibile-comprensibile |        5 | ... |          7 |
| NPS                           |        8 | ... |         10 |

Regole:

- gli item UEQ devono essere nel range 1-7
- `NPS` deve essere nel range 0-10
- le prime righe demografiche non vengono trattate come valori UEQ

## Validazione automatica

La pipeline controlla:

- colonne task mancanti
- formato errato dei tempi
- codici task diversi da `C`, `A`, `F`
- celle vuote
- valori di severita fuori range 0-4
- euristiche scritte in formato non valido
- valori UEQ fuori range 1-7
- valori NPS fuori range 0-10

Se la riga `NPS` manca, il toolkit emette un warning e salta il grafico NPS senza bloccare l'intera pipeline. Per la versione finale del progetto e comunque consigliato aggiungere una domanda NPS per ciascuna app.

Esempio di output:

```txt
OK: users-time.csv valido
OK: file euristiche valido
OK: file euristiche valido
OK: questionario valido
OK: questionario valido
```

## Output generati

La pipeline scrive gli output in `outputs/`.

### Grafici

Cartella:

```txt
outputs/figures/
```

Sono generati grafici PNG e SVG, tra cui:

- `user_tests/effectiveness_deliveroo_vs_glovo.png`
- `user_tests/effectiveness_confidence_interval.png`
- `user_tests/efficiency_boxplot.png`
- `user_tests/efficiency_violinplot.png`
- `heuristics/heuristics_distribution.png`
- `heuristics/heuristics_by_category.png`
- `questionnaire/ueq_scales.png`
- `questionnaire/nps_comparison.png`

### Tabelle

Cartelle:

```txt
outputs/tables/
outputs/tables_md/
```

Sono generate tabelle CSV e Markdown, tra cui:

- `user_test_effectiveness`
- `user_test_efficiency`
- `heuristics_summary`
- `problems_priority_table`
- `ueq_summary`
- `nps_summary`
- `subgroup_analysis`

### Testi per report

Cartella:

```txt
outputs/text_snippets/
```

Contiene frasi interpretative automatiche, per esempio sui test statistici degli user test.

### Report import Formbricks

Quando si usa l'importer Formbricks viene creato:

```txt
outputs/import_report.md
```

Il report indica:

- file importato
- numero di risposte raw
- numero di risposte usate
- numero di risposte escluse perche incomplete
- colonne riconosciute
- colonne ignorate
- warning
- output generati

## Moduli Python

La logica principale si trova in `src/`.

- `config.py`: caricamento configurazione e creazione cartelle output
- `data_loading.py`: lettura dei CSV con separatore automatico
- `validation.py`: controlli sui dati in input
- `formbricks_adapter.py`: conversione CSV Formbricks nel formato del toolkit
- `adapters/formbricks/`: adapter dinamici basati su tag, alias e schemi
- `schemas/`: schemi YAML per questionari, euristiche e user test
- `user_tests.py`: parsing task, efficacia, efficienza e statistiche user test
- `heuristics.py`: severita, priorita, distribuzione euristiche e categorie
- `questionnaire.py`: item UEQ, scale UEQ, NPS e sottogruppi
- `statistics.py`: intervalli di confidenza e frasi interpretative
- `plots.py`: tema grafico e funzioni di plotting
- `tables.py`: export tabelle CSV, Excel e Markdown
- `export.py`: creazione template CSV
- `cli.py`: interfaccia a riga di comando

## Funzionalita migliorate

Rispetto alla base originale sono stati implementati o preparati:

- configurazione unica in `config.yaml`
- rimozione dei nomi hardcoded dai notebook nuovi
- struttura dati organizzata
- validazione automatica dei CSV
- export automatico di grafici
- export automatico di tabelle
- template CSV generabili da CLI
- tema grafico centralizzato
- arrotondamento automatico dei decimali
- grafico efficacia con intervalli di confidenza
- boxplot e violin plot per efficienza
- distribuzione euristiche per categoria
- sintesi UEQ con range 1-7
- analisi NPS
- frasi interpretative con approccio "metodo del gorilla"
- notebook `00_run_all.ipynb`
- CLI `python -m src.cli`
- import automatico da Formbricks
- import dinamico con `import-any-form`
- report di import Formbricks
- NPS opzionale durante le fasi intermedie
- demographics arbitrarie e subgroup analysis generica

## Workflow consigliato

1. Aggiornare `config.yaml` con titolo, nomi sistemi e path corretti.
2. Se i dati arrivano da Formbricks, salvare gli export originali in `data/formbricks_raw/`.
3. Eseguire `python -m src.cli import-formbricks-all`, oppure inserire manualmente i CSV gia convertiti in `data/raw/`.
4. Controllare `outputs/import_report.md`.
5. Eseguire `python -m src.cli validate`.
6. Correggere eventuali errori segnalati.
7. Eseguire `python -m src.cli all`.
8. Usare grafici e tabelle da `outputs/` per report, PDF e slide.

## Documentazione aggiuntiva

Sono disponibili anche:

- `docs/data_format.md`: formato dei CSV
- `docs/analysis_pipeline.md`: comandi e pipeline
- `docs/formbricks_import.md`: import e conversione dei CSV Formbricks
- `docs/dynamic_form_architecture.md`: architettura dinamica schema/tag driven
- `docs/formbricks_workflow.md`: flusso completo con CSV Formbricks
- `docs/heuristic_consolidation.md`: consolidamento manuale dei problemi euristici
- `docs/users_time.md`: dataset osservazionale manuale dei test utenti
- `docs/visual_style.md`: stile centralizzato dei grafici
- `docs/codex_notes.md`: note operative per agenti AI che lavorano sul progetto
- `docs/slide_generation.md`: uso degli asset slide
- `docs/text_snippets.md`: testi generati per report
- `docs/troubleshooting.md`: problemi comuni
- `handbook.md`: guida operativa breve dalla root del progetto
- `Manuale.md`: checklist passo-passo per arrivare dagli input all'analisi completa

## Requirements

Le dipendenze principali sono:

- Python 3
- Jupyter Notebook
- pandas
- numpy
- matplotlib
- seaborn
- scipy
- PyYAML
- openpyxl
- nbformat
- tabulate

Tutte le dipendenze sono elencate in `requirements.txt`.
