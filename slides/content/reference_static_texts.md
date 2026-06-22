# Testi statici per deck in ordine reference

Questo file contiene i testi modificabili usati dalla modalità `reference_order` del generatore slide. Ogni sezione `## chiave` viene letta dal codice e può essere cambiata senza toccare Python.

## components
Gruppo HCI

## academic_year
Anno accademico 2025/2026

## DATA_STATUS_LABEL
Dati finali

## data_status_note
FINAL_DATA: i risultati includono tutti gli 8 esperti della valutazione di severità, 24 utenti nel test osservazionale e 24 risposte finite al questionario.

## index
**01 Contesto**
Obiettivi, ambiente e app analizzate

**02 Analisi esperta**
Valutatori, criticita e interventi

**03 Test con utenti**
Task, tempi, errori e completamento

**04 Questionario**
Scale, item chiave e percezione d'uso

**05 Sintesi finale**
Confronto, raccomandazioni e prossimi passi

**06 Appendice**
Materiali di supporto e tabelle complete

## problem_description
Negli ultimi anni le applicazioni di **food delivery** sono diventate uno strumento sempre più presente nella vita quotidiana degli utenti, permettendo di ordinare pasti, prodotti essenziali e spesa direttamente da smartphone.

In questo contesto si inseriscono **Deliveroo** e **Glovo**, due servizi diffusi nel mercato del delivery che condividono obiettivi simili, ma propongono *flussi, scelte di interfaccia e modalità di interazione* differenti.

Il problema affrontato in questa analisi nasce dalla necessita di comprendere quanto tali differenze incidano sull'**usabilità percepita**, soprattutto durante attività frequenti:
- ricerca del ristorante
- gestione del carrello
- checkout
- monitoraggio dell'ordine

Attraverso un'analisi trasversale di usabilità, lo studio mette a confronto **Deliveroo** e **Glovo** evidenziando *punti di forza*, **criticità** e problemi che possono ostacolare efficacia, efficienza e soddisfazione d'uso.

## evaluation_environment
L'analisi e stata condotta confrontando **Deliveroo** e **Glovo** nello stesso ambiente tecnologico, usando dispositivi mobili e condizioni di utilizzo il più possibile comparabili.

Le applicazioni sono state osservate con:
- impostazioni standard
- lingua italiana
- connessione stabile

Lo scenario simulato e quello di un **utilizzo quotidiano**: ricerca di un ristorante, selezione dei prodotti, modifica del carrello, pagamento e controllo dello stato della consegna.

## app_deliveroo
**Deliveroo** e un servizio di food delivery che consente di ordinare piatti, spesa e prodotti da ristoranti, supermercati e negozi locali. L'app permette di esplorare partner disponibili nella zona, ordinare con consegna immediata o programmata e seguire l'avanzamento dell'ordine.

Nell'App Store italiano, alla data di raccolta del **10 maggio 2026**, **Deliveroo** risulta indicata con valutazione **4,6 su 5** e circa **705 mila valutazioni**. La pagina App Store evidenzia anche funzionalita come tracking dell'ordine, consegna rapida e offerte per utenti Plus.

Nel contesto di questa analisi, Deliveroo rappresenta un'app centrata sul flusso di ordinazione alimentare, con particolare attenzione alla scelta tra ristoranti, offerte, carrello e stato della consegna.

## app_glovo
**Glovo** e un'app multi-categoria nata per rendere accessibili prodotti e servizi della citta: cibo, spesa, acquisti locali e consegne rapide. L'azienda si presenta come tech company spagnola attiva in Europa, Asia Centrale e Africa.

Nell'App Store italiano, alla data di raccolta del **10 maggio 2026**, **Glovo** risulta indicata con valutazione **4,7 su 5** e circa **442 mila valutazioni**. La descrizione dello store riporta oltre **80 milioni di download**, **23 paesi serviti** e più di **240 mila ristoranti e store** disponibili.

Nel contesto di questa analisi, **Glovo** rappresenta un sistema più ampio del solo food delivery, con un'interfaccia orientata alla scelta di categorie, negozi e servizi in tempi rapidi.

