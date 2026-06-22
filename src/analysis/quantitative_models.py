from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuantitativePaths:
    task_source: str = "data/raw/users_time.csv"
    questionnaire_deliveroo: str = "data/raw/questionnaire_deliveroo.csv"
    questionnaire_glovo: str = "data/raw/questionnaire_glovo.csv"
    user_profiles: str = "data/user_profiles.csv"
    output_tables: str = "outputs/tables"
    output_charts: str = "outputs/charts"
    output_validation: str = "outputs/validation"

