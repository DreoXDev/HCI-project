from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import pandas as pd


CATEGORY_ORDER = ["Bad", "Below Average", "Above Average", "Good", "Excellent"]
BENCHMARK_SOURCE = "UEQ_Data_Analysis_Tool_V14.xlsx, sheet Benchmark"

UEQ_SCALE_ALIASES = {
    "Attractiveness": "Attrattività",
    "Attrattivita": "Attrattività",
    "Attrattività": "Attrattività",
    "Perspicuity": "Apprendibilità",
    "Apprendibilita": "Apprendibilità",
    "Apprendibilità": "Apprendibilità",
    "Efficiency": "Efficienza",
    "Efficienza": "Efficienza",
    "Dependability": "Controllabilità",
    "Controllabilita": "Controllabilità",
    "Controllabilità": "Controllabilità",
    "Stimulation": "Stimolazione",
    "Stimolazione": "Stimolazione",
    "Novelty": "Originalità",
    "Originalita": "Originalità",
    "Originalità": "Originalità",
}

UEQ_INTERNAL_SCALE_ALIASES = {
    "Attrattività": "Attractiveness",
    "Apprendibilità": "Perspicuity",
    "Efficienza": "Efficiency",
    "Controllabilità": "Dependability",
    "Stimolazione": "Stimulation",
    "Originalità": "Novelty",
}

UEQ_BENCHMARK_THRESHOLDS = {
    "Attrattività": {"bad_upper": 0.69, "below_average_upper": 1.18, "above_average_upper": 1.58, "good_upper": 1.84},
    "Apprendibilità": {"bad_upper": 0.72, "below_average_upper": 1.20, "above_average_upper": 1.73, "good_upper": 2.00},
    "Efficienza": {"bad_upper": 0.60, "below_average_upper": 1.05, "above_average_upper": 1.50, "good_upper": 1.88},
    "Controllabilità": {"bad_upper": 0.78, "below_average_upper": 1.14, "above_average_upper": 1.48, "good_upper": 1.70},
    "Stimolazione": {"bad_upper": 0.50, "below_average_upper": 1.00, "above_average_upper": 1.35, "good_upper": 1.70},
    "Originalità": {"bad_upper": 0.16, "below_average_upper": 0.70, "above_average_upper": 1.12, "good_upper": 1.60},
}

UEQ_SCALE_ORDER = ["Attrattività", "Apprendibilità", "Efficienza", "Controllabilità", "Stimolazione", "Originalità"]
UEQ_INTERNAL_SCALE_ORDER = [UEQ_INTERNAL_SCALE_ALIASES[name] for name in UEQ_SCALE_ORDER]

PROJECT_BENCHMARK_SNAPSHOT = {
    ("Deliveroo", "Attrattività"): (-0.06, "Bad"),
    ("Deliveroo", "Apprendibilità"): (0.20, "Bad"),
    ("Deliveroo", "Efficienza"): (0.14, "Bad"),
    ("Deliveroo", "Controllabilità"): (0.62, "Bad"),
    ("Deliveroo", "Stimolazione"): (-0.29, "Bad"),
    ("Deliveroo", "Originalità"): (-0.47, "Bad"),
    ("Glovo", "Attrattività"): (0.83, "Below Average"),
    ("Glovo", "Apprendibilità"): (1.14, "Below Average"),
    ("Glovo", "Efficienza"): (0.78, "Below Average"),
    ("Glovo", "Controllabilità"): (1.06, "Below Average"),
    ("Glovo", "Stimolazione"): (0.33, "Bad"),
    ("Glovo", "Originalità"): (0.74, "Above Average"),
}


@dataclass(frozen=True)
class BenchmarkCheck:
    app: str
    scale: str
    mean: float
    expected_mean: float
    category: str
    expected_category: str

    @property
    def ok(self) -> bool:
        return round(self.mean, 2) == round(self.expected_mean, 2) and self.category == self.expected_category


def normalize_ueq_scale_name(name: object) -> str:
    text = str(name).strip()
    if text in UEQ_SCALE_ALIASES:
        return UEQ_SCALE_ALIASES[text]
    raise KeyError(f"Unknown UEQ scale name: {name!r}")


