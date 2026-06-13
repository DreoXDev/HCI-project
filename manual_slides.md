# Manuale slide finali

Questo documento distingue il deck finale consegnabile dal materiale di revisione usato durante lo sviluppo.

## Comando consigliato

```powershell
python -m src.cli full-pipeline --plot-style both --generate-slides --overwrite
python -m src.cli quality-check
```

Il comando genera il report finale e il deck separato per i partecipanti ai task.

## Incluso automaticamente nel report finale

La modalità `final_delivery` costruisce un report narrativo con:

- copertina, indice e divisori di sezione;
- introduzione al confronto Deliveroo vs Glovo;
- valutazione euristica con problemi separati per app e ordinati per priorità;
- matrici, grafici e tabelle sintetiche con insight testuali;
- user test con task aggiornati, efficacia, errori e tempi;
- questionario UEQ e NPS;
- conclusioni comparative e fonti statiche rilevanti.

## Escluso dal report finale

Restano fuori dal report consegnabile:

- liste di asset generati;
- appendici vuote;
- riferimenti a path locali;
- note di debug della pipeline;
- testi provvisori o indicazioni di completamento manuale.

Questi materiali possono essere usati per revisione interna, ma non devono comparire nel PPTX finale.

## Contenuti manuali ancora necessari

Prima della consegna il gruppo deve controllare o aggiungere solo contenuti realmente esterni alla pipeline:

- screenshot finali delle app, se richiesti dal docente;
- allegati amministrativi o autorizzazioni;
- link pubblici definitivi a survey o repository;
- conclusioni finali validate dal gruppo.

## Checklist

- Eseguire `validate-slide-template`.
- Eseguire `validate-slide-assets`.
- Eseguire `quality-check`.
- Aprire il PPTX finale e fare un controllo visuale.
- Esportare il PDF solo dopo il controllo visuale.
