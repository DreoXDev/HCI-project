# Visual Style Guide

## Obiettivo

Mantenere grafici coerenti tra questionari utente, valutazione euristica, user test legacy e dataset osservazionale `users_time`.

La pipeline genera due versioni:

- `dark`: grafici con sfondo scuro
- `presentation`: grafici senza sfondo, DPI alto

## Palette

| Sistema | Colore |
| --- | --- |
| Deliveroo | `#00CCBC` |
| Glovo | `#FFC244` |
| Neutral | `#1F2937` |
| Muted | `#6B7280` |
| Grid | `#E5E7EB` |

## Export

Ogni grafico principale viene esportato in PNG e SVG:

```txt
outputs/figures/dark/
outputs/figures/presentation/
```

## Comandi

```powershell
python -m src.cli full-pipeline --plot-style dark
python -m src.cli full-pipeline --plot-style presentation
python -m src.cli full-pipeline --plot-style both
```

Il default configurato e `both`.

## Regole

- usare sempre la palette brand
- non inserire loghi nei grafici
- evitare effetti pesanti nei grafici statistici
- usare annotazioni solo quando aiutano la lettura
- mantenere griglia leggera e assi leggibili
- esportare PNG per slide e SVG per eventuali modifiche grafiche

## Configurazione

La sezione `visualization` in `config.yaml` controlla stile, SVG/PNG, DPI, font e annotazioni.
