# UEQ scoring method

Le risposte raw restano su scala `1..7`.
La scala trasformata UEQ e `-3..+3`: `raw - 4` quando il polo positivo e a destra, `4 - raw` quando il polo positivo e a sinistra.
Item, ancore, dimensioni e verso positivo sono in `config/ueq_items.yml`.
Le dimensioni calcolate sono Attractiveness, Perspicuity, Efficiency, Dependability, Stimulation e Novelty.
Le zone positive/neutre/negative usano le soglie semplici `-0.8` e `0.8`; le categorie benchmark ufficiali usano `src/analysis/ueq_benchmark.py`.
