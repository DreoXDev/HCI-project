# UEQ Benchmark Method

## Fonte

Le categorie benchmark UEQ usate nel report derivano dal tool ufficiale `UEQ_Data_Analysis_Tool_V14.xlsx`, foglio `Benchmark`.

Il benchmark ufficiale indicato dal tool si basa su `21.175` partecipanti e `468` studi/prodotti. La pipeline non importa i dati grezzi dei partecipanti benchmark: usa solo le soglie aggregate ufficiali per classificare le medie del progetto.

Nota: il valore corretto e `21.175`, non `221.175`, salvo diversa versione ufficiale del tool.

## Soglie

Le soglie sono centralizzate in `src/analysis/ueq_benchmark.py`.

| Scala | Bad sotto | Below Average da | Above Average da | Good da | Excellent da |
|---|---:|---:|---:|---:|---:|
| Attrattivita | 0.69 | 0.69 | 1.18 | 1.58 | 1.84 |
| Apprendibilita | 0.72 | 0.72 | 1.20 | 1.73 | 2.00 |
| Efficienza | 0.60 | 0.60 | 1.05 | 1.50 | 1.88 |
| Controllabilita | 0.78 | 0.78 | 1.14 | 1.48 | 1.70 |
| Stimolazione | 0.50 | 0.50 | 1.00 | 1.35 | 1.70 |
| Originalita | 0.16 | 0.16 | 0.70 | 1.12 | 1.60 |

La classificazione usa confini inferiori inclusivi per la categoria successiva:

```text
mean < bad_upper -> Bad
mean < below_average_upper -> Below Average
mean < above_average_upper -> Above Average
mean < good_upper -> Good
otherwise -> Excellent
```

## Risultati finali

| App | Scala | Media | Categoria |
|---|---|---:|---|
| Deliveroo | Attrattivita | -0.06 | Bad |
| Deliveroo | Apprendibilita | 0.20 | Bad |
| Deliveroo | Efficienza | 0.14 | Bad |
| Deliveroo | Controllabilita | 0.62 | Bad |
| Deliveroo | Stimolazione | -0.29 | Bad |
| Deliveroo | Originalita | -0.47 | Bad |
| Glovo | Attrattivita | 0.83 | Below Average |
| Glovo | Apprendibilita | 1.14 | Below Average |
| Glovo | Efficienza | 0.78 | Below Average |
| Glovo | Controllabilita | 1.06 | Below Average |
| Glovo | Stimolazione | 0.33 | Bad |
| Glovo | Originalita | 0.74 | Above Average |

## Output di verifica

La pipeline genera:

- `outputs/tables/ueq/ueq_benchmark_by_scale_app.csv`
- `outputs/validation/ueq_benchmark_plot_data_deliveroo.csv`
- `outputs/validation/ueq_benchmark_plot_data_glovo.csv`
- `reports/audit/ueq_benchmark_code_inventory.md`
- `reports/audit/ueq_benchmark_slide_audit.md`

## Comandi

```bash
python scripts/validate_quantitative_report.py
python scripts/audit_ueq_benchmark_slides.py
python -m pytest tests/test_ueq_scoring.py tests/test_ueq_benchmark.py
python -m src.cli validate
python -m src.cli full-pipeline --plot-style both --generate-slides --export-pdf
```

`python -m src.cli validate` fallisce se le categorie benchmark non coincidono con lo snapshot atteso, se i CSV di plot validation non sono presenti o se l'audit slide non passa.
