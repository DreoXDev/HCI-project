# Configuration Guide

The current runtime remains compatible with `config.yaml` and `slides/config/slide_deck.yml`. The modular files in `config/` document the project in smaller pieces.

## Main Files

- `config/project.yaml`: title, course, group, systems and output preferences.
- `config/apps.yaml`: app names, brand colors, logo paths, store metadata.
- `config/theme.yaml`: fonts, palette, chart style, table defaults and slide template.
- `config/slides.yaml`: explicit slide manifest with stable ids, generators and data sources.
- `config/appendices.yaml`: appendix sections that can be enabled or disabled.
- `config/analysis.yaml`: significance level, statistical choices and missing value policy.
- `config/ueq.yaml`: UEQ item mapping, official labels, short labels and benchmark thresholds.
- `config/texts/it.yaml`: editable static Italian text.

## Rule Of Thumb

Change data in CSV/config, not in generated charts. Change repeatable slide behavior in config/code, not manually in the final PPTX.