## heuristic_objective
L'obiettivo della **valutazione euristica** e condurre un'analisi qualitativa dell'usabilità di **Deliveroo** e **Glovo**, fornendo una base utile per individuare criticità progettuali e differenze nell'esperienza d'uso.

Attraverso l'applicazione delle **euristiche di Nielsen**, l'analisi mira a riconoscere problemi legati a:
- chiarezza dell'interfaccia
- controllo dell'utente
- coerenza dei comandi
- prevenzione degli errori
- visibilita dello stato del sistema

I problemi emersi vengono descritti in linguaggio naturale e associati alle euristiche violate, così da evidenziare *punti di forza* e **debolezza** dei due sistemi.

## nielsen_heuristics
Le **10 euristiche di Nielsen** sono principi generali di usabilità utilizzati per valutare la qualità dell'interazione tra utente e sistema.

Il set comprende:
- visibilita dello stato del sistema
- corrispondenza con il mondo reale
- controllo e libertà dell'utente
- consistenza e standard
- prevenzione dell'errore
- riconoscimento invece di ricordo
- flessibilita ed efficienza d'uso
- estetica e minimalismo
- aiuto nel riconoscere e correggere errori
- aiuto e documentazione

Questi principi permettono di classificare le **criticità osservate** nelle due app e di collegarle a dimensioni cognitive, percettive e operative dell'interazione.

## heuristic_evaluators
Il gruppo di valutazione e composto da **utenti esperti** e valutatori con familiarita diversa rispetto alle app di delivery.

Gli esperti di usabilità si concentrano sulla **qualità dell'interfaccia** e sul rispetto dei principi di interazione, mentre gli esperti di dominio contribuiscono con osservazioni legate all'esperienza concreta di ordinazione e consegna.

La combinazione dei due punti di vista permette di analizzare:
- progettazione dell'interfaccia
- difficolta che emergono in scenari realistici

## manual_evaluator_table

## sample_composition
La composizione del campione viene letta dai dati raccolti e visualizzata attraverso grafici su eta, genere, occupazione e familiarita.

Questi elementi servono a interpretare i risultati tenendo conto del profilo dei partecipanti e del loro livello di esperienza con servizi simili.

## manual_expertise_matrix

## heuristic_problems_intro
Nelle slide successive viene presentata una lista dei **problemi di usabilità** emersi durante la valutazione euristica dei due sistemi.

Per ciascun problema e stata valutata la **gravita percepita**, assegnando un punteggio su scala **0-4**:
- 0 indica assenza di problema
- 4 indica una criticità da affrontare con priorità

I problemi sono stati poi ordinati e classificati per **priorità**, distinguendo le criticità più rilevanti da quelle meno urgenti.

## priority_criteria
La prioritizzazione si basa su tre parametri:
- **frequenza** di occorrenza del problema
- **impatto** sul task
- **persistenza** della criticità durante l'interazione

I valutatori assegnano un punteggio di gravita da **0 a 4**. I valori più alti indicano problemi rilevanti o di assoluta **priorità**, mentre i valori più bassi indicano criticità marginali o assenti.

Questa lettura permette di individuare quali problemi richiedono **interventi immediati** e quali possono essere considerati secondari.

## priority_bands
Dopo la prima suddivisione dei problemi, le criticità vengono organizzate in fasce di priorità.

La fascia A raccoglie i problemi più urgenti, la fascia B quelli intermedi e la fascia C quelli meno prioritari.

La classificazione consente di trasformare l'elenco delle osservazioni qualitative in una mappa di intervento più leggibile.

## manual_problem_list

## matrix_explanation
La matrice problemi-valutatori mostra quali criticità sono state individuate da ciascun valutatore e permette di osservare ricorrenze, accordi e differenze tra i giudizi.

## heuristic_distribution
La distribuzione delle euristiche violate permette di capire quali dimensioni dell'interazione risultano più problematiche nei due sistemi.

## heuristic_distribution_deliveroo
Per Deliveroo, la distribuzione delle euristiche violate evidenzia quali principi di usabilità risultano più frequentemente coinvolti nei problemi osservati. La torta per categorie permette di leggere la concentrazione delle criticità rispetto a dimensioni cognitive, percettive e di gestione degli errori.