def internal_ueq_scale_name(name: object) -> str:
    official = normalize_ueq_scale_name(name)
    return UEQ_INTERNAL_SCALE_ALIASES[official]


def classify_ueq_benchmark(scale: object, mean: float) -> str:
    if pd.isna(mean):
        return "n.d."
    official = normalize_ueq_scale_name(scale)
    thresholds = UEQ_BENCHMARK_THRESHOLDS[official]
    value = float(mean)
    if value < thresholds["bad_upper"]:
        return "Bad"
    if value < thresholds["below_average_upper"]:
        return "Below Average"
    if value < thresholds["above_average_upper"]:
        return "Above Average"
    if value < thresholds["good_upper"]:
        return "Good"
    return "Excellent"


def benchmark_interpretation(category: str) -> str:
    return {
        "Bad": "Nell'intervallo del 25% dei risultati peggiori.",
        "Below Average": "50% dei risultati e migliore, 25% e peggiore.",
        "Above Average": "25% dei risultati e migliore, 50% e peggiore.",
        "Good": "10% dei risultati e migliore, 75% e peggiore.",
        "Excellent": "Nel range del 10% dei risultati migliori.",
    }.get(str(category), "Categoria benchmark non disponibile.")


def threshold_row(scale: object) -> dict[str, float | str]:
    official = normalize_ueq_scale_name(scale)
    thresholds = UEQ_BENCHMARK_THRESHOLDS[official]
    return {"scale": official, **thresholds, "source": BENCHMARK_SOURCE}


def thresholds_dataframe() -> pd.DataFrame:
    return pd.DataFrame([threshold_row(scale) for scale in UEQ_SCALE_ORDER])


def build_ueq_benchmark_table(means_by_app: Mapping[str, Mapping[str, float]]) -> pd.DataFrame:
    rows = []
    for app, scale_values in means_by_app.items():
        for scale, mean in scale_values.items():
            official = normalize_ueq_scale_name(scale)
            rows.append(
                {
                    "app": app,
                    "scale": official,
                    "mean": float(mean),
                    "benchmark_category": classify_ueq_benchmark(official, float(mean)),
                    "benchmark_interpretation": benchmark_interpretation(classify_ueq_benchmark(official, float(mean))),
                    "benchmark_threshold_source": BENCHMARK_SOURCE,
                }
            )
    out = pd.DataFrame(rows)
    if not out.empty:
        out["_order"] = out["scale"].map(lambda value: UEQ_SCALE_ORDER.index(value) if value in UEQ_SCALE_ORDER else 999)
        out = out.sort_values(["app", "_order"]).drop(columns=["_order"])
    return out


def benchmark_plot_rows(app: str, scale_means: Mapping[str, float]) -> pd.DataFrame:
    rows = []
    for scale in UEQ_SCALE_ORDER:
        mean = float(scale_means[scale])
        thresholds = UEQ_BENCHMARK_THRESHOLDS[scale]
        rows.append(
            {
                "app": app,
                "scale": scale,
                "mean": mean,
                **thresholds,
                "category": classify_ueq_benchmark(scale, mean),
            }
        )
    return pd.DataFrame(rows)


def check_project_benchmark_snapshot(table: pd.DataFrame) -> list[BenchmarkCheck]:
    checks: list[BenchmarkCheck] = []
    if table.empty:
        return checks
    for (app, scale), (expected_mean, expected_category) in PROJECT_BENCHMARK_SNAPSHOT.items():
        official = normalize_ueq_scale_name(scale)
        selected = table[(table["app"] == app) & (table["scale"].map(normalize_ueq_scale_name) == official)]
        if selected.empty:
            checks.append(BenchmarkCheck(app, official, float("nan"), expected_mean, "missing", expected_category))
            continue
        row = selected.iloc[0]
        checks.append(BenchmarkCheck(app, official, float(row["mean"]), expected_mean, str(row["benchmark_category"]), expected_category))
    return checks
