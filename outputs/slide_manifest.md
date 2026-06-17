# Slide Manifest

## Uso Grafici
- `outputs/figures/presentation/`: grafici senza sfondo.
- `outputs/figures/clean/`: copia pulita dei grafici scuri per export/report.
- `outputs/figures/dark/`: grafici con sfondo scuro.

## 1. Introduzione
- Testo: `outputs/texts/snippets/intro.md`

## 2. Valutazione euristica
- Testo: `outputs/texts/snippets/heuristics.md`
- Dark: `outputs/figures/dark/heuristics/heuristics_distribution.png`
- Transparent: `outputs/figures/presentation/heuristics/heuristics_distribution.png`
- Severità deduplicata: `outputs/heuristics/heuristics_summary.md`
- Top problemi: `outputs/heuristics/heuristics_top_problems.png`
- Matrice problemi-esperti: `outputs/heuristics/heuristics_problem_expert_heatmap.png`
- Confronto app: `outputs/heuristics/heuristics_by_app.png`
- Sintesi euristiche: `outputs/heuristics/heuristics_by_heuristic.png`
- Tabella problemi critici: `outputs/heuristics/heuristics_critical_problems_table.csv`

## 3. User Test
- Testo: `outputs/texts/snippets/user_tests.md`
- Dark: `outputs/figures/dark/user_tests/effectiveness_deliveroo_vs_glovo.png`
- Transparent: `outputs/figures/presentation/user_tests/effectiveness_deliveroo_vs_glovo.png`

## User Test - Tempi, efficacia ed errori

### Tabelle
- `outputs/tables/markdown/users_time_summary.md`
- `outputs/tables/users_time_stat_tests.csv`

### Grafici
- Dark: `outputs/figures/dark/users_time_mean_by_task.png`
- Transparent: `outputs/figures/presentation/users_time_mean_by_task.png`
- Dark: `outputs/figures/dark/users_time_boxplot_by_task.png`
- Transparent: `outputs/figures/presentation/users_time_boxplot_by_task.png`
- Dark: `outputs/figures/dark/users_time_success_rate.png`
- Transparent: `outputs/figures/presentation/users_time_success_rate.png`
- Dark: `outputs/figures/dark/users_time_errors_by_task.png`
- Transparent: `outputs/figures/presentation/users_time_errors_by_task.png`

### Testi pronti per slide
- `outputs/texts/analysis/users_time_interpretation.md`

## 4. Questionario UEQ e NPS
- Testo: `outputs/texts/snippets/questionnaire.md`
- NPS: `outputs/texts/snippets/nps.md`
- Dark: `outputs/figures/dark/questionnaire/ueq_scales.png`
- Transparent: `outputs/figures/presentation/questionnaire/ueq_scales.png`

## 5. Conclusioni
- Testo: `outputs/texts/snippets/conclusions.md`
- Manifest asset: `outputs/slide_assets/pack/assets_manifest.csv`

## Note
- Se un asset non compare, significa che il dato corrispondente manca o non e stato generato.
- Le euristiche importate da Formbricks richiedono review manuale in `data/processed/heuristics/consolidated_problems.csv` prima della survey severità.