## heuristic_distribution_glovo
Per Glovo, la distribuzione delle euristiche violate mostra il profilo delle criticità emerse nella valutazione esperta. Il grafico a torta evidenzia il peso relativo delle categorie di problemi, rendendo più immediata la lettura delle aree di interazione maggiormente coinvolte.

## heuristic_quantitative_conclusion
La valutazione quantitativa delle criticità deve essere letta come supporto alla discussione qualitativa.

L'obiettivo non e produrre un verdetto automatico, ma individuare le aree di intervento più importanti per migliorare l'esperienza utente.

## user_test_objective
Per valutare **efficacia** ed **efficienza** dei due servizi, abbiamo chiesto agli utenti di svolgere gli stessi task su Deliveroo e Glovo.

Ogni partecipante ha lavorato su un task alla volta. Durante l'attivita poteva pensare ad alta voce, segnalare dubbi, fermarsi in caso di blocco e non doveva completare acquisti reali.

Durante i test abbiamo osservato:
- completamento del task
- errori
- richieste di aiuto
- tempo impiegato

Il confronto tra **Deliveroo** e **Glovo** mostra dove flussi simili diventano piu semplici, piu lenti o piu difficili da portare a termine.

## user_test_tasks
Le task simulano lo stesso flusso di ordinazione in entrambe le app:

1. Inserire l'indirizzo di consegna: Piazza dell'Ateneo Nuovo, 1, 20126 Milano MI.
2. Trovare Bun Burgers nella lista di ristoranti di Hamburger, aggiungere un Menù Cheeseburger Singolo con Patatine Normali e una bibita a piacere. Procedere fino al Checkout, NON confermare l'ordine, poi tornare alla Home.
3. Aprire il carrello, modificare l'ordine da Cheeseburger Singolo a Cheeseburger Doppio, aumentare la quantita da 1 a 2 e controllare che il checkout sia corretto.

## task_deck_purpose
Questa presentazione serve a guidarti durante il test utente su Deliveroo e Glovo.
Dovrai svolgere 3 task in entrambe le applicazioni. Lo scopo delle task e di analizzare la app: Non sei sotto esaminazione, la app lo e!
Durante l'attivita puoi pensare ad alta voce, segnalare dubbi, difficolta o passaggi poco chiari.

## task_deck_before_start
Prima di iniziare:
- svolgi un task alla volta
- avvisa quando inizi e quando pensi di aver completato il task
- se qualcosa non e chiaro, dillo ad alta voce
- non inserire dati personali o completare acquisti reali.

Se un task non puo essere completato per motivi tecnici, fermati e descrivi cosa ti ha bloccato.

## user_task_1
Inserisci come indirizzo di consegna:
Piazza dell'Ateneo Nuovo, 1, 20126 Milano MI.

## user_task_1_deliveroo
Apri Deliveroo, e inserisci come indirizzo di consegna:
Piazza dell'Ateneo Nuovo, 1, 20126 Milano MI

## user_task_1_glovo
Apri Glovo, e inserisci come indirizzo di consegna:
Piazza dell'Ateneo Nuovo, 1, 20126 Milano MI

