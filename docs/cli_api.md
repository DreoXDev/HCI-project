# Mappa CLI

> [!Info]
> Tutti i comandi partono da `python -m src.cli`.

## Comandi principali

| Comando | Scopo |
|---|---|
| `validate` | Valida i CSV normalizzati |
| `full-pipeline` | Rigenera analisi, asset, testi e slide pack |
| `generate-slides` | Crea il PPTX finale |
| `build-slide-pack` | Prepara testi e asset narrativi per le slide |
| `quality-check` | Controlla dati, output e documentazione |
| `validate-slide-template` | Controlla i `TEMPLATE_ID` del template |
| `validate-slide-assets` | Controlla asset richiesti dal deck |

## `python -m src.cli full-pipeline`

> [!Info]
> Esegue la pipeline completa e, con `--export-pdf`, genera anche PPTX e PDF.

### Uso

```powershell
python -m src.cli full-pipeline --plot-style both --export-pdf
```

### Output

`outputs/figures/`, `outputs/tables/`, `outputs/tables_md/`, `outputs/text_snippets/`, `outputs/slide_pack/`, `outputs/slides/`.

### Opzioni

| Opzione | Effetto |
|---|---|
| `--plot-style both` | Esporta figure scure e presentation |
| `--generate-slides` | Genera il PPTX senza chiedere PDF |
| `--export-pdf` | Genera PPTX e tenta export PDF |
| `--no-export-pdf` | Salta il PDF |

## `python -m src.cli generate-slides`

> [!Info]
> Usa `slides/config/slide_deck.yml` e il template PPTX per generare la presentazione.

```powershell
python -m src.cli generate-slides --auto --overwrite --export-pdf
```

### Errori comuni

| Errore | Causa |
|---|---|
| LibreOffice non trovato | Serve per `--export-pdf` |
| Asset mancante | Lancia prima `full-pipeline` |
| Template non valido | Esegui `validate-slide-template` |

## `python -m src.cli build-slide-pack`

> [!Info]
> Genera il materiale narrativo in `outputs/slide_pack/`. Con `--export-pdf` genera anche PPTX e PDF.

```powershell
python -m src.cli build-slide-pack --export-pdf
```

## Import Formbricks

```powershell
python -m src.cli import-formbricks-questionnaire --input data/formbricks_raw/questionnaire/formbricks_questionnaire_demo_12_users.csv
python -m src.cli import-formbricks-heuristics-discovery --input data/formbricks_raw/heuristics_discovery/formbricks_heuristics_discovery_demo_6_experts.csv
python -m src.cli import-formbricks-heuristics-ratings --input data/formbricks_raw/heuristics_ratings/formbricks_heuristics_ratings_demo_6_experts.csv --output data/templates/heuristics_consolidated_problems_demo.csv
```

## Validazione slide

```powershell
python -m src.cli validate-slide-template
python -m src.cli validate-slide-assets
```

## Note

> [!Warning]
> La CLI usa un parser globale: alcune opzioni sono visibili per più comandi, ma hanno effetto solo dove indicato.

