# Snippet testuali

> [!Info]
> Gli snippet non sono output casuali: alimentano slide pack, findings automatici e sezioni report.

## Decisione di audit

| Gruppo | Generato da | Consumatore attuale | Decisione |
|---|---|---|---|
| `intro*`, `methods`, `sample*` | `src/text_generation/final_summary_text.py`, `src/final_assets.py` | `outputs/slide_pack/01_intro.md`, auto deck | Mantenere |
| `heuristics*`, matrici problemi-valutatori | `src/text_generation/final_summary_text.py`, `src/final_assets.py` | `outputs/slide_pack/02_heuristics.md`, findings | Mantenere |
| `user_test*`, `user_tests_t*` | `src/text_generation/final_summary_text.py`, `src/final_assets.py` | `outputs/slide_pack/03_user_tests.md`, slide task | Mantenere |
| `questionnaire*`, `nps*`, `ueq_benchmark*` | `src/text_generation/final_summary_text.py`, `src/benchmark.py` | `outputs/slide_pack/04_questionnaire.md`, findings | Mantenere |
| `conclusions`, `redesign_recommendations`, `limitations` | `src/text_generation/final_summary_text.py` | `outputs/slide_pack/05_conclusions.md`, executive summary | Mantenere |
| `outputs/text/users_time_interpretation.md` | `src/users_time.py` | Documentazione e report notes | Mantenere come nota report |

> [!Important]
> Non eliminare `outputs/text_snippets/`: il generatore slide può trasformare snippet brevi in slide findings e il deck usa il materiale consolidato in `outputs/slide_pack/`.

## Regole

- Gli snippet lunghi vengono fusi nel report/slide pack.
- Gli snippet brevi possono diventare bullet nelle slide.
- Gli snippet duplicati vanno fusi a livello di generatore, non cancellati a mano da `outputs/`.