## user_task_2
Partendo dalla schermata Home:
Trova la lista di ristoranti di Hamburger. In questa lista trova il ristorante "Bun Burgers".
Aggiungi un Menù Cheeseburger Singolo, con Patatine Normali e una bibita a piacere.
Procedi fino al Checkout (NON confermare l'ordine)
Ora torna alla Home.

## user_task_2_deliveroo
Partendo dalla schermata Home:
Trova la lista di ristoranti di Hamburger. In questa lista trova il ristorante "Bun Burgers".
Aggiungi un Menù Cheeseburger Singolo, con Patatine Normali e una bibita a piacere.
Procedi fino al Checkout (NON confermare l'ordine)
Ora torna alla Home.

## user_task_2_glovo
Partendo dalla schermata Home:
Trova la lista di ristoranti di Hamburger. In questa lista trova il ristorante "Bun Burgers".
Aggiungi un Menù Cheeseburger Singolo, con Patatine Normali e una bibita a piacere.
Procedi fino al Checkout (NON confermare l'ordine)
Ora torna alla Home.

## user_task_3
Partendo dalla schermata Home:
Apri il carrello con i prodotti che hai aggiunto nel Task Precedente, e modifica l'ordine nei seguenti modi:
1. Anziche un Cheeseburger Singolo, scegli il Cheeseburger Doppio
2. Adesso, Anziche 1 Menu Cheeseburger Doppio, aumenta a 2
Raggiungi il Checkout e assicurati che l'ordine modificato sia corretto.

## user_task_3_deliveroo
Partendo dalla schermata Home:
Apri il carrello con i prodotti che hai aggiunto nel Task Precedente, e modifica l'ordine nei seguenti modi:
1. Anziche un Cheeseburger Singolo, scegli il Cheeseburger Doppio
2. Adesso, Anziche 1 Menu Cheeseburger Doppio, aumenta a 2
Raggiungi il Checkout e assicurati che l'ordine modificato sia corretto.

## user_task_3_glovo
Partendo dalla schermata Home:
Apri il carrello con i prodotti che hai aggiunto nel Task Precedente, e modifica l'ordine nei seguenti modi:
1. Anziche un Cheeseburger Singolo, scegli il Cheeseburger Doppio
2. Adesso, Anziche 1 Menu Cheeseburger Doppio, aumenta a 2
Raggiungi il Checkout e assicurati che l'ordine modificato sia corretto.

## user_task_4
Completa il checkout fino alla schermata finale prima della conferma definitiva.

## user_task_4_deliveroo
1. Apri il carrello.
2. Controlla indirizzo e orario.
3. Seleziona il metodo di pagamento.
4. Arriva alla schermata di riepilogo.

## user_task_4_glovo
1. Apri il carrello.
2. Controlla indirizzo e orario.
3. Seleziona il metodo di pagamento.
4. Arriva alla schermata di riepilogo.

## user_task_5
Individua dove si controlla lo stato dell'ordine e interpreta le informazioni di tracking.

## user_task_5_deliveroo
1. Accedi allo stato dell'ordine.
2. Identifica la fase corrente.
3. Controlla tempo stimato e dettagli della consegna.

## user_task_5_glovo
1. Accedi allo stato dell'ordine.
2. Identifica la fase corrente.
3. Controlla tempo stimato e dettagli della consegna.

## task_deck_survey
Bene! Grazie di aver partecipato ai Test.
Prima di concludere, compila il questionario finale:
serve a raccogliere la tua percezione d'uso su Deliveroo e Glovo dopo l'esperienza pratica.
Link questionario:
SURVEY FORMBRICKS

## user_test_sample
La composizione del campione dei test utente aiuta a leggere **tempi**, **errori** e successo dei task in relazione al profilo dei partecipanti.

Stato raccolta: **dati finali**, 24 utenti disponibili su 24 previsti.

## effectiveness_intro
Sono state distinte due metriche: l'**efficacia** misura il completamento complessivo del task, mentre l'**efficacia assoluta** considera solo i task completati autonomamente e senza criticità annotate.

## effectiveness_legend
I casi completati con aiuto o workaround sono inclusi nell'efficacia generale, ma esclusi dall'efficacia assoluta.

Efficacia: task completata, anche con aiuto o criticità.
Efficacia assoluta: task completata senza aiuto e senza criticità annotate.
Completamento con criticità: task completata ma con aiuto, workaround o problema rilevante.

## efficiency_intro
L'**efficienza** considera il tempo necessario per completare i task, confrontando le prestazioni tra app e tra attività.

Le analisi di efficienza principale considerano solo i tempi dei task completati autonomamente. I tempi dei task completati con aiuto sono riportati nei dati grezzi, ma non usati per stimare l'efficienza autonoma.

## task_result_placeholder
Il task va letto combinando successo, errori e tempo: una differenza di durata diventa rilevante soprattutto quando coincide con esitazioni, richieste di aiuto o perdita di controllo nel flusso.

## task_error_placeholder
La slide mostra gli errori medi osservati per il task. Usarla insieme alla slide di efficacia per distinguere task completati rapidamente da task completati con frizioni operative.

## users_time_summary
La lettura congiunta di **tempi**, successo ed errori permette di distinguere task rapidi ma problematici da task più lunghi ma completati correttamente.

## user_test_statistical_significance
I tempi dei task sono stati confrontati usando gli stessi **24 partecipanti** su Deliveroo e Glovo, quindi il confronto e **appaiato**. Per i p-value principali vengono usate solo coppie in cui l'utente ha completato autonomamente il task su entrambe le app; con meno di 5 coppie valide il confronto viene indicato come non sufficiente.

Per ogni task la pipeline seleziona un test appaiato sui tempi di completamento:
- paired t-test quando la distribuzione delle differenze e compatibile con l'assunzione di normalita
- Wilcoxon signed-rank quando la distribuzione delle differenze non supporta tale assunzione

La soglia di significativita e **alpha = 0,05**. Un p-value inferiore a 0,05 indica una differenza statisticamente significativa tra le due app per quel task; un p-value superiore indica che la differenza osservata va trattata come descrittiva.

## questionnaire_intro
Una buona applicazione non deve soltanto funzionare correttamente: deve anche risultare **comprensibile**, *piacevole*, prevedibile e adatta alle aspettative degli utenti.

Il questionario raccoglie la **percezione soggettiva** dei partecipanti e completa la valutazione oggettiva ottenuta con euristiche e **user test**.

## questionnaire_sample
La composizione del campione del questionario viene usata per contestualizzare i risultati **UEQ** e **NPS**.

Stato raccolta: **dati finali**, 24 risposte finite su 24 previste.

## questionnaire_item_placeholder
Insight calcolato automaticamente dalla tabella `questionnaire_items_summary.csv` per la domanda mostrata.

## questionnaire_comparison_intro
Nelle slide successive vengono presentati alcuni **confronti tra sistemi** sulle domande più rappresentative.

L'obiettivo e osservare se le differenze percepite dagli utenti sono coerenti con le evidenze emerse nei test e nella **valutazione euristica**.

## questionnaire_stat_placeholder
Insight statistico calcolato automaticamente dalla tabella `questionnaire_items_summary.csv` per la domanda mostrata.

## ueq_scale
La scala **UEQ** consente di misurare l'esperienza d'uso lungo dimensioni come:
- attrattiva
- perspicuita
- efficienza
- affidabilita
- stimolazione
- novita

Il confronto tra sistemi permette di leggere non solo la **prestazione funzionale**, ma anche il vissuto soggettivo degli utenti.

## subgroup_placeholder
L'analisi per sottogruppi contestualizza i risultati rispetto al profilo dei partecipanti.

## ueq_table_placeholder
La tabella riassume le scale UEQ e rende confrontabili le dimensioni principali dell'esperienza d'uso.

## ueq_summary
Il grafico riassume le scale **UEQ** e permette di individuare rapidamente le dimensioni in cui una delle due app risulta percepita meglio.

## nps_intro
Il **Net Promoter Score** misura la disponibilita degli utenti a consigliare un servizio.

Il grafico confronta Deliveroo e Glovo nella stessa vista e sintetizza **promotori**, passivi e **detrattori**, offrendo una lettura immediata della soddisfazione complessiva.

## nps_placeholder
La distribuzione NPS distingue promotori, passivi e detrattori per l'app selezionata.

## deliveroo_strength_1
**Flusso di ordinazione** focalizzato sul food delivery.

## deliveroo_strength_2
**Tracking** e gestione dell'ordine ben riconoscibili.

## deliveroo_weakness
Possibili **criticità** nei passaggi di modifica carrello e checkout.

## glovo_strength_1
**Ampiezza dell'offerta** e categorie multi-servizio.

## glovo_strength_2
**Percorso rapido** per accedere a negozi e prodotti diversi.

## glovo_weakness
La maggiore ampiezza funzionale può aumentare **carico cognitivo** e dispersione.

## winner_label
Il confronto va letto integrando **euristiche**, **user test**, **UEQ** e **NPS**: il risultato finale non e un verdetto automatico, ma una sintesi delle evidenze raccolte.

## conclusions
L'analisi ha confrontato Deliveroo e Glovo attraverso valutazione euristica, user test e questionario.

Nel complesso, le differenze principali emergono dal modo in cui le due app organizzano:
- ricerca
- scelta dei prodotti
- carrello
- conferma dell'ordine

Le conclusioni finali vanno validate dal gruppo sulla base dei dati raccolti e delle evidenze presentate nel report.

## appendix_placeholder
Materiale di supporto incluso quando disponibile.

## table_footnote
Dati ordinati e sintetizzati per la presentazione finale.


## nps_placeholder
La distribuzione NPS distingue promotori, passivi e detrattori per l'app selezionata.

## deliveroo_strength_1
**Flusso di ordinazione** focalizzato sul food delivery.

## deliveroo_strength_2
**Tracking** e gestione dell'ordine ben riconoscibili.

## deliveroo_weakness
Possibili **criticità** nei passaggi di modifica carrello e checkout.

## glovo_strength_1
**Ampiezza dell'offerta** e categorie multi-servizio.

## glovo_strength_2
**Percorso rapido** per accedere a negozi e prodotti diversi.

## glovo_weakness
La maggiore ampiezza funzionale può aumentare **carico cognitivo** e dispersione.

## winner_label
Il confronto va letto integrando **euristiche**, **user test**, **UEQ** e **NPS**: il risultato finale non e un verdetto automatico, ma una sintesi delle evidenze raccolte.

## conclusions
L'analisi ha confrontato Deliveroo e Glovo attraverso valutazione euristica, user test e questionario.

Nel complesso, le differenze principali emergono dal modo in cui le due app organizzano:
- ricerca
- scelta dei prodotti
- carrello
- conferma dell'ordine

Le conclusioni finali vanno validate dal gruppo sulla base dei dati raccolti e delle evidenze presentate nel report.

## appendix_placeholder
Materiale di supporto incluso quando disponibile.

## table_footnote
Dati ordinati e sintetizzati per la presentazione finale.

## sources
Fonti consultate per i testi statici, rilevate il 10 maggio 2026:

- Apple App Store Italia, pagina Deliveroo: valutazione 4,6 su 5, circa 705K valutazioni, descrizione funzionale dell'app.
- Apple App Store Italia, pagina Glovo: valutazione 4,7 su 5, circa 442K valutazioni, oltre 80 milioni di download, 23 paesi e più di 240K ristoranti/store.
- Deliveroo Help Centre, "Deliveroo 101: how it works": descrizione del tracking ordine, rete di rider e modello di consegna.
- Glovo corporate site, "This is Glovo" e homepage: descrizione aziendale, presenza in 23 paesi, 120K corrieri mensili, 150K store mensili e 3K dipendenti.

## expert_demographics
Il campione dei valutatori è composto da 8 esperti. La maggioranza è costituita da studenti under 25, con una presenza prevalentemente maschile. Questa composizione va considerata nella lettura dei risultati, perché riflette un campione giovane e con buona familiarità con servizi digitali.

Nota: i valutatori costituiscono un unico campione esperto; ciascun esperto ha valutato entrambe le applicazioni.

## expert_profile_experience
Il gruppo include sia esperti di usabilità sia esperti di dominio. La familiarità con app di delivery è prevalentemente intermedia, mentre i punteggi di esperienza in usabilità e dominio consentono di bilanciare osservazioni metodologiche e conoscenza pratica del contesto d'uso.

Nota: i valutatori costituiscono un unico campione esperto; ciascun esperto ha valutato entrambe le applicazioni.

## user_demographics
Il campione utenti è composto da 24 partecipanti. Le variabili demografiche sono state conteggiate una sola volta per utente, poiché ogni partecipante ha valutato entrambi i sistemi.

Nota: le variabili demografiche sono conteggiate una sola volta per partecipante. Gli stessi utenti hanno valutato entrambe le applicazioni.

## user_familiarity_profile
La familiarità con le app di delivery permette di interpretare le prestazioni nei task e le risposte al questionario. Il campione non rappresenta due gruppi distinti per app: gli stessi utenti hanno svolto task e valutazioni su entrambi i sistemi.

Nota: le variabili demografiche sono conteggiate una sola volta per partecipante. Gli stessi utenti hanno valutato entrambe le applicazioni.
