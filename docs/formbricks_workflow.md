# Workflow Formbricks

> [!info]
> Questa pagina separa questionario utenti, valutazione euristica e dati osservazionali.

## 1. Questionario utenti

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/formbricks_questionnaire_demo_12_users.csv
```

Output:

```text
data/raw/questionnaire_deliveroo.csv
data/raw/questionnaire_glovo.csv
```

## 2. Discovery euristica

```powershell
python -m src.cli import-formbricks-heuristics-discovery --input data/formbricks_raw/heuristics_discovery/formbricks_heuristics_discovery_demo_6_experts.csv
```

Output:

```text
data/processed/heuristics_candidates.csv
data/processed/heuristics_review.csv
```

## 3. Review manuale

> [!warning]
> La deduplicazione non è automatica: apri `heuristics_review.csv` e compila `problem_group_id`.

Checklist:

- [ ] Problemi simili raggruppati
- [ ] `problem_group_id` coerente
- [ ] Titoli leggibili
- [ ] App corretta

## 4. Rating severità/priorità

```powershell
python -m src.cli import-formbricks-heuristics-ratings --input data/formbricks_raw/heuristics_ratings/formbricks_heuristics_ratings_demo_6_experts.csv --output data/templates/heuristics_consolidated_problems_demo.csv
```

## 5. Dati osservazionali

`users_time.csv` non viene da Formbricks. Va compilato dagli osservatori:

```text
data/raw/users_time.csv
```

## Collegamenti

- [Manuale](manual.md)
- [Formato dati](data_format.md)
- [Mappa CLI](cli_api.md)

## Workflow severità deduplicato

> [!info]
> Per il workflow nuovo usare `clean_problems.csv` e una survey Formbricks con domande tipo `[P001] Titolo problema`.

Percorsi consigliati:

```text
data/processed/heuristics/clean_problems.csv
data/formbricks_raw/heuristics/severity_ratings_export.csv
```

Comando unico:

```powershell
python -m src.cli heuristics severity-pipeline --problems data/processed/heuristics/clean_problems.csv --ratings-export data/formbricks_raw/heuristics/severity_ratings_export.csv --out outputs/heuristics --strict
```

Il parser ignora `No.`, `Response ID`, `Timestamp`, `Finished`, `Survey ID`, metadata utente e colonne `- Option ID`. Le severità accettate sono numeriche o testuali sulla scala Nielsen 0-4.
