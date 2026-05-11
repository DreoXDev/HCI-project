# Workflow Formbricks

> [!Info]
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

> [!Warning]
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

