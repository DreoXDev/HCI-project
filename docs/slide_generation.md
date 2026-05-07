# Generazione slide

Il comando:

```powershell
python -m src.cli full-pipeline
```

genera:

```txt
outputs/slide_manifest.md
outputs/slide_assets/
outputs/text_snippets/
outputs/generated_report_sections/
```

## Manifest

Apri `outputs/slide_manifest.md` per sapere quali testi, grafici e tabelle usare in ogni sezione.

## Asset principali

```txt
outputs/slide_assets/02_heuristics/
outputs/slide_assets/03_user_tests/
outputs/slide_assets/04_questionnaire/
outputs/slide_assets/05_conclusions/
```

Se un asset manca, significa che manca il dato corrispondente o che quella parte e stata saltata.
