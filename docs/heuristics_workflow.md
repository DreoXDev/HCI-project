# Workflow euristiche Formbricks

Il nuovo flusso euristico ha due survey separate.

## Survey 1: raccolta problemi

Ogni esperto compila il form con dati profilo e fino a 10 problemi. L'export Formbricks e wide: ogni slot problema ha app, descrizione breve, descrizione lunga ed euristiche violate.

```powershell
python -m src.cli heuristics raw --input data/raw/formbricks/heuristics_experts_raw.csv
```

Il comando produce output grezzi utili per review, grafici demografici degli esperti e report Markdown.

## Review manuale

Il gruppo legge `raw_problems_table.csv`, accorpa problemi simili e compila `consolidated_problems.csv` partendo dal template:

```txt
data/templates/heuristics_consolidated_problems_template.csv
```

Questa fase resta manuale per evitare deduplicazioni opache.

## Survey 2: severita

La seconda survey chiede agli esperti di valutare ogni problema consolidato con scala 0-4.

```powershell
python -m src.cli heuristics severity --ratings data/raw/formbricks/heuristics_severity_ratings.csv --problems data/processed/heuristics/consolidated_problems.csv
```

Il toolkit calcola media, mediana, deviazione standard, IQR e fascia priorita A/B/C.

## Dark pattern

I dark pattern non sono piu un comando automatico. Possono essere trattati come discussione qualitativa manuale nelle slide o nel report.
