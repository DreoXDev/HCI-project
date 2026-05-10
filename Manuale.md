# Manuale operativo

## 1. Metti i file qui

```txt
data/formbricks_raw/questionnaire/export_questionario.csv
data/raw/formbricks/heuristics_experts_raw.csv
data/raw/users_time.csv
```

Se hai gia la survey severita:

```txt
data/raw/formbricks/heuristics_severity_ratings.csv
data/processed/heuristics/consolidated_problems.csv
```

## 2. Avvia l'ambiente

```powershell
cd "D:\Projects\IUM\Improved Notebooks\HCI-project"
..\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 3. Esegui

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/export_questionario.csv
python -m src.cli heuristics raw --input data/raw/formbricks/heuristics_experts_raw.csv
python -m src.cli validate-users-time
python -m src.cli validate
python -m src.cli all --plot-style both
```

## 4. Passaggio manuale euristiche

Apri:

```txt
data/processed/heuristics/raw_problems_table.csv
data/templates/heuristics_consolidated_problems_template.csv
```

Compila e salva:

```txt
data/processed/heuristics/consolidated_problems.csv
```

Poi, se hai il CSV severita:

```powershell
python -m src.cli heuristics severity --ratings data/raw/formbricks/heuristics_severity_ratings.csv --problems data/processed/heuristics/consolidated_problems.csv
```

## 5. Slide opzionali

```powershell
python main.py generate-slides --strict
```
