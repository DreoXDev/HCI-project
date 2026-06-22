# UEQ scoring method

Le risposte raw restano su scala `1..7`.
La scala trasformata UEQ e `-3..+3`: `raw - 4` quando il polo positivo e a destra, `4 - raw` quando il polo positivo e a sinistra.
Item, ancore, dimensioni e verso positivo sono in `config/ueq_items.yml`.
Le dimensioni calcolate sono Attractiveness, Perspicuity, Efficiency, Dependability, Stimulation e Novelty.
Le categorie benchmark sono configurate in `config/ueq_benchmark_thresholds.yml`.
