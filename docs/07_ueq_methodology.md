# UEQ Methodology

UEQ measures pragmatic and hedonic qualities of the interaction through 26 bipolar items.

## Transformation

Raw answers are collected on a `1..7` scale and transformed to the official `-3..+3` UEQ scale. Positive and negative item direction is handled by the item mapping in `config/ueq_items.yml`.

## Scale Means

Items are grouped into six dimensions:

- Attrattività;
- Apprendibilità;
- Efficienza;
- Controllabilità;
- Stimolazione;
- Originalità.

The pipeline computes item and scale means, standard deviations and confidence intervals.

## Benchmark

Benchmark categories use the official threshold table in `config/ueq_benchmark_thresholds.yml` through `src.analysis.ueq_benchmark`.

Categories include Bad, Below Average, Above Average, Good and Excellent. Small samples should be interpreted cautiously.

## Sanity Checks

- official UEQ outputs use `-3..+3`;
- no official UEQ slide should present raw means as final results;
- heatmaps may use short labels, but tables should use official full names;
- benchmark wording must appear only when benchmark thresholds are applied.
