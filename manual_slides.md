# Manuale slide finali

Questo documento separa ciò che la pipeline genera automaticamente da ciò che, confrontando `outputs/slides/final_report.pptx` con il riferimento `EddassouliSakawSoldati.pdf`, resta da scrivere o rifinire a mano.

## Comando consigliato

```powershell
python -m src.cli full-pipeline --plot-style both --generate-slides --overwrite
```

Questo comando genera sia `outputs/slides/final_report.pptx` sia `outputs/slides/user_task_deck.pptx`.

Per rigenerare solo la presentazione da mostrare ai partecipanti durante le task:

```powershell
python -m src.cli generate-slides --config slides/config/user_task_deck.yml --overwrite
```

Per generare anche i PDF serve LibreOffice nel `PATH`:

```powershell
python -m src.cli full-pipeline --plot-style both --generate-slides --export-pdf --overwrite
```

## Slide generate automaticamente

La modalita `reference_order` in `slides/config/slide_deck.yml` costruisce il deck seguendo l'ordine del PDF guida:

- copertina, indice e sezioni principali;
- introduzione, ambiente di valutazione e descrizione delle app;
- valutazione euristica con obiettivo, euristiche, valutatori, campione, problemi, matrici e distribuzioni;
- user test con task, risultati di efficacia, errori, efficienza e viste aggregate sui tempi;
- questionario con item UEQ selezionati, confronti statistici, scale UEQ, sottogruppi e NPS;
- conclusioni, appendici placeholder, fonti statiche e mappa degli asset.

La presentazione separata `outputs/slides/user_task_deck.pptx` genera invece solo:

- apertura;
- spiegazione dello scopo del test;
- istruzioni prima di iniziare;
- task Deliveroo;
- task Glovo;
- slide finale con placeholder per il link alla survey.

Gli asset letti dalla pipeline sono soprattutto:

- `outputs/figures/dark/` per grafici e matrici;
- `outputs/tables/` per tabelle CSV adatte alle slide;
- `outputs/texts/snippets/` per testi sintetici;
- `slides/content/reference_static_texts.md` per testi statici modificabili senza toccare Python.

## Aggiunte automatiche rispetto al deck precedente

Queste parti esistono nei dati o negli output e ora vengono incluse nella generazione:

- **Matrice di expertise**: generata da `data/processed/heuristics/expert_profiles.csv` in `outputs/figures/dark/heuristics/expertise_matrix.png`.
- **Profili valutatori**: esportati anche come tabella slide in `outputs/tables/heuristics_expert_profiles.csv`.
- **Legenda efficacia**: slide testuale generata da `slides/content/reference_static_texts.md`.
- **Errori per task**: una slide per task usa `outputs/figures/dark/user_tests/tasks/tXX_error_breakdown.png`.
- **Successo e distribuzione tempi**: vista comparativa con `users_time_success_rate.png` e `users_time_boxplot_by_task.png`.

## Parti da completare manualmente o in post-produzione

Nel PDF guida ci sono sezioni che non possono essere ricostruite in modo affidabile dai CSV attuali perché dipendono da contenuti narrativi, screenshot o allegati esterni:

- **Screenshot passo-passo delle app nei task**: servono immagini reali delle schermate Deliveroo/Glovo per ogni step.
- **Appendici delle singole valutazioni euristiche**: richiedono note complete per valutatore e per app, non solo il dataset aggregato.
- **Modulo autorizzazione foto/video**: è un documento amministrativo, non un output analitico.
- **Link o allegati esterni del questionario**: eventuali URL Drive/Formbricks vanno inseriti a mano se devono comparire in appendice.
- **Dark pattern specifici**: vanno scritti solo se sono stati davvero rilevati nei dati; la pipeline non deve inventarli.
- **Conclusioni finali argomentative**: la pipeline propone una sintesi, ma il gruppo deve validare il messaggio finale prima della consegna.
- **Dati App Store o fonti aggiornate**: i testi statici contengono valori rilevati manualmente; se cambiano, aggiornare `slides/content/reference_static_texts.md`.
- **Link survey Formbricks**: sostituire `INSERIRE QUI IL LINK ALLA SURVEY FORMBRICKS` in `slides/content/reference_static_texts.md`.

## Checklist prima della consegna

- Eseguire `python -m src.cli validate-slide-template`.
- Eseguire `python -m src.cli validate-slide-assets`.
- Eseguire `python -m src.cli quality-check`.
- Rigenerare il deck con `--overwrite`.
- Aprire `outputs/slides/final_report.pptx` e controllare le slide placeholder in appendice.
- Aggiornare a mano screenshot, allegati, link e conclusioni finali.
- Esportare il PDF solo dopo il controllo visuale del PPTX.
