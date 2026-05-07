# Formato dati

La configurazione del progetto vive in `config.yaml`. Per cambiare progetto o sistemi confrontati, aggiornare i nomi e i path in quel file.

## User test

Nuovo file osservazionale consigliato: `data/raw/users_time.csv`.

Ogni riga rappresenta un utente che esegue una task su una app. Vedi `docs/users_time.md`.

Colonne obbligatorie:

```txt
user_id,app,task_id,task_name,completion_time_sec,success,errors_count,help_requests
```

Il vecchio formato wide resta supportato come input legacy:

```txt
data/raw/users-time.csv
```

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

Se i dati arrivano da Formbricks, non creare questi file a mano. Usa:

```powershell
python -m src.cli import-formbricks-heuristics --input data/formbricks_raw/heuristics/export_esperti.csv
```

Poi revisiona `data/processed/heuristics_review.csv` e genera i CSV finali con:

```powershell
python -m src.cli build-heuristics-from-review --input data/processed/heuristics_review.csv --output-dir data/raw
```

## Questionario

File predefiniti:

- `data/raw/questionnaire_deliveroo.csv`
- `data/raw/questionnaire_glovo.csv`

La prima colonna contiene il nome della riga, le colonne successive gli utenti. Le prime righe sono demografiche; le righe UEQ devono avere valori 1-7; `NPS` deve avere valori 0-10.
