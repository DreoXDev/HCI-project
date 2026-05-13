# Users Time Dataset

## Cos'e

Il dataset `users_time` raccoglie metriche osservazionali dei test utenti:

- tempo di completamento delle task
- successo o fallimento
- errori osservati
- richieste di aiuto
- note qualitative dell'osservatore

## Quando compilarlo

Va compilato durante i test utenti, mentre il partecipante esegue task definite. Ogni riga rappresenta un utente che esegue una task su una app.

## perché non usare Formbricks

Questi dati sono misurazioni e osservazioni, non risposte soggettive. Sono più adatti a un foglio CSV/XLSX compilato live da un osservatore.

## File ufficiale

```txt
data/raw/users_time.csv
```

Il progetto usa il formato snake_case `users_time.csv`.

## Colonne obbligatorie

| Colonna | Tipo | Esempio | Descrizione |
| --- | --- | --- | --- |
| `user_id` | string | `U01` | ID anonimo partecipante |
| `app` | string | `Deliveroo` | App testata |
| `task_id` | string | `T01` | ID task |
| `task_name` | string | `Ricerca ristorante` | Nome leggibile della task |
| `completion_time_sec` | number | `42` | Tempo in secondi |
| `success` | boolean | `true` | Task completata con successo |
| `errors_count` | integer | `1` | Errori osservati |
| `help_requests` | integer | `0` | Richieste di aiuto |

## Colonne opzionali

| Colonna | Esempio |
| --- | --- |
| `notes` | `Utente indeciso nel checkout` |
| `start_time` | `14:32:10` |
| `end_time` | `14:32:52` |
| `device` | `Android` |
| `observer_id` | `OBS1` |
| `order` | `1` |

## Workflow

1. Genera template:

```powershell
python -m src.cli create-templates
```

2. Compila `data/examples/users_time_template.xlsx` durante i test.
3. Salva una copia pulita come:

```txt
data/raw/users_time.csv
```

4. Valida:

```powershell
python -m src.cli validate-users-time
```

5. Analizza:

```powershell
python -m src.cli analyze-users-time
```

6. Usa gli output in report e slide:

```txt
outputs/tables/users_time_summary.csv
outputs/tables/users_time_summary.md
outputs/tables/users_time_stat_tests.csv
outputs/figures/users_time_mean_by_task.png
outputs/figures/users_time_boxplot_by_task.png
outputs/figures/users_time_success_rate.png
outputs/figures/users_time_errors_by_task.png
outputs/text/users_time_interpretation.md
outputs/reports/users_time_validation_report.md
```

## Booleani accettati

`success` accetta `true/false`, `si/no`, `sì/no`, `yes/no`, `1/0`.

## Configurazione

La sezione dedicata e in `config.yaml`:

```yaml
users_time:
  enabled: true
  input_path: "data/raw/users_time.csv"
```
