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

- Dati finali: 8 esperti, 24 utenti, 144 righe osservazionali long.
- Il quality gate deve indicare `READY_FOR_FINAL_SLIDES`.

## Regola anti-confusione

La repo non mantiene dataset demo o template dati nei percorsi `data/`: i path canonici devono puntare solo a input reali o derivati finali.
