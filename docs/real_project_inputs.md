# Input reali progetto finale

Questa pagina descrive i file reali usati per rigenerare il report Deliveroo vs Glovo.

## Percorsi canonici

| File | Scopo |
|---|---|
| `data/processed/heuristics/clean_problems.csv` | 40 problemi consolidati, `P001`-`P020` Deliveroo e `P021`-`P040` Glovo |
| `data/formbricks_raw/heuristics/severity_ratings_export.csv` | Export Formbricks severita problemi |
| `data/raw/users_time.csv` | Test osservazionali in formato long |
| `data/raw/user_testing_observations.csv` | Note qualitative degli osservatori |
| `data/formbricks_raw/questionnaire/users_questionnaire_export.csv` | Export Formbricks questionario utenti |

## Bootstrap

```powershell
python -m src.cli prepare-real-inputs --source-dir data/inbox --overwrite
```

Il comando cerca i CSV reali, li copia nei path canonici, valida encoding e colonne, importa questionario/severita quando possibile e scrive:

```text
outputs/reports/real_input_status.md
```

## Completezza

- Dati attuali: 8 esperti, 18 utenti, 108 righe osservazionali long.
- Dati finali attesi: 8 esperti, 24 utenti, 144 righe osservazionali long.
- Con 18 utenti il quality gate deve indicare `PARTIAL_READY_FOR_REVIEW`.
- Con 24 utenti il quality gate deve indicare `READY_FOR_FINAL_SLIDES`.

## Regola anti-demo

I file demo possono restare in `data/templates` o `data/examples`, ma non devono essere referenziati da `config.yaml` o dal deck finale quando i dati reali sono disponibili.
