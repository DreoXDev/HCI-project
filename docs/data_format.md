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

## Valutazione euristica Formbricks

La pipeline euristica nuova parte dall'export grezzo della prima survey esperti:

```txt
data/raw/formbricks/heuristics_experts_raw.csv
```

Il CSV puo essere wide, con fino a 10 slot problema. Il toolkit lo normalizza in:

```txt
data/processed/heuristics/raw_problems_long.csv
data/processed/heuristics/raw_problems_table.csv
```

Colonne principali di `raw_problems_table.csv`:

```csv
raw_problem_id,evaluator_id,problem_slot,app,short_description,long_description,heuristics,notes,completion_status
```

Le euristiche sono normalizzate come `E1;E6;E10`. I blocchi vuoti vengono ignorati, quelli parziali restano nel file con `completion_status`.

Comando:

```powershell
python -m src.cli heuristics raw --input data/raw/formbricks/heuristics_experts_raw.csv
```

Dopo la review manuale, il file consolidato atteso e:

```txt
data/processed/heuristics/consolidated_problems.csv
```

Formato:

```csv
final_problem_id,app,short_description,long_description,heuristics,source_raw_problem_ids,notes
```

Quando la seconda survey e disponibile, i rating 0-4 vengono normalizzati in:

```txt
data/processed/heuristics/severity_ratings_long.csv
data/processed/heuristics/final_problem_summary.csv
```

```powershell
python -m src.cli heuristics severity --ratings data/raw/formbricks/heuristics_severity_ratings.csv --problems data/processed/heuristics/consolidated_problems.csv
```

I vecchi file `data/raw/heuristics_deliveroo.csv` e `data/raw/heuristics_glovo.csv` restano supportati dalla pipeline storica, ma non sono il formato di ingresso consigliato per nuovi dati Formbricks.

## Questionario

File predefiniti:

- `data/raw/questionnaire_deliveroo.csv`
- `data/raw/questionnaire_glovo.csv`

La prima colonna contiene il nome della riga, le colonne successive gli utenti. Le prime righe sono demografiche; le righe UEQ devono avere valori 1-7; `NPS` deve avere valori 0-10.
