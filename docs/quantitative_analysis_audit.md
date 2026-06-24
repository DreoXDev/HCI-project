# Quantitative Analysis Audit

## Dataset trovati
- `data\user_testing_times.csv`: trovato
- `data\raw\users_time.csv`: trovato
- `data\raw\questionnaire_deliveroo.csv`: trovato
- `data\raw\questionnaire_glovo.csv`: trovato
- `data\user_profiles.csv`: trovato

## Colonne disponibili
- `data\user_testing_times.csv`: user_id, collector, app, task, time_raw, time_seconds, outcome, assistance, error_flag, issue_note
- `data\raw\users_time.csv`: user_id, app, task_id, task_name, completion_time_sec, success, errors_count, help_requests, notes, completion_time_raw, observer
- `data\raw\questionnaire_deliveroo.csv`: item, Utente 1, Utente 2, Utente 3, Utente 4, Utente 5, Utente 6, Utente 7, Utente 8, Utente 9, Utente 10, Utente 11, Utente 12, Utente 13, Utente 14, Utente 15, Utente 16, Utente 17, Utente 18, Utente 19, Utente 20, Utente 21, Utente 22, Utente 23, Utente 24
- `data\raw\questionnaire_glovo.csv`: item, Utente 1, Utente 2, Utente 3, Utente 4, Utente 5, Utente 6, Utente 7, Utente 8, Utente 9, Utente 10, Utente 11, Utente 12, Utente 13, Utente 14, Utente 15, Utente 16, Utente 17, Utente 18, Utente 19, Utente 20, Utente 21, Utente 22, Utente 23, Utente 24
- `data\user_profiles.csv`: user_id, age_group, gender, occupation, delivery_familiarity, food_delivery_frequency

## Analisi implementate
- Efficacia task/app con completamento totale, autonomo, aiuto, errori critici e fallimenti.
- Test McNemar exact per confronti appaiati Deliveroo vs Glovo.
- Efficienza con descrittive, test appaiati e confronto OET.
- UEQ raw 1..7, score trasformato -3..+3, zone semplici e benchmark ufficiale per scala.
- Sottogruppi descrittivi sulle variabili profilo realmente disponibili.

## Colonne mancanti o limiti
- `app_order` non e presente nei CSV disponibili.
- Le categorie benchmark UEQ usano il benchmark ufficiale centralizzato in `src/analysis/ueq_benchmark.py`.
- I sottogruppi con N piccolo sono trattati descrittivamente.

## Output attesi generati
- Tabelle CSV in `outputs\tables`
- Grafici PNG in `outputs\charts`
- Validazione in `outputs\validation`

## Warning
