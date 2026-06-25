# Template Cleanup Report

## Template Iniziale

- Path: `slides/templates/Deliveroo_vs_Glovo_clean_python_ready_template.pptx`
- Numero slide layout: 25
- `TEMPLATE_ID` trovati: 25
- Audit completo: `docs/template-audit.md`

Layout trovati:

- `cover`
- `section_divider_neutral`, `section_divider_deliveroo`, `section_divider_glovo`
- `graph_full_neutral`, `graph_full_deliveroo`, `graph_full_glovo`
- `comparison_neutral`
- `table_large_neutral`, `table_large_deliveroo`, `table_large_glovo`
- `findings_neutral`, `findings_deliveroo`, `findings_glovo`
- `task_results_neutral`, `task_results_deliveroo`, `task_results_glovo`
- `ueq_question_neutral`, `ueq_question_deliveroo`, `ueq_question_glovo`
- `final_verdict`
- `sources`
- `text_only_neutral`, `text_only_deliveroo`, `text_only_glovo`

## Template Pulito

- Path attivo: `slides/templates/Deliveroo_vs_Glovo_clean_python_ready_template.pptx`
- Path legacy completo: `slides/templates/hci_project_template_legacy_full.pptx`
- Numero slide mantenute nel template attivo: 25
- Numero slide nel template legacy: 25

### TEMPLATE_ID mantenuti come usati dal report finale

- `cover`
- `section_divider_neutral`
- `graph_full_neutral`, `graph_full_deliveroo`, `graph_full_glovo`
- `comparison_neutral`
- `table_large_neutral`, `table_large_deliveroo`, `table_large_glovo`
- `text_only_neutral`, `text_only_deliveroo`, `text_only_glovo`

### TEMPLATE_ID mantenuti come opzionali/compatibilità

- `section_divider_deliveroo`, `section_divider_glovo`
- `findings_neutral`, `findings_deliveroo`, `findings_glovo`
- `task_results_neutral`, `task_results_deliveroo`, `task_results_glovo`
- `ueq_question_neutral`, `ueq_question_deliveroo`, `ueq_question_glovo`
- `final_verdict`
- `sources`

### TEMPLATE_ID rimossi

Nessuno.

Decisione: la pulizia fisica è stata conservativa. I layout non usati dal report finale sono ancora referenziati da percorsi opzionali del generatore (`include_sources`, auto findings, task detail cards, UEQ question details). Rimuoverli ora renderebbe il template più piccolo ma più fragile. La separazione è quindi documentata tramite audit, config e copia legacy; la rimozione fisica potrà essere fatta in un secondo step dopo aver disabilitato o rimosso quei percorsi opzionali dal codice.

## Modifiche Al Codice

- Aggiunto `tools/audit_pptx_template.py`.
- Aggiunto alias CLI `validate-template` mantenendo `validate-slide-template`.
- Aggiunto `config/presentation.yaml` con template attivo, template legacy, slide config e comandi di validazione/audit.
- Aggiunti test di presenza per documentazione/config template.

## Modifiche Alla Documentazione

- Aggiunto `docs/template-guide.md`.
- Aggiunto `docs/template-audit.md` generato dallo script di audit.
- Aggiornato `README.md` con sezione `Customizing The PowerPoint Template`.
- Aggiornato `docs/10_templates_and_branding.md`.
- Aggiornato `docs/cli_api.md` con `validate-template`.

## Comandi Eseguiti

```powershell
python tools/audit_pptx_template.py
python -m src.cli validate-template
```

## Rischi Residui

- Il template attivo contiene ancora layout opzionali non usati dal report finale corrente. È una scelta intenzionale per evitare regressioni nei percorsi opzionali ancora presenti nel codice.
- Se in futuro si vuole un template fisicamente minimale, prima occorre aggiornare `src/slide_export/template_variants.py`, i test e la configurazione delle sezioni opzionali.
- Dopo modifiche manuali al PPTX, eseguire sempre `python -m src.cli validate-template` e rigenerare il report.
