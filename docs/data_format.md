# Formato dati

La configurazione del progetto vive in `config.yaml`. Per cambiare progetto o sistemi confrontati, aggiornare i nomi e i path in quel file.

## User test

File predefinito: `data/raw/users-time.csv`.

Colonne attese:

```txt
User;Task 1 Deliveroo;Task 2 Deliveroo;Task 3 Deliveroo;Task 1 Glovo;Task 2 Glovo;Task 3 Glovo;Sesso;Eta;Lavoro;Istruzione
```

Ogni cella task usa il formato `minuti.secondi-esito`, per esempio `1.23-C`.

Codici esito:

- `C`: completato
- `A`: completato con aiuto
- `F`: fallito

## Valutazione euristica

File predefiniti:

- `data/raw/heuristics_deliveroo.csv`
- `data/raw/heuristics_glovo.csv`

Colonne chiave:

- `Problema`
- `Expert 1`, `Expert 2`, ...
- `Euristiche`, nel formato `E1-E3-E10`
- `Id valutatori`, nel formato `EU1-ED1`

## Questionario

File predefiniti:

- `data/raw/questionnaire_deliveroo.csv`
- `data/raw/questionnaire_glovo.csv`

La prima colonna contiene il nome della riga, le colonne successive gli utenti. Le prime righe sono demografiche; le righe UEQ devono avere valori 1-7; `NPS` deve avere valori 0-10.
