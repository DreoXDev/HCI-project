# Generazione slide

Con i CSV gia pronti in `data/raw/`, il comando:

```powershell
python -m src.cli all
```

genera:

```txt
outputs/slide_manifest.md
outputs/slide_pack/
outputs/text_snippets/
outputs/generated_report_sections/
```

Se parti da export Formbricks, completa prima il workflow in `Manuale.md`, inclusa la review manuale delle euristiche.

## Manifest

Apri `outputs/slide_manifest.md` per sapere quali testi, grafici e tabelle usare in ogni sezione.

Per il pacchetto finale pronto da copiare nelle slide usa:

```powershell
python -m src.cli build-slide-pack
```

Il comando genera:

```txt
outputs/slide_pack/00_index.md
outputs/slide_pack/01_intro.md
outputs/slide_pack/02_heuristics.md
outputs/slide_pack/03_user_tests.md
outputs/slide_pack/04_questionnaire.md
outputs/slide_pack/05_conclusions.md
outputs/slide_pack/executive_summary.md
outputs/slide_pack/assets_manifest.csv
```

Ogni file contiene asset consigliati, testo suggerito e note da completare manualmente.

## Asset principali

```txt
outputs/figures/presentation/
outputs/figures/dark/
```

Se un asset manca, significa che manca il dato corrispondente o che quella parte e stata saltata.

## Checklist finale

Prima di assemblare le slide:

```powershell
python -m src.cli quality-check
```

Il report e in `outputs/reports/final_quality_check.md` e termina con `READY_FOR_SLIDES` oppure `NEEDS_FIXES`.
