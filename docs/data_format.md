# Formato dati

> [!Info]
> I file Markdown sono UTF-8. I CSV generati dalla pipeline usano `utf-8-sig` per essere leggibili anche in Excel su Windows.

## Questionario utenti

| Campo | Descrizione |
|---|---|
| Demografiche | Genere, età, professione, familiarità |
| UEQ | Item numerici su scala 1-7 |
| NPS | Valore 0-10, se presente |

Input Formbricks:

```text
data/formbricks_raw/questionnaire/
```

Output normalizzati:

```text
data/raw/questionnaire_deliveroo.csv
data/raw/questionnaire_glovo.csv
```

## Valutazione euristica

> [!Important]
> Il flusso supportato è quello completo: discovery, review manuale, rating, aggregazione severità/priorità.

### 1. Discovery problemi

Campi minimi:

| Campo | Uso |
|---|---|
| `expert_id` / `ID valutatore` | ID stabile dell'esperto |
| `expert_group` | `ED` o `EU` |
| `app` | Deliveroo o Glovo |
| `problem_title` | Titolo del problema |
| `problem_description` | Descrizione sintetica |
| `heuristic` | Euristiche violate |

### 2. Review manuale

La pipeline genera:

```text
data/processed/heuristics_candidates.csv
data/processed/heuristics_review.csv
```

Compilare `problem_group_id` per raggruppare problemi simili.

### 3. Rating severità/priorità

Campi minimi:

| Campo | Uso |
|---|---|
| `evaluator_id` | Esperto che valuta |
| `expert_group` | Gruppo ED/EU |
| `problem_group_id` | Problema consolidato |
| `severity` | Valore 0-4 |
| `frequency` | Frequenza |
| `impact` | Impatto |
| `priority` | Priorità |

## Dati osservazionali

`users_time.csv` non viene da Formbricks: è compilato dagli osservatori durante i test.

```text
data/raw/users_time.csv
```

| Campo | Descrizione |
|---|---|
| `user_id` | ID utente anonimo |
| `app` | App testata |
| `task_id` | Task |
| `completion_time_sec` | Tempo in secondi |
| `success` | Esito |
| `errors_count` | Errori osservati |
| `help_requests` | Richieste di aiuto |

