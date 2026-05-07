from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .detection import find_by_alias, is_metadata_column, parse_column_tags
from .normalization import FINISHED_TRUE_VALUES, comparable


@dataclass
class ImportReport:
    kind: str
    input_path: str
    raw_rows: int
    kept_rows: int
    output_paths: list[str] = field(default_factory=list)
    recognized_columns: list[str] = field(default_factory=list)
    ignored_columns: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def excluded_rows(self) -> int:
        return self.raw_rows - self.kept_rows

    def to_markdown(self) -> str:
        return "\n".join(
            [
                f"# Import report - {self.kind}",
                "",
                f"- File importato: `{self.input_path}`",
                f"- Risposte raw: {self.raw_rows}",
                f"- Risposte usate: {self.kept_rows}",
                f"- Risposte escluse: {self.excluded_rows}",
                "",
                "## Output generati",
                *[f"- `{path}`" for path in self.output_paths],
                "",
                "## Colonne riconosciute",
                *[f"- `{column}`" for column in self.recognized_columns],
                "",
                "## Colonne ignorate",
                *[f"- `{column}`" for column in self.ignored_columns[:100]],
                "",
                "## Warning",
                *([f"- {warning}" for warning in self.warnings] or ["- Nessun warning"]),
                "",
            ]
        )


def filter_finished(df: pd.DataFrame, use_only_finished: bool = True) -> pd.DataFrame:
    if not use_only_finished or "Finished" not in df.columns:
        return df.copy()
    values = df["Finished"].astype(str).map(comparable)
    return df[values.isin(FINISHED_TRUE_VALUES)].copy()


def detect_demographic_columns(df: pd.DataFrame, schema: dict, metadata_columns: list[str]) -> dict[str, str]:
    columns = [column for column in df.columns if not is_metadata_column(column, metadata_columns)]
    fields = schema.get("questionnaire", {}).get("demographic_fields", [])
    result: dict[str, str] = {}
    for column in columns:
        parsed = parse_column_tags(column)
        if parsed.has("demographic"):
            matched = next(
                (
                    field
                    for field in fields
                    if find_by_alias([parsed.label], [field.get("id", ""), *field.get("aliases", [])]) is not None
                ),
                None,
            )
            field_id = matched["id"] if matched else comparable(parsed.label).replace(" ", "_") or comparable(column).replace(" ", "_")
            result[field_id] = column
    for field in fields:
        aliases = [field.get("id", ""), *field.get("aliases", [])]
        match = find_by_alias(columns, aliases)
        if match:
            result[field["id"]] = match
    return result


def update_ignored_columns(report: ImportReport, raw_columns: list[str]) -> None:
    recognized = set(report.recognized_columns)
    report.ignored_columns = [column for column in raw_columns if column not in recognized]
